# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: tray.py
# -------------------------------------------------------------------------
from aqt import mw  # Importa a janela principal do Anki (MainWindow)
from aqt.qt import * # Importa todos os componentes da interface gráfica Qt (PyQt/PySide)
from .consts import * # Importa as constantes definidas no projeto (nomes, ações, etc)
# Importa a função de tradução para usar nos menus de contexto
from .lang import tr

class GerenciadorBandeja:
    """
    Gerencia a interação com a bandeja do sistema (System Tray).
    Controla o ícone, o menu de contexto e os eventos de clique.
    """
    def __init__(self):
        """
        Construtor da classe. Inicializa as variáveis e configura os eventos.
        """
        self.icone_bandeja = None  # Variável para armazenar o objeto do ícone
        self.fechamento_real = False  # Flag para distinguir entre minimizar e fechar realmente o programa
        self.configurar_ganchos()  # Configura a interceptação do botão 'X' da janela
        self.configurar_icone_bandeja()  # Cria e configura o ícone visual na bandeja

    def obter_config(self, chave):
        """
        Lê uma configuração específica do add-on através do gerenciador do Anki.
        """
        return mw.addonManager.getConfig(__name__).get(chave)

    def configurar_icone_bandeja(self):
        """
        Cria o ícone da bandeja, define seu menu e conecta as ações de clique.
        """
        # Se o ícone já existe, não faz nada para evitar duplicidade
        if self.icone_bandeja: return
        
        # Cria uma instância do ícone de bandeja vinculada à janela principal
        self.icone_bandeja = QSystemTrayIcon(mw)
        
        # Define a imagem do ícone como sendo a mesma da janela do Anki
        self.icone_bandeja.setIcon(mw.windowIcon())
        
        # Define o texto que aparece ao passar o mouse (tooltip)
        self.icone_bandeja.setToolTip(DICA_BANDEJA)
        
        # Cria o menu de contexto (clique com botão direito)
        menu = QMenu()
        
        # Cria a ação de "Abrir/Mostrar" usando o texto traduzido
        acao_mostrar = QAction(tr("menu_abrir"), menu)
        # Conecta o clique dessa ação à função que restaura a janela
        acao_mostrar.triggered.connect(self.mostrar_janela)
        # Adiciona a ação ao menu visual
        menu.addAction(acao_mostrar)
        
        # Cria a ação de "Sincronizar" usando o texto traduzido
        acao_sinc = QAction(tr("menu_sincronizar"), menu)
        # Conecta a uma função lambda que chama a sincronização do Anki
        acao_sinc.triggered.connect(lambda: mw.onSync())
        menu.addAction(acao_sinc)

        # Adiciona uma linha separadora visual no menu
        menu.addSeparator()

        # Cria a ação de "Sair Totalmente" usando o texto traduzido
        acao_sair = QAction(tr("menu_sair_total"), menu)
        # Conecta à função que encerra o programa de vez
        acao_sair.triggered.connect(self.forcar_saida)
        menu.addAction(acao_sair)

        # Define o menu criado como o menu de contexto do ícone
        self.icone_bandeja.setContextMenu(menu)
        
        # Conecta o clique simples/duplo no ícone à função 'ao_clicar_icone'
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)

        # --- NOVA FUNCIONALIDADE AQUI ---
        # Conecta o evento de "Clicar na mensagem (balão)" à função que abre a janela.
        # Assim, quando o usuário clicar na notificação, o Anki se abre.
        self.icone_bandeja.messageClicked.connect(self.mostrar_janela)

    def ao_clicar_icone(self, razao):
        """
        Trata os eventos de clique direto no ícone da bandeja (não no menu).
        """
        # Se a razão do evento for um clique (Trigger), mostra a janela
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            self.mostrar_janela()

    def mostrar_janela(self):
        """
        Restaura a janela do Anki, tirando-a do estado minimizado e trazendo para frente.
        """
        # Torna a janela visível (caso esteja oculta)
        mw.show()
        
        # Obtém o estado atual da janela
        estado_atual = mw.windowState()
        
        # Remove o estado de 'Minimizado' e adiciona o estado de 'Ativo'
        # Isso garante que a janela saia da barra de tarefas e abra na tela
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        
        # Traz a janela para o foco do sistema operacional
        mw.activateWindow()
        
        # Força a janela a ficar sobre as outras janelas momentaneamente
        mw.raise_()
        
        # Oculta o ícone da bandeja, pois o programa agora está aberto na barra de tarefas
        if self.icone_bandeja: self.icone_bandeja.hide()

    def esconder_para_bandeja(self):
        """
        Oculta a janela principal e mostra o ícone na bandeja.
        """
        # Verifica a configuração se deve sincronizar antes de esconder
        if self.obter_config("sincronizar_na_bandeja"):
            mw.onSync()
            
        # Mostra o ícone na bandeja antes de esconder a janela (para o usuário ver para onde foi)
        if self.icone_bandeja: self.icone_bandeja.show()
        
        # Oculta a janela principal do Anki
        mw.hide()

    def forcar_saida(self):
        """
        Encerra o aplicativo, garantindo que não seja apenas minimizado.
        """
        # Garante a sincronização antes de sair para não perder dados
        mw.onSync()
        
        # Define a flag como True para que o evento 'closeEvent' saiba que deve fechar de verdade
        self.fechamento_real = True
        
        # Chama o fechamento da janela principal
        mw.close()

    def configurar_ganchos(self):
        """
        Substitui o evento padrão de fechar janela do Anki pelo nosso método personalizado.
        """
        # Salva o método original de fechar para poder chamá-lo depois se necessário
        self.evento_fechar_original = mw.closeEvent
        
        # Substitui o método da janela pelo nosso 'ao_evento_fechar'
        mw.closeEvent = self.ao_evento_fechar

    def ao_evento_fechar(self, evento):
        """
        Intercepta a tentativa de fechar a janela (clique no X).
        Decide se fecha ou minimiza baseando-se na configuração.
        """
        # Se a flag de fechamento real estiver ativa (clicou em Sair no menu), fecha normal
        if self.fechamento_real:
            self.evento_fechar_original(evento)
            return
        
        # Obtém a configuração do usuário sobre o que fazer ao fechar
        acao = self.obter_config("acao_ao_fechar")
        
        # Se a ação for "ir para bandeja"
        if acao == ACAO_BANDEJA:
            # Ignora o evento de fechamento (não mata o processo)
            evento.ignore()
            # Chama nossa função de esconder
            self.esconder_para_bandeja()
        else:
            # Se for para fechar mesmo, chama o evento original
            self.evento_fechar_original(evento)

# Instancia o gerenciador globalmente para que comece a funcionar ao importar
gerenciador_bandeja = GerenciadorBandeja()