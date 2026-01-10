# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------

import datetime
from aqt import mw
from aqt.qt import *
from .lang import tr

class GerenciadorNotificacao:
    """
    Gerencia notificações e sincronização silenciosa.
    Agora força a atualização da interface para evitar números defasados.
    """
    def __init__(self):
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        self.referencia_anterior = 0
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """Inicia o timer conforme as configurações."""
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            self.temporizador.start(ms)
        else:
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """Consulta o banco de dados por IDs únicos de cartões Learn e Due."""
        try:
            if not mw.col:
                return 0

            # Atualiza o agendador interno
            mw.col.reset()

            agora_timestamp = int(datetime.datetime.now().timestamp())
            query = "SELECT count(id) FROM cards WHERE queue IN (1, 2, 3) AND due <= ?"
            total = mw.col.db.scalar(query, agora_timestamp) or 0
            
            return total
        except:
            return 0
    
    def resetar_contagem(self):
        """Sincroniza a referência interna com o banco de dados."""
        self.referencia_anterior = self.obter_contagem_relevante()

    def verificar_inicializacao(self, iniciado_minimizado):
        """Executado ao carregar o perfil do Anki."""
        self.resetar_contagem()
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """Ciclo de execução: Sincronia silenciosa e atualização de UI."""
        if not mw.isVisible():
            try:
                if mw.col:
                    # Sincroniza o banco de dados
                    mw.col.sync()
                    # FORÇA A ATUALIZAÇÃO DA INTERFACE: 
                    # Isso garante que, ao abrir o Anki, a tela inicial (DeckBrowser) seja recarregada
                    mw.moveToState("deckBrowser")
            except:
                pass
            
            QTimer.singleShot(2000, self.verificar_novas_pendencias)
        else:
            self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """Calcula se há novos cartões e dispara o alerta."""
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
                self.referencia_anterior = atual
            elif delta < 0:
                self.referencia_anterior = atual
            
        except:
            pass

    def mostrar_notificacao(self, mensagem):
        """Dispara som e balão de mensagem na bandeja."""
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

notificador = GerenciadorNotificacao()