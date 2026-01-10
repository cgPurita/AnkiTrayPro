# Importa o módulo principal da interface gráfica do Anki
import aqt
# Importa a referência para a janela principal do Anki
from aqt import mw
# Importa as classes necessárias da biblioteca gráfica Qt para interface e eventos
from aqt.qt import QAction, QMenu, QSystemTrayIcon, QIcon

# Define a classe responsável pelo ícone na bandeja do sistema
class AnkiTrayIcon(QSystemTrayIcon):
    # Método construtor da classe do ícone da bandeja
    def __init__(self, parent=None):
        # Inicializa a classe pai QSystemTrayIcon
        super().__init__(parent)
        # Define o ícone visual a ser exibido na bandeja usando o recurso padrão do Anki
        self.setIcon(QIcon(":/icons/anki.png"))
        # Cria um menu de contexto para o ícone
        self.menu = QMenu(parent)
        
        # Cria a ação de interface para restaurar a janela
        self.action_restore = QAction("Restaurar", self)
        # Conecta o gatilho da ação à função de restauração
        self.action_restore.triggered.connect(self.restore_anki)
        
        # Cria a ação de interface para encerrar o aplicativo
        self.action_quit = QAction("Sair", self)
        # Conecta o gatilho da ação à função de encerramento
        self.action_quit.triggered.connect(self.quit_anki)
        
        # Adiciona a ação de restaurar ao menu de contexto
        self.menu.addAction(self.action_restore)
        # Adiciona a ação de sair ao menu de contexto
        self.menu.addAction(self.action_quit)
        
        # Define o menu configurado como o menu de contexto oficial do ícone
        self.setContextMenu(self.menu)
        
        # Conecta o evento de ativação do ícone (clique) à função tratadora
        self.activated.connect(self.on_tray_activated)

    # Função que restaura a janela principal do Anki para o estado visível
    def restore_anki(self):
        # Torna a janela principal visível
        mw.show()
        # Restaura o estado da janela, removendo a minimização e ativando-a
        mw.setWindowState(mw.windowState() & ~aqt.qt.Qt.WindowState.WindowMinimized | aqt.qt.Qt.WindowState.WindowActive)
        # Traz a janela para o primeiro plano do sistema
        mw.activateWindow()
        # Eleva a janela sobre as outras para garantir foco
        mw.raise_()

    # Função que encerra a aplicação Anki
    def quit_anki(self):
        # Oculta o ícone da bandeja visualmente
        self.hide()
        # Encerra o processo da aplicação com código de saída 0
        mw.app.exit(0)

    # Função que trata os eventos de clique no ícone da bandeja
    def on_tray_activated(self, reason):
        # Verifica se a ativação foi um clique simples (gatilho)
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Chama a função de restaurar a janela
            self.restore_anki()

# Inicializa a variável global que conterá a instância do ícone
tray_icon = None

# Função que instancia e exibe o ícone na bandeja se ainda não existir
def create_tray_icon():
    # Referencia a variável global
    global tray_icon
    # Verifica se o ícone ainda não foi instanciado
    if tray_icon is None:
        # Instancia a classe do ícone passando a janela principal como pai
        tray_icon = AnkiTrayIcon(mw)
        # Exibe o ícone na bandeja do sistema
        tray_icon.show()

# Armazena a referência do evento original de fechamento da janela
original_close_event = mw.closeEvent

# Função personalizada para tratar o evento de fechamento da janela
def custom_close_event(event):
    # Carrega a configuração do addon ou define padrão como True
    config = mw.addonManager.getConfig(__name__) or {"minimize_to_tray": True}
    
    # Verifica se a configuração de minimizar para a bandeja está ativa
    if config.get("minimize_to_tray", True):
        # Dispara a sincronização do Anki para garantir o salvamento de dados
        mw.onSync()
        
        # Ignora o evento de fechamento padrão para impedir o encerramento do processo
        event.ignore()
        # Oculta a janela principal do usuário
        mw.hide()
        # Garante a criação e exibição do ícone na bandeja
        create_tray_icon()
        
    else:
        # Executa o evento de fechamento original se a configuração estiver inativa
        original_close_event(event)

# Substitui o manipulador de evento de fechamento da janela pela função personalizada
mw.closeEvent = custom_close_event

# Função intermediária para abrir a janela de configuração do addon
def open_config():
    # Chama o gerenciador de addons para abrir a configuração deste módulo específico
    mw.addonManager.toggleConfig(__name__)

# Função responsável por criar o item de menu na aba Tools
def setup_menu():
    # Cria a ação visual com o nome que aparecerá no menu
    action = QAction("Configurações Anki Tray Pro", mw)
    # Conecta o clique na ação à função que abre a configuração
    action.triggered.connect(open_config)
    # Adiciona a ação criada ao menu Tools (Ferramentas) da janela principal
    mw.form.menuTools.addAction(action)

# Função chamada para inicializar o addon
def init_addon():
    # Cria o ícone da bandeja imediatamente ao iniciar
    create_tray_icon()
    # Configura e adiciona o item ao menu Tools
    setup_menu()

# Adiciona a função de inicialização ao gancho de abertura de perfil do Anki
aqt.gui_hooks.profile_did_open.append(init_addon)