# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------

# Importa módulos para lidar com tempo e banco de dados
import datetime
# Importa a instância principal do Anki e ganchos de interface
from aqt import mw
from aqt.qt import *
# Importa as traduções do add-on
from .lang import tr

class GerenciadorNotificacao:
    """
    Gerencia notificações e sincronização silenciosa no tray.
    Evita pop-ups intrusivos durante o uso em segundo plano.
    """
    def __init__(self):
        # Temporizador principal para as verificações
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        # Referência de contagem para detectar novos vencimentos
        self.referencia_anterior = 0
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """Inicia o timer conforme as configurações do usuário."""
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

            # Atualiza o estado do agendador para refletir o tempo real
            mw.col.reset()

            # Obtém o timestamp atual
            agora_timestamp = int(datetime.datetime.now().timestamp())
            
            # Conta cartões únicos nas filas 1, 2 e 3 (Learn/Review) que venceram
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
        """Ciclo de execução: Sincronia silenciosa seguida de verificação."""
        if not mw.isVisible():
            # SINCRONIZAÇÃO SILENCIOSA:
            # Desativamos temporariamente o gerenciador de progresso para evitar pop-ups
            mw.progress.disable()
            try:
                # Executa a sincronização nativa
                mw.onSync()
            finally:
                # Reativamos imediatamente após a execução para não afetar o uso manual
                mw.progress.enable()
            
            # Aguarda a estabilização dos dados após a rede para verificar pendências
            QTimer.singleShot(3000, self.verificar_novas_pendencias)
        else:
            # Se visível, apenas verifica sem sincronizar (para não interromper o usuário)
            self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """Calcula se novos cartões surgiram e dispara o alerta se necessário."""
        if mw.isVisible():
            self.resetar_contagem()
            return

        try:
            atual = self.obter_contagem_relevante()
            delta = atual - self.referencia_anterior
            
            if delta > 0:
                # Determina mensagem singular ou plural
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                
                self.mostrar_notificacao(msg)
                self.referencia_anterior = atual
            elif delta < 0:
                # Atualiza referência caso o usuário tenha estudado fora
                self.referencia_anterior = atual
            
        except:
            pass

    def mostrar_notificacao(self, mensagem):
        """Dispara som e balão de mensagem na bandeja do sistema."""
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

# Instancia o gerenciador de notificações
notificador = GerenciadorNotificacao()