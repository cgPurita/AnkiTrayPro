# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------
from aqt import mw  # Importa a janela principal do Anki (MainWindow)
from aqt.qt import * # Importa componentes da interface gráfica Qt
from .lang import tr  # Importa a função de tradução

class GerenciadorNotificacao:
    """
    Gerencia as notificações inteligentes e a sincronização periódica.
    Monitora o agendador do Anki e prioriza a verificação antes da sincronia.
    """
    def __init__(self):
        """
        Construtor da classe.
        """
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        
        # Armazena a contagem da última verificação para cálculo de delta.
        self.referencia_anterior = 0
        
        # Inicia a contagem baseada na configuração
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """
        Lê as configurações do Add-on e inicia o timer.
        """
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            ms = config.get("intervalo_notificacao", 30) * 60 * 1000
            self.temporizador.start(ms)
        else:
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Retorna a soma apenas de APRENDIZAGEM (Learn) e REVISÃO (Review).
        Tenta acessar o banco de dados com segurança.
        """
        try:
            # Verifica se a coleção (banco de dados) está carregada e acessível
            if not mw.col:
                return 0

            # mw.col.sched.counts() retorna (Novos, Aprendizado, Revisão)
            c = mw.col.sched.counts()
            
            # Somamos apenas índice 1 e 2 (Ignoramos Novos)
            return c[1] + c[2]
        except:
            # Se o banco estiver travado ou inacessível, retorna 0 para evitar crash
            return 0
    
    def resetar_contagem(self):
        """
        Atualiza a referência imediatamente para o valor atual.
        Chamado ao minimizar/maximizar para 'zerar' pendências visuais.
        """
        self.referencia_anterior = self.obter_contagem_relevante()

    def verificar_inicializacao(self, iniciado_minimizado):
        """
        Executado ao iniciar o Anki.
        """
        # Zera a contagem para não notificar coisas antigas
        self.resetar_contagem()
        
        # Se quiser notificar ao ligar o PC ("Bom dia"), mantém isso.
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """
        Executado a cada intervalo de tempo.
        A ORDEM AQUI É CRUCIAL: Primeiro verifica, depois sincroniza.
        """
        # --- PASSO 1: VERIFICAÇÃO (Leitura Rápida) ---
        # Verificamos se surgiram novos cartões ANTES de qualquer operação pesada
        self.verificar_novas_pendencias()
        
        # --- PASSO 2: SINCRONIZAÇÃO (Operação Pesada) ---
        # Só sincroniza se estiver minimizado (invisível)
        if not mw.isVisible():
            # A sincronização pode bloquear o banco por alguns segundos
            mw.onSync()

    def verificar_novas_pendencias(self):
        """
        Calcula se há novos cartões desde a última vez.
        """
        # Se a janela está aberta, o usuário está vendo, então apenas atualizamos a referência
        if mw.isVisible():
            self.resetar_contagem()
            return

        try:
            # Obtém o número atual de cartões a fazer
            atual = self.obter_contagem_relevante()
            
            # Calcula a diferença (Delta)
            delta = atual - self.referencia_anterior
            
            # Se o número aumentou (cartões "nasceram" ou "venceram")
            if delta > 0:
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                 
                self.mostrar_notificacao(msg)
            
            # Atualiza a referência. 
            # Se acabamos de notificar sobre 1 cartão, 'referencia_anterior' sobe.
            # Na próxima vez, só notificaremos se tivermos MAIS do que isso.
            self.referencia_anterior = atual
            
        except:
            pass

    def mostrar_notificacao(self, mensagem):
        """Emite som e mostra o balão."""
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

# Instancia o gerenciador
notificador = GerenciadorNotificacao()