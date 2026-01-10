# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
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
        # Cria e configura o ícone na área de notificação do Windows
        self.configurar_icone_bandeja()

    def obter_config(self, chave):
        # Busca uma configuração específica no gerenciador de complementos do Anki
        return mw.addonManager.getConfig(__name__).get(chave)

    def configurar_icone_bandeja(self):
        """
        Cria o ícone na bandeja, define o menu de contexto e o tooltip traduzido.
        """
        # Evita a criação duplicada do ícone
        if self.icone_bandeja: return
        
        # Cria o objeto do ícone vinculado à janela principal
        self.icone_bandeja = QSystemTrayIcon(mw)
        # Define o ícone visual usando o ícone oficial do Anki
        self.icone_bandeja.setIcon(mw.windowIcon())
        
        # DEFINE O TOOLTIP USANDO A TRADUÇÃO VARIÁVEL
        # O texto agora depende do idioma configurado no perfil do usuário
        self.icone_bandeja.setToolTip(tr("tooltip_tray"))
        
        # Cria o menu que aparece ao clicar com o botão direito no ícone
        menu = QMenu()
        
        # Ação para restaurar a janela principal
        acao_mostrar = QAction(tr("menu_abrir"), menu)
        acao_mostrar.triggered.connect(self.mostrar_janela)
        menu.addAction(acao_mostrar)
        
        # Ação para forçar uma sincronização manual
        acao_sinc = QAction(tr("menu_sincronizar"), menu)
        acao_sinc.triggered.connect(lambda: mw.onSync())
        menu.addAction(acao_sinc)

        # Divisor visual no menu
        menu.addSeparator()

        # Ação para encerrar o Anki definitivamente
        acao_sair = QAction(tr("menu_sair_total"), menu)
        acao_sair.triggered.connect(self.forcar_saida)
        menu.addAction(acao_sair)

        # Atribui o menu ao ícone e conecta o clique do botão esquerdo
        self.icone_bandeja.setContextMenu(menu)
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)
        
        # Permite abrir a janela ao clicar em um balão de notificação
        self.icone_bandeja.messageClicked.connect(self.mostrar_janela)

    def ao_clicar_icone(self, razao):
        # Se o ícone for clicado normalmente, restaura a janela
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            self.mostrar_janela()

    def mostrar_janela(self):
        """
        Restaura a janela do Anki para o primeiro plano.
        """
        # Garante que a janela seja exibida e ganhe foco
        mw.show()
        estado_atual = mw.windowState()
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        mw.activateWindow()
        mw.raise_()
        
        # Esconde o ícone da bandeja enquanto a janela está aberta
        if self.icone_bandeja: self.icone_bandeja.hide()

        # Reseta a contagem de referência do notificador
        from .notifications import notificador
        notificador.resetar_contagem()

    def esconder_para_bandeja(self):
        """
        Oculta a janela e garante que o usuário saia do modo de revisão.
        """
        # [cite_start]LÓGICA DE SEGURANÇA: Se estiver respondendo um cartão, volta para a tela inicial [cite: 81]
        if mw.state == "review":
            # Força o retorno para o navegador de baralhos antes de ocultar
            mw.deckBrowser.show()
            
        # [cite_start]Sincroniza se a opção estiver ativada nas configurações [cite: 81]
        if self.obter_config("sincronizar_na_bandeja"):
            mw.onSync()
            
        # [cite_start]Exibe o ícone na bandeja e oculta a janela principal [cite: 81]
        if self.icone_bandeja: self.icone_bandeja.show()
        mw.hide()

        # [cite_start]Atualiza o notificador para considerar o estado atual como "visto" [cite: 82]
        from .notifications import notificador
        notificador.resetar_contagem()

    def forcar_saida(self):
        """
        Sincroniza e encerra o aplicativo completamente.
        """
        mw.onSync()
        self.fechamento_real = True
        mw.close()

    def configurar_ganchos(self):
        """
        Intercepta o evento de fechamento da janela principal.
        """
        self.evento_fechar_original = mw.closeEvent
        mw.closeEvent = self.ao_evento_fechar

    def ao_evento_fechar(self, evento):
        """
        Decide se o aplicativo deve fechar ou ir para a bandeja.
        """
        if self.fechamento_real:
            self.evento_fechar_original(evento)
            return
        
        # [cite_start]Lê a preferência do usuário (Bandeja ou Sair) [cite: 83]
        acao = self.obter_config("acao_ao_fechar")
        if acao == ACAO_BANDEJA:
            # Cancela o fechamento e apenas oculta a janela
            evento.ignore()
            self.esconder_para_bandeja()
        else:
            # Executa o fechamento padrão do Anki
            self.evento_fechar_original(evento)

# Instancia o objeto global para ativar o gerenciamento da bandeja
gerenciador_bandeja = GerenciadorBandeja()