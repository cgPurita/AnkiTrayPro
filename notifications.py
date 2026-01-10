# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------
from aqt import mw  # Importa a janela principal do Anki
from aqt.qt import * # Importa componentes da interface gráfica Qt
from .lang import tr  # Importa a função de tradução

class GerenciadorNotificacao:
    """
    Gerencia as notificações inteligentes e a sincronização periódica.
    Foca exclusivamente no AUMENTO de cartões de Revisão e Aprendizagem.
    """
    def __init__(self):
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        
        # Armazena a contagem da última verificação.
        self.referencia_anterior = 0
        
        # Inicia a contagem baseada na configuração
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """Lê config e inicia o timer."""
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            ms = config.get("intervalo_notificacao", 30) * 60 * 1000
            self.temporizador.start(ms)
        else:
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Retorna a soma apenas de APRENDIZAGEM (Learn) e REVISÃO (Review).
        Ignora cartões NOVOS.
        """
        try:
            c = mw.col.sched.counts()
            return c[1] + c[2]
        except:
            return 0
    
    def resetar_contagem(self):
        """
        Atualiza a referência imediatamente para o valor atual.
        Isso 'zera' o delta, impedindo notificações de cartões já existentes.
        Deve ser chamado ao minimizar ou maximizar a janela.
        """
        self.referencia_anterior = self.obter_contagem_relevante()

    def verificar_inicializacao(self, iniciado_minimizado):
        """
        Executado ao iniciar. Define o 'marco zero'.
        """
        self.resetar_contagem()
        
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """
        Executado a cada intervalo.
        """
        if not mw.isVisible():
            mw.onSync()
        
        self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """
        Calcula o DELTA (Diferença) entre agora e a última checagem.
        """
        # Se a janela está aberta, atualizamos a referência
        if mw.isVisible():
            self.resetar_contagem()
            return

        try:
            atual = self.obter_contagem_relevante()
            delta = atual - self.referencia_anterior
            
            if delta > 0:
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                 
                self.mostrar_notificacao(msg)
            
            # Atualiza a referência para evitar repetição
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

# Instancia
notificador = GerenciadorNotificacao()