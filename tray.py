# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: tray.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from .consts import *

class GerenciadorBandeja:
    """
    Gerencia a interação com a bandeja do sistema (System Tray) e intercepta
    eventos de janela para alterar o comportamento de fechar/minimizar.
    """
    def __init__(self):
        self.icone_bandeja = None
        
        # Configura o ícone visual e seus menus
        self.configurar_icone_bandeja()
        
        # Instala os ganchos nos eventos da janela principal
        self.configurar_ganchos()

    def obter_config(self, chave):
        """Recupera um valor específico da configuração."""
        return mw.addonManager.getConfig(__name__).get(chave)

    def configurar_icone_bandeja(self):
        """Cria o objeto QSystemTrayIcon e define suas ações."""
        
        # Cria o ícone associado à janela principal
        self.icone_bandeja = QSystemTrayIcon(mw)
        self.icone_bandeja.setIcon(QIcon(":/icons/anki.png"))
        self.icone_bandeja.setToolTip(DICA_BANDEJA)
        
        # Cria o menu de contexto (clique direito)
        menu = QMenu()
        
        # Opção para restaurar a janela
        acao_mostrar = QAction("Abrir Anki", menu)
        acao_mostrar.triggered.connect(self.mostrar_janela)
        menu.addAction(acao_mostrar)
        
        # Opção para forçar sincronização
        acao_sinc = QAction("Sincronizar", menu)
        acao_sinc.triggered.connect(lambda: mw.onSync())
        menu.addAction(acao_sinc)

        menu.addSeparator()

        # Opção para encerrar o aplicativo
        acao_sair = QAction("Sair Totalmente", menu)
        acao_sair.triggered.connect(self.forcar_saida)
        menu.addAction(acao_sair)

        # Associa o menu ao ícone
        self.icone_bandeja.setContextMenu(menu)
        
        # Monitora cliques no ícone (esquerdo/duplo clique)
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)

    def ao_clicar_icone(self, razao):
        """Trata o evento de clique no ícone da bandeja."""
        # Se for um clique de ativação (gatilho), restaura a janela
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            self.mostrar_janela()

    def mostrar_janela(self):
        """Traz o Anki de volta para a tela e foca na janela."""
        mw.show()
        
        # Restaura o estado da janela removendo a flag de minimizado
        estado_atual = mw.windowState()
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        
        mw.activateWindow()
        mw.raise_()
        
        # Esconde o ícone da bandeja enquanto a janela estiver visível
        self.icone_bandeja.hide()

    def esconder_para_bandeja(self):
        """Minimiza o Anki, mostra o ícone na bandeja e sincroniza se necessário."""
        
        # Executa sincronização se configurado
        if self.obter_config("sincronizar_na_bandeja"):
            mw.onSync()

        # Torna o ícone da bandeja visível
        self.icone_bandeja.show()
        
        # Oculta a janela principal
        mw.hide()
        
        # Exibe notificação visual de confirmação
        self.icone_bandeja.showMessage(
            NOME_APP, 
            "Minimizado para a bandeja.", 
            QSystemTrayIcon.MessageIcon.Information, 
            1000
        )

    def forcar_saida(self):
        """Encerra a aplicação completamente."""
        mw.app.quit()

    # --- Tratamento de Eventos (Hooks) ---

    def configurar_ganchos(self):
        """Substitui os métodos de evento padrão do Anki pelos nossos."""
        self.evento_fechar_original = mw.closeEvent
        mw.closeEvent = self.ao_evento_fechar
        
        self.evento_mudanca_original = mw.changeEvent
        mw.changeEvent = self.ao_evento_mudanca

    def ao_evento_fechar(self, evento):
        """Intercepta o clique no botão 'X'."""
        acao = self.obter_config("acao_ao_fechar")
        
        if acao == ACAO_BANDEJA:
            # Impede o fechamento padrão e envia para a bandeja
            evento.ignore()
            self.esconder_para_bandeja()
        else:
            # Permite o fechamento padrão
            self.evento_fechar_original(evento)

    def ao_evento_mudanca(self, evento):
        """Intercepta mudanças de estado (ex: minimizar)."""
        if evento.type() == QEvent.Type.WindowStateChange:
            # Verifica se a janela entrou em estado minimizado
            if mw.windowState() & Qt.WindowState.WindowMinimized:
                acao = self.obter_config("acao_ao_minimizar")
                if acao == ACAO_BANDEJA:
                    # Agenda a ocultação para o próximo ciclo de eventos
                    QTimer.singleShot(0, self.esconder_para_bandeja)
        
        # Mantém o comportamento original para outros eventos
        self.evento_mudanca_original(evento)

# Instância global
gerenciador_bandeja = GerenciadorBandeja()