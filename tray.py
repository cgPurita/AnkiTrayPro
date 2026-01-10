# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
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
        # Inicializa a variável que guardará a referência ao ícone
        self.icone_bandeja = None
        
        # Instala os ganchos (hooks) nos eventos da janela principal do Anki
        self.configurar_ganchos()
        
        # Configura o aspecto visual do ícone e seus menus
        self.configurar_icone_bandeja()

    def obter_config(self, chave):
        """
        Acessa o gerenciador de addons do Anki para ler uma configuração salva.
        Retorna o valor associado à chave solicitada.
        """
        return mw.addonManager.getConfig(__name__).get(chave)

    def configurar_icone_bandeja(self):
        """
        Cria o objeto QSystemTrayIcon, define o ícone visual e constrói
        o menu de contexto que aparece ao clicar com o botão direito.
        """
        
        # Verifica se o ícone já existe para evitar recriação desnecessária
        if self.icone_bandeja:
            return

        # Cria a instância do ícone de bandeja associada à janela principal
        self.icone_bandeja = QSystemTrayIcon(mw)
        
        # Utiliza o próprio ícone da janela do Anki para manter a consistência visual
        self.icone_bandeja.setIcon(mw.windowIcon())
        
        # Define o texto que aparece quando o mouse repousa sobre o ícone
        self.icone_bandeja.setToolTip(DICA_BANDEJA)
        
        # Cria o menu de contexto (clique com botão direito)
        menu = QMenu()
        
        # Cria a ação para restaurar a janela principal
        acao_mostrar = QAction("Abrir Anki", menu)
        # Conecta o disparo da ação ao método que mostra a janela
        acao_mostrar.triggered.connect(self.mostrar_janela)
        # Adiciona a ação ao menu
        menu.addAction(acao_mostrar)
        
        # Cria a ação para forçar a sincronização
        acao_sinc = QAction("Sincronizar", menu)
        # Conecta diretamente ao método nativo de sincronização do Anki
        acao_sinc.triggered.connect(lambda: mw.onSync())
        # Adiciona a ação ao menu
        menu.addAction(acao_sinc)

        # Adiciona uma linha separadora visual no menu
        menu.addSeparator()

        # Cria a ação para encerrar o aplicativo completamente
        acao_sair = QAction("Sair Totalmente", menu)
        # Conecta ao método que fecha o programa
        acao_sair.triggered.connect(self.forcar_saida)
        # Adiciona a ação ao menu
        menu.addAction(acao_sair)

        # Atribui o menu criado ao ícone da bandeja
        self.icone_bandeja.setContextMenu(menu)
        
        # Conecta o evento de clique (esquerdo ou duplo) ao tratador de cliques
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)

    def ao_clicar_icone(self, razao):
        """
        Recebe o motivo (reason) do clique no ícone.
        Se for um clique de ativação (geralmente clique simples), restaura a janela.
        """
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            self.mostrar_janela()

    def mostrar_janela(self):
        """
        Traz a janela do Anki de volta para a tela, restaura se estiver minimizada
        e coloca o foco nela.
        """
        # Torna a janela visível
        mw.show()
        
        # Obtém o estado atual da janela
        estado_atual = mw.windowState()
        
        # Remove a flag de 'Minimizado' e adiciona a flag de 'Ativo'
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        
        # Solicita ativação da janela ao sistema operacional
        mw.activateWindow()
        # Traz a janela para o topo da pilha de janelas
        mw.raise_()
        
        # Oculta o ícone da bandeja, pois a janela principal já está visível
        if self.icone_bandeja:
            self.icone_bandeja.hide()

    def esconder_para_bandeja(self):
        """
        Realiza o procedimento de esconder o Anki: executa sincronia (se configurado),
        mostra o ícone na bandeja e oculta a janela principal.
        """
        
        # Verifica na configuração se deve sincronizar antes de esconder
        if self.obter_config("sincronizar_na_bandeja"):
            mw.onSync()

        # Garante que o ícone da bandeja esteja visível antes de sumir com a janela
        if self.icone_bandeja:
            self.icone_bandeja.show()
        
        # Oculta a janela principal do Anki
        mw.hide()
        
        # Exibe um balão de notificação informando que o programa continua rodando
        if self.icone_bandeja:
            self.icone_bandeja.showMessage(
                NOME_APP, 
                "Minimizado para a bandeja.", 
                QSystemTrayIcon.MessageIcon.Information, 
                1000
            )

    def forcar_saida(self):
        """
        Encerra a instância da aplicação Qt, fechando o Anki definitivamente.
        """
        mw.app.quit()

    # --- Tratamento de Eventos (Hooks) ---

    def configurar_ganchos(self):
        """
        Substitui os métodos originais de evento da janela principal (mw) pelos
        métodos personalizados desta classe.
        """
        # Salva referência ao evento de fechar original
        self.evento_fechar_original = mw.closeEvent
        # Substitui pelo nosso método
        mw.closeEvent = self.ao_evento_fechar
        
        # Salva referência ao evento de mudança de estado original
        self.evento_mudanca_original = mw.changeEvent
        # Substitui pelo nosso método
        mw.changeEvent = self.ao_evento_mudanca

    def ao_evento_fechar(self, evento):
        """
        Intercepta o evento de fechamento da janela (botão X ou Alt+F4).
        """
        # Lê a configuração para saber qual ação tomar
        acao = self.obter_config("acao_ao_fechar")
        
        if acao == ACAO_BANDEJA:
            # Ignora o pedido de fechamento do sistema
            evento.ignore()
            # Executa a rotina de minimizar para a bandeja
            self.esconder_para_bandeja()
        else:
            # Se a ação for sair ou padrão, repassa para o tratamento original do Anki
            self.evento_fechar_original(evento)

    def ao_evento_mudanca(self, evento):
        """
        Intercepta eventos de mudança de estado da janela (ex: minimizar, maximizar).
        """
        # Verifica se o tipo de evento é uma mudança de estado da janela
        if evento.type() == QEvent.Type.WindowStateChange:
            # Verifica se o novo estado inclui a flag de minimizado
            if mw.windowState() & Qt.WindowState.WindowMinimized:
                # Lê a configuração do usuário para minimização
                acao = self.obter_config("acao_ao_minimizar")
                
                if acao == ACAO_BANDEJA:
                    # Agenda a execução do escondimento para o próximo ciclo do loop de eventos.
                    # Isso permite que o sistema operacional conclua animações pendentes.
                    QTimer.singleShot(50, self.esconder_para_bandeja)
        
        # Chama o tratador original para garantir que outras mudanças funcionem normalmente
        self.evento_mudanca_original(evento)

# Instancia o gerenciador globalmente para que inicie junto com o módulo
gerenciador_bandeja = GerenciadorBandeja()