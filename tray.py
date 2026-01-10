# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: tray.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from .consts import * # Importa nossas constantes (ACAO_BANDEJA, etc)

class GerenciadorBandeja:
    """
    Gerencia o ícone na área de notificação e intercepta os eventos de 
    fechar e minimizar da janela principal.
    """
    def __init__(self):
        self.icone_bandeja = None
        
        # Configura o visual e menus do ícone
        self.configurar_icone_bandeja()
        
        # Instala os "ganchos" para alterar como o Anki reage ao fechar/minimizar
        self.configurar_ganchos()

    def obter_config(self, chave):
        """Atalho para ler uma chave específica da configuração."""
        return mw.addonManager.getConfig(__name__).get(chave)

    def configurar_icone_bandeja(self):
        """Cria o ícone, define o tooltip e o menu de contexto (botão direito)."""
        
        # Cria o objeto do ícone vinculado à janela principal (mw)
        self.icone_bandeja = QSystemTrayIcon(mw)
        
        # Define a imagem do ícone (usa o ícone padrão do Anki)
        self.icone_bandeja.setIcon(QIcon(":/icons/anki.png"))
        
        # Define o texto que aparece ao passar o mouse
        self.icone_bandeja.setToolTip(DICA_BANDEJA)
        
        # --- Criação do Menu (Botão Direito) ---
        menu = QMenu()
        
        # Opção 1: Abrir o Anki
        acao_mostrar = QAction("Abrir Anki", menu)
        acao_mostrar.triggered.connect(self.mostrar_janela)
        menu.addAction(acao_mostrar)
        
        # Opção 2: Sincronizar (Útil para não ter que abrir a janela só para isso)
        acao_sinc = QAction("Sincronizar", menu)
        # Usa uma função lambda para chamar o sincronizador nativo do Anki
        acao_sinc.triggered.connect(lambda: mw.onSync())
        menu.addAction(acao_sinc)

        menu.addSeparator() # Linha divisória visual

        # Opção 3: Sair totalmente (Matar o processo)
        acao_sair = QAction("Sair Totalmente", menu)
        acao_sair.triggered.connect(self.forcar_saida)
        menu.addAction(acao_sair)

        # Anexa o menu criado ao ícone
        self.icone_bandeja.setContextMenu(menu)
        
        # Conecta o clique no ícone (esquerdo ou duplo) a uma função
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)

    def ao_clicar_icone(self, razao):
        """Reage quando o usuário clica no ícone da bandeja."""
        # Se for um clique de ativação (geralmente clique simples ou duplo dependendo do OS)
        if razao == QSystemTrayIcon.Trigger:
            self.mostrar_janela()

    def mostrar_janela(self):
        """Restaura a janela do Anki e esconde o ícone da bandeja."""
        mw.show() # Torna a janela visível
        
        # Remove o estado de 'Minimizado' e garante que ela está 'Ativa'
        estado_atual = mw.windowState()
        mw.setWindowState(estado_atual & ~Qt.WindowMinimized | Qt.WindowActive)
        
        mw.activateWindow() # Foca na janela
        mw.raise_()         # Traz para frente de outras janelas
        
        self.icone_bandeja.hide() # Esconde o ícone da bandeja pois a janela está aberta

    def esconder_para_bandeja(self):
        """Minimiza o Anki, mostra o ícone na bandeja e opcionalmente sincroniza."""
        
        # Verifica na config se deve sincronizar antes de esconder
        if self.obter_config("sincronizar_na_bandeja"):
            mw.onSync()

        # Mostra o ícone na bandeja antes de esconder a janela (para o usuário ver para onde foi)
        self.icone_bandeja.show()
        
        # Esconde a janela principal
        mw.hide()
        
        # Mostra um balão informativo rápido (1 segundo)
        self.icone_bandeja.showMessage(
            NOME_APP, 
            "Minimizado para a bandeja.", 
            QSystemTrayIcon.Information, 
            1000
        )

    def forcar_saida(self):
        """Fecha o aplicativo Anki verdadeiramente."""
        mw.app.quit()

    # --- INTERCEPTAÇÃO DE EVENTOS (HOOKS) ---

    def configurar_ganchos(self):
        """Substitui as funções originais do Anki pelas nossas."""
        
        # Salva a função original de fechar para podermos chamá-la se necessário
        self.evento_fechar_original = mw.closeEvent
        # Substitui pela nossa
        mw.closeEvent = self.ao_evento_fechar
        
        # Salva a função original de mudança de estado (minimizar/maximizar)
        self.evento_mudanca_original = mw.changeEvent
        # Substitui pela nossa
        mw.changeEvent = self.ao_evento_mudanca

    def ao_evento_fechar(self, evento):
        """Chamado quando o usuário clica no 'X' da janela."""
        acao = self.obter_config("acao_ao_fechar")
        
        if acao == ACAO_BANDEJA:
            # Se a config for 'tray', ignoramos o pedido de fechamento
            evento.ignore()
            # E executamos nossa lógica de esconder
            self.esconder_para_bandeja()
        else:
            # Se for 'quit' ou outra coisa, deixamos o Anki fechar normalmente
            # chamando a função original que salvamos antes.
            self.evento_fechar_original(evento)

    def ao_evento_mudanca(self, evento):
        """Chamado quando a janela muda de estado (ex: é minimizada)."""
        
        # Verifica se o tipo de evento foi uma mudança de estado da janela
        if evento.type() == QEvent.WindowStateChange:
            # Verifica se o estado atual é 'Minimizado'
            if mw.windowState() & Qt.WindowMinimized:
                acao = self.obter_config("acao_ao_minimizar")
                
                if acao == ACAO_BANDEJA:
                    # Usamos um Timer de 0ms para agendar a execução para o próximo ciclo
                    # Isso evita bugs visuais no Qt ao tentar esconder durante o evento de minimizar
                    QTimer.singleShot(0, self.esconder_para_bandeja)
        
        # Sempre chama o evento original para não quebrar outras funcionalidades do Anki
        self.evento_mudanca_original(evento)

# Instância global
gerenciador_bandeja = GerenciadorBandeja()