# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from .lang import tr

class GerenciadorNotificacao:
    """
    Controla um temporizador para verificar periodicamente cartões vencidos
    e emitir alertas quando o Anki estiver minimizado.
    """
    def __init__(self):
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.verificar_cartoes_vencidos)
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """Lê as configurações e inicia ou para o ciclo de verificação."""
        configuracao = mw.addonManager.getConfig(__name__)
        
        if configuracao.get("notificacoes_ativadas"):
            # Converte o intervalo de minutos para milissegundos
            intervalo_ms = configuracao.get("intervalo_notificacao", 30) * 60 * 1000
            self.temporizador.start(intervalo_ms)
        else:
            self.temporizador.stop()

    def verificar_cartoes_vencidos(self):
        """Consulta a coleção do Anki para contar revisões pendentes."""
        
        # Não notifica se a janela estiver visível para o usuário
        if mw.isVisible():
            return

        try:
            # Obtém a contagem: (novos, aprendizado, revisão)
            contagens = mw.col.sched.counts()
            # Considera apenas aprendizado e revisão para o alerta
            total_pendente = contagens[1] + contagens[2]
        except:
            # Tratamento de erro caso a API do agendador não esteja disponível
            total_pendente = 0

        if total_pendente > 0:
            self.mostrar_notificacao(total_pendente)

    def mostrar_notificacao(self, quantidade):
        """Emite sinal sonoro e exibe balão na bandeja."""
        
        # Emite som padrão do sistema
        QApplication.beep()
        
        # Importa o gerenciador de bandeja localmente para acessar o ícone
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            mensagem = tr("msg_vencidos").format(quantidade)
            
            # Exibe a mensagem flutuante com ícone de informação
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

# Instância global
notificador = GerenciadorNotificacao()