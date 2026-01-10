# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------

# Importa o módulo 'os' para lidar com caminhos de arquivos (necessário para o log)
import os
# Importa 'datetime' para carimbar o horário nos logs
import datetime
# Importa a janela principal do Anki (MainWindow)
from aqt import mw
# Importa componentes da interface gráfica Qt, incluindo o Timer
from aqt.qt import *
# Importa a função de tradução
from .lang import tr

class GerenciadorNotificacao:
    """
    Gerencia as notificações inteligentes e a sincronização periódica.
    Monitora o agendador do Anki para avisar quando novos cartões vencem.
    """
    def __init__(self):
        """
        Construtor da classe. Inicializa o timer e a referência de contagem.
        """
        # Define o caminho do arquivo de log para debug (o mesmo usado anteriormente)
        self.caminho_log = os.path.join(os.path.dirname(__file__), "debug_log.txt")
        
        # Cria o temporizador que vai disparar periodicamente
        self.temporizador = QTimer(mw)
        # Conecta o 'bater' do relógio à função 'ao_bater_relogio'
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        
        # Armazena a contagem da última verificação para saber se aumentou depois
        self.referencia_anterior = 0
        
        # Inicia a contagem baseada na configuração salva
        self.iniciar_temporizador()

    def registrar_log(self, mensagem):
        """
        Função auxiliar para escrever no arquivo de debug_log.txt.
        Ajuda a entender o que está acontecendo internamente.
        """
        try:
            # Pega a hora atual
            agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Abre o arquivo em modo de 'append' (adicionar ao final)
            with open(self.caminho_log, "a", encoding="utf-8") as f:
                # Escreve a linha identificando que veio do [NOTIFIER]
                f.write(f"[{agora}] [NOTIFIER] {mensagem}\n")
        except:
            # Se der erro no log, ignora para não travar o Anki
            pass

    def iniciar_temporizador(self):
        """
        Lê as configurações do Add-on e inicia (ou para) o timer.
        """
        # Obtém a configuração atual do addon
        config = mw.addonManager.getConfig(__name__)
        
        # Verifica se as notificações estão ativadas no JSON de config
        if config.get("notificacoes_ativadas"):
            # Converte minutos para milissegundos (min * 60s * 1000ms)
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            
            # [DEBUG] Registra que o timer está iniciando e qual o intervalo
            self.registrar_log(f"Iniciando Timer. Intervalo configurado: {minutos} minutos ({ms} ms).")
            
            # Inicia o timer com o intervalo calculado
            self.temporizador.start(ms)
        else:
            # [DEBUG] Registra que as notificações estão desligadas
            self.registrar_log("Notificações desativadas nas configurações. Parando Timer.")
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Retorna a soma apenas de cartões em APRENDIZAGEM (Learn) e REVISÃO (Review).
        Tenta acessar o banco de dados do Anki com segurança.
        """
        try:
            # Verifica se a coleção (banco de dados) está carregada
            if not mw.col:
                # [DEBUG] Coleção não carregada ainda
                self.registrar_log("ERRO: Coleção (mw.col) não encontrada ou fechada.")
                return 0

            # mw.col.sched.counts() retorna uma tupla: (Novos, Aprendizado, Revisão)
            c = mw.col.sched.counts()
            
            # Somamos apenas índice 1 (Learn) e 2 (Review). Ignoramos Novos (índice 0).
            total = c[1] + c[2]
            
            # [DEBUG] Registra a contagem bruta vinda do Anki para conferência
            # self.registrar_log(f"Contagem bruta Anki (New, Lrn, Rev): {c} -> Total Relevante: {total}")
            return total
        except Exception as e:
            # Se o banco estiver travado, retorna 0 e loga o erro
            self.registrar_log(f"ERRO ao obter contagem: {str(e)}")
            return 0
    
    def resetar_contagem(self):
        """
        Atualiza a referência imediatamente para o valor atual.
        Chamado ao minimizar/maximizar para 'zerar' pendências visuais,
        evitando notificar cartões que o usuário já viu.
        """
        # Obtém quantos cartões existem AGORA
        atual = self.obter_contagem_relevante()
        # Atualiza a referência
        self.referencia_anterior = atual
        
        # [DEBUG] Registra que a contagem foi resetada (sincronizada com o real)
        self.registrar_log(f"RESET: Referência atualizada para {self.referencia_anterior}. O sistema considera que você já viu esses cartões.")

    def verificar_inicializacao(self, iniciado_minimizado):
        """
        Executado ao iniciar o Anki.
        """
        # [DEBUG] Log de inicialização
        self.registrar_log(f"Verificando inicialização. Iniciado minimizado? {iniciado_minimizado}")
        
        # Zera a contagem para não notificar coisas antigas imediatamente
        self.resetar_contagem()
        
        # Se iniciou minimizado e já tem cartões, manda a notificação de "Bom dia"
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """
        Executado a cada intervalo de tempo definido pelo timer.
        A ORDEM AQUI É CRUCIAL: Primeiro verifica, depois sincroniza.
        """
        # [DEBUG] O timer disparou (tick)
        self.registrar_log("TIMER: O relógio bateu. Iniciando verificação...")

        # --- PASSO 1: VERIFICAÇÃO (Leitura Rápida) ---
        # Verificamos se surgiram novos cartões ANTES de qualquer operação pesada
        self.verificar_novas_pendencias()
        
        # --- PASSO 2: SINCRONIZAÇÃO (Operação Pesada) ---
        # Só sincroniza se estiver minimizado (invisível) para não travar o usuário
        if not mw.isVisible():
            # A sincronização pode bloquear o banco por alguns segundos
            # [DEBUG] Log antes da sync
            self.registrar_log("TIMER: Janela oculta. Iniciando sincronização periódica.")
            mw.onSync()
        else:
            # [DEBUG] Log informando que pulou a sync pois o usuário está usando
            self.registrar_log("TIMER: Janela visível. Pulando sincronização.")

    def verificar_novas_pendencias(self):
        """
        Calcula se há novos cartões desde a última vez.
        """
        # Se a janela está aberta, o usuário está vendo, então apenas atualizamos a referência
        if mw.isVisible():
            # [DEBUG] Janela aberta, apenas atualiza referência sem notificar
            self.registrar_log("STATUS: Janela aberta. Apenas atualizando referência silenciosamente.")
            self.resetar_contagem()
            return

        try:
            # Obtém o número atual de cartões a fazer
            atual = self.obter_contagem_relevante()
            
            # Calcula a diferença (Delta) entre o que existe agora e o que existia antes
            delta = atual - self.referencia_anterior
            
            # [DEBUG] Log crucial da matemática da notificação
            self.registrar_log(f"CHECK: Atual={atual} | Anterior={self.referencia_anterior} | Delta={delta}")
            
            # Se o número aumentou (cartões "nasceram" ou "venceram")
            if delta > 0:
                # Escolhe a mensagem (singular ou plural)
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                
                # [DEBUG] Log confirmando que vai pedir para mostrar a notificação
                self.registrar_log(f"DISPARO: Delta positivo ({delta}). Enviando notificação: '{msg}'")
                
                # Mostra a notificação visual
                self.mostrar_notificacao(msg)
                
                # Atualiza a referência para o novo valor atual.
                # Assim, no próximo tick, só notifica se aparecerem MAIS cartões além destes.
                self.referencia_anterior = atual
            else:
                # [DEBUG] Log quando não há nada novo
                self.registrar_log("CHECK: Nenhum cartão novo detectado (Delta <= 0).")
            
        except Exception as e:
            # [DEBUG] Log de erro na verificação
            self.registrar_log(f"ERRO FATAL na verificação: {str(e)}")
            pass

    def mostrar_notificacao(self, mensagem):
        """Emite som e mostra o balão na bandeja."""
        # Toca o som padrão do sistema
        QApplication.beep()
        
        # Importa o gerenciador de bandeja aqui para evitar importação circular no topo
        from .tray import gerenciador_bandeja
        
        # Verifica se o ícone da bandeja existe e está ativo
        if gerenciador_bandeja.icone_bandeja:
            # [DEBUG] Log final da exibição
            self.registrar_log("INTERFACE: Exibindo balão no sistema.")
            
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000 # Tempo de duração em ms
            )
        else:
            # [DEBUG] Log de aviso se o ícone não existir
            self.registrar_log("AVISO: Tentativa de notificar falhou pois icone_bandeja é None.")

# Instancia o gerenciador (ao carregar o arquivo, ele já configura o timer)
notificador = GerenciadorNotificacao()