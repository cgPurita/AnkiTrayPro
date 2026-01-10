# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: tray.py
# -------------------------------------------------------------------------

# Importa a janela principal do Anki (MainWindow) através do objeto 'mw'
from aqt import mw
# Importa componentes da interface gráfica Qt (botões, menus, ícones, ações)
from aqt.qt import *
# Importa as constantes definidas no arquivo consts.py (ex: chaves de configuração)
from .consts import *
# Importa a função de tradução para suportar múltiplos idiomas
from .lang import tr

class GerenciadorBandeja:
    """
    Classe responsável por gerenciar a interação do add-on com a bandeja do sistema (System Tray).
    Controla o ícone, o menu de contexto e as ações de minimizar/restaurar.
    """
    def __init__(self):
        # Inicializa a variável que guardará a referência ao ícone da bandeja como Nula
        self.icone_bandeja = None
        # Define uma flag para diferenciar o fechamento real do programa da minimização
        self.fechamento_real = False
        # Chama o método que substitui os eventos padrões de fechar janela do Anki
        self.configurar_ganchos()
        # Chama o método que cria visualmente o ícone na bandeja do sistema
        self.configurar_icone_bandeja()

    def obter_config(self, chave):
        # Acessa o gerenciador de configurações do Anki para ler uma chave específica deste add-on
        return mw.addonManager.getConfig(__name__).get(chave)

    def configurar_icone_bandeja(self):
        # Se o ícone já estiver criado, não faz nada para evitar duplicação e erros de memória
        if self.icone_bandeja: return
        
        # Cria uma nova instância de ícone de bandeja vinculada à janela principal (mw)
        self.icone_bandeja = QSystemTrayIcon(mw)
        # Define a imagem do ícone usando o mesmo ícone da janela principal do Anki
        self.icone_bandeja.setIcon(mw.windowIcon())
        # Define o texto que aparece ao passar o mouse sobre o ícone (Tooltip)
        self.icone_bandeja.setToolTip(DICA_BANDEJA)
        
        # Cria um menu de contexto (o menu que abre ao clicar com botão direito no ícone)
        menu = QMenu()
        
        # Cria a ação de "Abrir" ou "Mostrar" o Anki no menu
        acao_mostrar = QAction(tr("menu_abrir"), menu)
        # Conecta o clique dessa ação à função 'mostrar_janela'
        acao_mostrar.triggered.connect(self.mostrar_janela)
        # Adiciona essa ação ao menu visível
        menu.addAction(acao_mostrar)
        
        # Cria a ação de "Sincronizar" diretamente pela bandeja
        acao_sinc = QAction(tr("menu_sincronizar"), menu)
        # Conecta o clique a uma função lambda que chama a sincronização nativa do Anki
        acao_sinc.triggered.connect(lambda: mw.onSync())
        # Adiciona essa ação ao menu visível
        menu.addAction(acao_sinc)

        # Adiciona uma linha separadora visual no menu para organizar as opções
        menu.addSeparator()

        # Cria a ação de "Sair Totalmente" (encerrar o processo do Anki)
        acao_sair = QAction(tr("menu_sair_total"), menu)
        # Conecta o clique à função 'forcar_saida' que encerra o app
        acao_sair.triggered.connect(self.forcar_saida)
        # Adiciona essa ação ao menu visível
        menu.addAction(acao_sair)

        # Define o menu criado como o menu de contexto oficial do ícone da bandeja
        self.icone_bandeja.setContextMenu(menu)
        
        # Conecta o evento de clique no ícone (botão esquerdo) à função de tratamento
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)
        
        # Conecta o clique no balão de notificação para abrir o Anki automaticamente quando notificado
        self.icone_bandeja.messageClicked.connect(self.mostrar_janela)

    def ao_clicar_icone(self, razao):
        # Verifica se a razão da ativação foi um clique simples (Trigger)
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            # Se foi clique simples, executa a restauração da janela do Anki
            self.mostrar_janela()

    def mostrar_janela(self):
        """
        Restaura a janela do Anki, trazendo-a para frente e tornando-a visível.
        """
        # Comando Qt para tornar a janela visível caso esteja oculta
        mw.show()
        # Obtém o estado atual da janela (minimizada, maximizada, etc.)
        estado_atual = mw.windowState()
        # Remove o estado de 'Minimizado' e adiciona o estado de 'Ativa', forçando a restauração visual
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        # Tenta ativar a janela no sistema operacional (foco)
        mw.activateWindow()
        # Traz a janela para o topo da pilha de janelas do sistema
        mw.raise_()
        
        # Se o ícone da bandeja existe, nós o escondemos pois o app está visível na barra de tarefas
        if self.icone_bandeja: self.icone_bandeja.hide()

        # Importa o notificador aqui para evitar importação circular no início do arquivo
        from .notifications import notificador
        # Reseta a contagem de notificações, pois o usuário está vendo a tela agora
        notificador.resetar_contagem()

    def esconder_para_bandeja(self):
        """
        Oculta a janela principal e envia para a bandeja.
        Inclui lógica de segurança para sair do modo de revisão se necessário.
        """
        # --- LÓGICA DE SEGURANÇA: SAIR DA REVISÃO ---
        # Verifica se o estado atual do Anki é 'review' (estudando cartão)
        if mw.state == "review":
            # Se estiver estudando, força o retorno para a tela de lista de baralhos (DeckBrowser)
            mw.deckBrowser.show()
        
        # Verifica se a configuração de sincronização automática está ativada
        if self.obter_config("sincronizar_na_bandeja"):
            # Chama a sincronização do Anki antes de esconder
            mw.onSync()
            
        # Se o ícone da bandeja estiver configurado, mostra ele agora para o usuário não perder o acesso
        if self.icone_bandeja: self.icone_bandeja.show()
        
        # Esconde a janela principal do Anki da barra de tarefas e da tela
        mw.hide()

        # Importa o notificador localmente
        from .notifications import notificador
        # Reseta a contagem de notificações, definindo o estado atual como "visto"
        notificador.resetar_contagem()

    def forcar_saida(self):
        # Garante uma sincronização final dos dados antes de fechar o programa
        mw.onSync()
        # Marca a flag de fechamento real como Verdadeira para ignorar o gancho de minimização
        self.fechamento_real = True
        # Chama o fechamento da janela principal (que agora não será interceptado)
        mw.close()

    def configurar_ganchos(self):
        # Salva o evento original de fechamento do Anki para poder chamá-lo depois se necessário
        self.evento_fechar_original = mw.closeEvent
        # Substitui o evento de fechar do Anki pelo nosso método personalizado 'ao_evento_fechar'
        mw.closeEvent = self.ao_evento_fechar

    def ao_evento_fechar(self, evento):
        # Verifica se é um fechamento real (solicitado pelo menu "Sair Totalmente")
        if self.fechamento_real:
            # Chama o evento original e permite que o Anki feche normalmente
            self.evento_fechar_original(evento)
            return
        
        # Obtém a configuração do usuário sobre o que fazer ao fechar (Tray ou Quit)
        acao = self.obter_config("acao_ao_fechar")
        
        # Se a ação configurada for enviar para a bandeja (constante ACAO_BANDEJA)
        if acao == ACAO_BANDEJA:
            # Ignora o evento de fechamento (impede o programa de encerrar o processo)
            evento.ignore()
            # Chama nossa função de minimizar para a bandeja
            self.esconder_para_bandeja()
        else:
            # Se a configuração for sair ou padrão, executa o fechamento original
            self.evento_fechar_original(evento)

# Instancia o gerenciador de bandeja globalmente para que ele comece a funcionar ao carregar o add-on
gerenciador_bandeja = GerenciadorBandeja()