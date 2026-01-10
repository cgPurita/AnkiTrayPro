# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------

# Importa módulos do sistema para manipulação de arquivos e datas
import os
import datetime
# Importa a janela principal e componentes do Anki/Qt
from aqt import mw
from aqt.qt import *
# Importa a função de tradução para as mensagens de alerta
from .lang import tr

class GerenciadorNotificacao:
    """
    Gerencia as notificações inteligentes e a sincronização periódica.
    Monitora a árvore de baralhos para somar cartões Learn (Vermelhos) e Due (Verdes).
    """
    def __init__(self):
        # Define o caminho do arquivo de log para debug na pasta do addon
        self.caminho_log = os.path.join(os.path.dirname(__file__), "debug_log.txt")
        # Cria o temporizador vinculado à janela principal do Anki
        self.temporizador = QTimer(mw)
        # Conecta o sinal de timeout à função de processamento principal
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        # Inicializa a referência de contagem anterior como zero
        self.referencia_anterior = 0
        # Inicia o timer com base nas configurações de intervalo definidas pelo usuário
        self.iniciar_temporizador()

    def registrar_log(self, mensagem):
        """Escreve mensagens de diagnóstico detalhadas no arquivo debug_log.txt."""
        try:
            # Obtém o carimbo de data e hora atual
            agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Abre o arquivo em modo append para não apagar logs anteriores
            with open(self.caminho_log, "a", encoding="utf-8") as f:
                f.write(f"[{agora}] [NOTIFIER] {mensagem}\n")
        except:
            # Falha silenciosa para evitar travamentos do Anki por erros de permissão de escrita
            pass

    def iniciar_temporizador(self):
        """Configura o intervalo do timer lendo o config.json do add-on."""
        # Acessa as configurações salvas do complemento
        config = mw.addonManager.getConfig(__name__)
        # Verifica se o usuário deseja receber notificações
        if config.get("notificacoes_ativadas"):
            # Converte o intervalo de minutos para milissegundos
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            self.registrar_log(f"Timer configurado e iniciado. Verificação a cada {minutos} min.")
            self.temporizador.start(ms)
        else:
            # Desativa o timer se o usuário desligar as notificações
            self.registrar_log("Notificações desativadas pelo usuário. Timer parado.")
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Varre a árvore de baralhos global (Deck Tree) somando Learn + Due.
        Ignora os cartões Novos (New).
        """
        try:
            # Verifica se o banco de dados do Anki está acessível
            if not mw.col:
                return 0

            # FORÇA O RESET: Essencial para o Anki processar cartões Learn que venceram o tempo
            mw.col.reset()

            # Obtém o nó raiz da árvore de baralhos (DeckTreeNode)
            raiz = mw.col.sched.deck_due_tree()
            
            total_learn = 0
            total_review = 0
            total_new = 0
            
            # Função recursiva interna para navegar por todos os sub-baralhos
            def processar_no(no):
                nonlocal total_learn, total_review, total_new
                
                # Extrai as contagens de cada categoria do nó atual
                total_new += getattr(no, 'new_count', 0)
                total_learn += getattr(no, 'learn_count', 0)
                total_review += getattr(no, 'review_count', 0)
                
                # Se o baralho tiver filhos (sub-baralhos), processa cada um deles
                if hasattr(no, 'children'):
                    for filho in no.children:
                        processar_no(filho)

            # Inicia o processamento a partir do nó raiz retornado pelo scheduler
            processar_no(raiz)

            # O resultado relevante é a soma de Aprendizado (Learn) e Revisão (Due)
            total_relevante = total_learn + total_review
            
            # Registra o resultado detalhado no log para conferência com a imagem da tela inicial
            self.registrar_log(f"SCAN GLOBAL: Novos(Ignorados)={total_new} | Learn={total_learn} | Due={total_review} -> TOTAL RELEVANTE={total_relevante}")
            
            return total_relevante

        except Exception as e:
            # Registra qualquer erro técnico encontrado durante a leitura da árvore
            self.registrar_log(f"ERRO CRÍTICO ao ler árvore: {str(e)}")
            return 0
    
    def resetar_contagem(self):
        """Sincroniza a referência interna com o estado atual dos baralhos."""
        # Obtém a contagem real atual através da árvore
        atual = self.obter_contagem_relevante()
        # Define esta contagem como a nova base de comparação (Anterior)
        self.referencia_anterior = atual
        self.registrar_log(f"RESET: Contagem de referência sincronizada em {self.referencia_anterior}.")

    def verificar_inicializacao(self, iniciado_minimizado):
        """Chamado no momento em que o perfil do Anki é aberto."""
        # Garante que começamos do zero para não notificar pendências antigas do dia anterior
        self.resetar_contagem()
        # Se o boot foi automático e minimizado, envia um resumo inicial
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """Executa a verificação periódica disparada pelo temporizador."""
        self.registrar_log("TIMER: Iniciando ciclo de verificação automática...")
        # Chama a função que calcula se há novos cartões a serem notificados
        self.verificar_novas_pendencias()
        
        # Sincroniza os dados com a nuvem (AnkiWeb) se o app estiver em segundo plano
        if not mw.isVisible():
            self.registrar_log("TIMER: App em background. Executando sincronização periódica (mw.onSync).")
            mw.onSync()

    def verificar_novas_pendencias(self):
        """Calcula a diferença entre cartões atuais e a última vez que o usuário viu o app."""
        # Se o usuário está com o Anki aberto na frente dele, não precisa de notificação
        if mw.isVisible():
            self.registrar_log("STATUS: Janela visível. Atualizando referência e pulando notificação.")
            self.resetar_contagem()
            return

        try:
            # Obtém a contagem real e atualizada (com mw.col.reset ativo)
            atual = self.obter_contagem_relevante()
            # Calcula o Delta (quantos cartões 'surgiram' desde a última vez)
            delta = atual - self.referencia_anterior
            
            self.registrar_log(f"CHECK: Atual={atual} | Anterior={self.referencia_anterior} | Delta={delta}")
            
            # Notifica apenas se o número de pendências globais aumentou
            if delta > 0:
                # Formata a mensagem baseada na quantidade (singular ou plural)
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                
                self.registrar_log(f"DISPARO: Mudança detectada. Enviando alerta: '{msg}'")
                self.mostrar_notificacao(msg)
                # Atualiza a referência para que o próximo alerta só ocorra se o número subir novamente
                self.referencia_anterior = atual
            
        except Exception as e:
            self.registrar_log(f"ERRO no processamento de pendências: {str(e)}")

    def mostrar_notificacao(self, mensagem):
        """Faz a ponte entre a lógica do notificador e a interface gráfica da bandeja."""
        # Emite o bipe sonoro do Windows
        QApplication.beep()
        # Importação local do tray para evitar dependência circular
        from .tray import gerenciador_bandeja
        # Se o ícone estiver ativo no sistema, mostra o balão de texto
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000 # O balão some após 5 segundos
            )

# Cria a instância global do notificador
notificador = GerenciadorNotificacao()