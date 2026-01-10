# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------
import datetime
from aqt import mw
from aqt.qt import *
from .lang import tr

class GerenciadorNotificacao:
    def __init__(self):
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        self.referencia_anterior = 0
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            self.temporizador.start(ms)
        else:
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        try:
            if not mw.col: return 0
            
            # Resetamos o scheduler para processar vencimentos de tempo
            mw.col.reset()
            
            agora_timestamp = int(datetime.datetime.now().timestamp())
            # SQL para contar Learn/Due ignorando duplicatas da interface
            query = "SELECT count(id) FROM cards WHERE queue IN (1, 2, 3) AND due <= ?"
            return mw.col.db.scalar(query, agora_timestamp) or 0
        except:
            return 0
    
    def resetar_contagem(self):
        self.referencia_anterior = self.obter_contagem_relevante()

    def verificar_inicializacao(self, iniciado_minimizado):
        self.resetar_contagem()
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        # Só executa se o Anki estiver escondido
        if not mw.isVisible():
            try:
                if mw.col:
                    # Sincronização direta no DB para evitar pop-ups de interface
                    mw.col.sync()
            except:
                pass
            
            # Aguarda um pouco para o banco estabilizar e checa notificações
            QTimer.singleShot(2000, self.verificar_novas_pendencias)
        else:
            self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        if mw.isVisible():
            self.resetar_contagem()
            return

        try:
            atual = self.obter_contagem_relevante()
            delta = atual - self.referencia_anterior
            
            if delta > 0:
                msg = tr("msg_novos_um") if delta == 1 else tr("msg_novos_varios").format(delta)
                self.mostrar_notificacao(msg)
                self.referencia_anterior = atual
            elif delta < 0:
                self.referencia_anterior = atual
        except:
            pass

    def mostrar_notificacao(self, mensagem):
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", mensagem, QSystemTrayIcon.MessageIcon.Information, 5000
            )

notificador = GerenciadorNotificacao()