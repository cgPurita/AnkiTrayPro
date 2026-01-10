# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------
from aqt import mw  # Janela principal do Anki
from aqt.qt import * # Componentes gráficos do Qt (Timer, Som, etc)
from .lang import tr # Nossa função de tradução

class GerenciadorNotificacao:
    """
    Classe responsável por verificar periodicamente se há cartões para estudar
    e emitir um alerta visual/sonoro.
    """
    def __init__(self):
        # Cria um temporizador (Timer) vinculado à janela principal
        self.temporizador = QTimer(mw)
        
        # Conecta o evento de "tempo esgotado" do timer à função de verificação
        self.temporizador.timeout.connect(self.verificar_cartoes_vencidos)
        
        # Inicia a contagem assim que a classe é criada
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """Lê a configuração e inicia (ou para) o timer."""
        # Obtém o arquivo de configuração do add-on
        configuracao = mw.addonManager.getConfig(__name__)
        
        if configuracao.get("notificacoes_ativadas"):
            # Pega o intervalo em minutos (padrão 30) e converte para milissegundos
            # (minutos * 60 segundos * 1000 milissegundos)
            intervalo_ms = configuracao.get("intervalo_notificacao", 30) * 60 * 1000
            
            # Inicia o timer com esse intervalo
            self.temporizador.start(intervalo_ms)
        else:
            # Se notificações estiverem desligadas, para o timer para economizar recurso
            self.temporizador.stop()

    def verificar_cartoes_vencidos(self):
        """Lógica executada a cada 'X' minutos."""
        
        # Só envia notificação se a janela NÃO estiver visível (ou seja, se estiver na bandeja).
        # Não faz sentido notificar se o usuário já está com o Anki aberto na cara dele.
        if mw.isVisible():
            return

        # Pergunta ao agendador (scheduler) do Anki quantos cartões existem
        # O método retorna uma tupla: (novos, aprendizado, revisao)
        contagens = mw.col.sched.counts()
        
        # Somamos cartões em aprendizado (índice 1) + revisão (índice 2)
        # Ignoramos 'novos' (índice 0) para não incomodar demais, mas você pode somar se quiser.
        total_pendente = contagens[1] + contagens[2]

        if total_pendente > 0:
            self.mostrar_notificacao(total_pendente)

    def mostrar_notificacao(self, quantidade):
        """Exibe o balão na bandeja e toca um som."""
        
        # Toca um som padrão de "bip" do sistema operacional
        QApplication.beep()
        
        # Precisamos acessar o ícone da bandeja que está sendo gerenciado em outro arquivo.
        # Importamos aqui dentro para evitar "importação circular" (erro de loop de import).
        from .tray import gerenciador_bandeja
        
        if gerenciador_bandeja.icone_bandeja:
            # Busca o texto traduzido e formata com o número
            mensagem = tr("msg_vencidos").format(quantidade)
            
            # Exibe a mensagem flutuante (Título, Mensagem, Ícone Info, Duração ms)
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki", 
                mensagem, 
                QSystemTrayIcon.Information, 
                5000 # Fica visível por 5 segundos
            )

# Cria uma instância global para ser usada em outros lugares
notificador = GerenciadorNotificacao()