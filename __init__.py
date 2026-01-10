# Importa o módulo principal da interface gráfica do Anki
import aqt
# Importa a referência para a janela principal do Anki
from aqt import mw
# Importa as classes necessárias da biblioteca gráfica Qt para interface e eventos
from aqt.qt import QAction, QMenu, QSystemTrayIcon, QIcon, QEvent, QTimer
# Importa utilitários do Anki, embora não usados diretamente neste bloco lógico final, mantidos para compatibilidade
from aqt.utils import tooltip

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
        # Dispara a sincronização do Anki
        mw.onSync()
        
        # Ignora o evento de fechamento padrão para impedir o encerramento do processo
        event.ignore()
        # Oculta a janela principal
        mw.hide()
        # Garante a criação e exibição do ícone na bandeja
        create_tray_icon()
        
    else:
        # Executa o evento de fechamento original se a configuração estiver inativa
        original_close_event(event)

# Armazena a referência do evento original de mudança de estado da janela
original_change_event = mw.changeEvent

# Função personalizada para tratar mudanças de estado da janela (ex: minimizar)
def custom_change_event(event):
    # Verifica se o evento é uma mudança de estado da janela
    if event.type() == QEvent.Type.WindowStateChange:
        # Verifica se o novo estado inclui a janela minimizada
        if mw.windowState() & aqt.qt.Qt.WindowState.WindowMinimized:
            # Carrega a configuração do addon
            config = mw.addonManager.getConfig(__name__) or {"minimize_to_tray": True}
            
            # Verifica se a configuração de minimizar para bandeja está ativa
            if config.get("minimize_to_tray", True):
                # Agenda o ocultamento da janela para o próximo ciclo de eventos imediato
                QTimer.singleShot(0, mw.hide)
                # Garante a existência do ícone na bandeja
                create_tray_icon()
    
    # Executa o tratamento original para outros eventos de mudança de estado
    original_change_event(event)

# Substitui o manipulador de evento de fechamento da janela pela função personalizada
mw.closeEvent = custom_close_event

# Substitui o manipulador de evento de mudança de estado pela função personalizada
mw.changeEvent = custom_change_event

# Função chamada para inicializar o addon
def init_addon():
    # Cria o ícone da bandeja
    create_tray_icon()

# Adiciona a função de inicialização ao gancho de abertura de perfil do Anki
aqt.gui_hooks.profile_did_open.append(init_addon)