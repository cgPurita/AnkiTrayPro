# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: tray.py
# -------------------------------------------------------------------------

# Importa a janela principal do Anki através do objeto global 'mw' 
from aqt import mw
# Importa as classes necessárias da biblioteca Qt para interface gráfica 
from aqt.qt import *
# Importa as constantes globais do projeto (como ACAO_BANDEJA) 
from .consts import *
# Importa a função de tradução para suporte a múltiplos idiomas 
from .lang import tr

class GerenciadorBandeja:
    """
    Gerencia a interação com a bandeja do sistema (System Tray).
    Controla a visibilidade da janela e o ícone de segundo plano. 
    """
    def __init__(self):
        # Inicializa a referência do ícone como nula 
        self.icone_bandeja = None
        # Flag para permitir o fechamento real do aplicativo 
        self.fechamento_real = False
        # Configura os ganchos (hooks) de fechamento da janela principal 
        self.configurar_ganchos()
        # Cria e configura o ícone na área de notificação do Windows [cite: 76]
        self.configurar_icone_bandeja()

    def obter_config(self, chave):
        # Busca uma configuração específica no gerenciador de complementos do Anki [cite: 76]
        return mw.addonManager.getConfig(__name__).get(chave)

    def configurar_icone_bandeja(self):
        """
        Cria o ícone na bandeja, define o menu de contexto e o tooltip traduzido.
        """
        # Evita a criação duplicada do ícone [cite: 76]
        if self.icone_bandeja: return
        
        # Cria o objeto do ícone vinculado à janela principal [cite: 76]
        self.icone_bandeja = QSystemTrayIcon(mw)
        # Define o ícone visual usando o ícone oficial do Anki [cite: 76]
        self.icone_bandeja.setIcon(mw.windowIcon())
        
        # DEFINE O TOOLTIP USANDO A TRADUÇÃO VARIÁVEL [Personalização solicitada]
        # O texto agora depende do idioma configurado no perfil do usuário [cite: 104]
        self.icone_bandeja.setToolTip(tr("tooltip_tray"))
        
        # Cria o menu que aparece ao clicar com o botão direito no ícone [cite: 76]
        menu = QMenu()
        
        # Ação para restaurar a janela principal [cite: 76]
        acao_mostrar = QAction(tr("menu_abrir"), menu)
        acao_mostrar.triggered.connect(self.mostrar_janela)
        menu.addAction(acao_mostrar)
        
        # Ação para forçar uma sincronização manual [cite: 77]
        acao_sinc = QAction(tr("menu_sincronizar"), menu)
        acao_sinc.triggered.connect(lambda: mw.onSync())
        menu.addAction(acao_sinc)

        # Divisor visual no menu [cite: 77]
        menu.addSeparator()

        # Ação para encerrar o Anki definitivamente [cite: 77]
        acao_sair = QAction(tr("menu_sair_total"), menu)
        acao_sair.triggered.connect(self.forcar_saida)
        menu.addAction(acao_sair)

        # Atribui o menu ao ícone e conecta o clique do botão esquerdo [cite: 77, 78]
        self.icone_bandeja.setContextMenu(menu)
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)
        
        # Permite abrir a janela ao clicar em um balão de notificação [cite: 78]
        self.icone_bandeja.messageClicked.connect(self.mostrar_janela)

    def ao_clicar_icone(self, razao):
        # Se o ícone for clicado normalmente, restaura a janela [cite: 78]
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            self.mostrar_janela()

    def mostrar_janela(self):
        """
        Restaura a janela do Anki para o primeiro plano. [cite: 79]
        """
        # Garante que a janela seja exibida e ganhe foco [cite: 79]
        mw.show()
        estado_atual = mw.windowState()
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        mw.activateWindow()
        mw.raise_()
        
        # Esconde o ícone da bandeja enquanto a janela está aberta [cite: 79]
        if self.icone_bandeja: self.icone_bandeja.hide()

        # Reseta a contagem de referência do notificador [cite: 80]
        from .notifications import notificador
        notificador.resetar_contagem()

    def esconder_para_bandeja(self):
        """
        Oculta a janela e garante que o usuário saia do modo de revisão. [cite: 81]
        """
        # LÓGICA DE SEGURANÇA: Se estiver respondendo um cartão, volta para a tela inicial
        if mw.state == "review":
            # Força o retorno para o navegador de baralhos antes de ocultar
            mw.deckBrowser.show()
            
        # Sincroniza se a opção estiver ativada nas configurações [cite: 81]
        if self.obter_config("sincronizar_na_bandeja"):
            mw.onSync()
            
        # Exibe o ícone na bandeja e oculta a janela principal [cite: 81]
        if self.icone_bandeja: self.icone_bandeja.show()
        mw.hide()

        # Atualiza o notificador para considerar o estado atual como "visto" [cite: 82]
        from .notifications import notificador
        notificador.resetar_contagem()

    def forcar_saida(self):
        """
        Sincroniza e encerra o aplicativo completamente. [cite: 82]
        """
        mw.onSync()
        self.fechamento_real = True
        mw.close()

    def configurar_ganchos(self):
        """
        Intercepta o evento de fechamento da janela principal. [cite: 82]
        """
        self.evento_fechar_original = mw.closeEvent
        mw.closeEvent = self.ao_evento_fechar

    def ao_evento_fechar(self, evento):
        """
        Decide se o aplicativo deve fechar ou ir para a bandeja. [cite: 83]
        """
        if self.fechamento_real:
            self.evento_fechar_original(evento)
            return
        
        # Lê a preferência do usuário (Bandeja ou Sair) [cite: 83]
        acao = self.obter_config("acao_ao_fechar")
        if acao == ACAO_BANDEJA:
            # Cancela o fechamento e apenas oculta a janela [cite: 83]
            evento.ignore()
            self.esconder_para_bandeja()
        else:
            # Executa o fechamento padrão do Anki [cite: 83]
            self.evento_fechar_original(evento)

# Instancia o objeto global para ativar o gerenciamento da bandeja [cite: 83]
gerenciador_bandeja = GerenciadorBandeja()