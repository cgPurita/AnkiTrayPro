# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: tray.py
# -------------------------------------------------------------------------

# Importa o módulo 'os' para manipulação de caminhos de arquivos e pastas
import os
# Importa o módulo 'datetime' para registrar o horário exato dos eventos no log
import datetime
# Importa a janela principal do Anki (MainWindow) através do objeto 'mw'
from aqt import mw
# Importa componentes da interface gráfica Qt (botões, menus, ícones, timers)
from aqt.qt import *
# Importa as constantes definidas no arquivo consts.py (ex: chaves de configuração)
from .consts import *
# Importa a função de tradução para suportar múltiplos idiomas
from .lang import tr

class GerenciadorBandeja:
    """
    Classe responsável por gerenciar a interação do add-on com a bandeja do sistema (System Tray).
    Controla o ícone, o menu de contexto, as ações de minimizar/restaurar e o log de debug em arquivo.
    """
    def __init__(self):
        # Inicializa a variável que guardará a referência ao ícone da bandeja como Nula
        self.icone_bandeja = None
        # Define uma flag para diferenciar o fechamento real do programa da minimização
        self.fechamento_real = False
        # Define o caminho completo para o arquivo de log (debug_log.txt) na raiz do add-on
        self.caminho_log = os.path.join(os.path.dirname(__file__), "debug_log.txt")
        # Chama o método que substitui os eventos padrões de fechar janela do Anki
        self.configurar_ganchos()
        # Chama o método que cria visualmente o ícone na bandeja do sistema
        self.configurar_icone_bandeja()

    def obter_config(self, chave):
        # Acessa o gerenciador de configurações do Anki para ler uma chave específica deste add-on
        return mw.addonManager.getConfig(__name__).get(chave)

    def registrar_log(self, mensagem):
        """
        Escreve uma mensagem no arquivo debug_log.txt com carimbo de tempo.
        """
        try:
            # Obtém o horário atual formatado como string
            agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Abre o arquivo de log em modo de adição ('a' - append) com codificação UTF-8
            with open(self.caminho_log, "a", encoding="utf-8") as f:
                # Escreve a linha formatada no arquivo
                f.write(f"[{agora}] {mensagem}\n")
        except Exception as e:
            # Em caso de erro ao escrever o arquivo, falha silenciosamente para não travar o app
            pass

    def acao_adiada_debug(self):
        """
        Função executada 3 minutos após a minimização para verificar o estado do app.
        """
        # Registra no arquivo que o timer de 3 minutos disparou
        self.registrar_log("DEBUG: 3 minutos se passaram desde a minimização.")
        # Registra o estado atual da janela (se está visível ou oculta)
        self.registrar_log(f"DEBUG: Estado de visibilidade da janela: {mw.isVisible()}")
        # Registra o estado interno do Anki (deckBrowser, review, overview, etc.)
        self.registrar_log(f"DEBUG: Estado interno do Anki (mw.state): {mw.state}")
        # Registra uma linha separadora para facilitar a leitura
        self.registrar_log("-" * 30)

    def configurar_icone_bandeja(self):
        # Se o ícone já estiver criado, não faz nada para evitar duplicação
        if self.icone_bandeja: return
        
        # Cria uma nova instância de ícone de bandeja vinculada à janela principal (mw)
        self.icone_bandeja = QSystemTrayIcon(mw)
        # Define a imagem do ícone usando o mesmo ícone da janela principal do Anki
        self.icone_bandeja.setIcon(mw.windowIcon())
        # Define o texto que aparece ao passar o mouse sobre o ícone (Tooltip)
        self.icone_bandeja.setToolTip(DICA_BANDEJA)
        
        # Cria um menu de contexto (o menu que abre ao clicar com botão direito no ícone)
        menu = QMenu()
        
        # Cria a ação de "Abrir" ou "Mostrar" o Anki
        acao_mostrar = QAction(tr("menu_abrir"), menu)
        # Conecta o clique dessa ação à função 'mostrar_janela'
        acao_mostrar.triggered.connect(self.mostrar_janela)
        # Adiciona essa ação ao menu
        menu.addAction(acao_mostrar)
        
        # Cria a ação de "Sincronizar" diretamente pela bandeja
        acao_sinc = QAction(tr("menu_sincronizar"), menu)
        # Conecta o clique a uma função lambda que chama a sincronização do Anki
        acao_sinc.triggered.connect(lambda: mw.onSync())
        # Adiciona essa ação ao menu
        menu.addAction(acao_sinc)

        # Adiciona uma linha separadora visual no menu
        menu.addSeparator()

        # Cria a ação de "Sair Totalmente" (encerrar o processo do Anki)
        acao_sair = QAction(tr("menu_sair_total"), menu)
        # Conecta o clique à função 'forcar_saida'
        acao_sair.triggered.connect(self.forcar_saida)
        # Adiciona essa ação ao menu
        menu.addAction(acao_sair)

        # Define o menu criado como o menu de contexto oficial do ícone da bandeja
        self.icone_bandeja.setContextMenu(menu)
        
        # Conecta o evento de clique no ícone (botão esquerdo) à função de tratamento
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)
        
        # Conecta o clique no balão de notificação para abrir o Anki automaticamente
        self.icone_bandeja.messageClicked.connect(self.mostrar_janela)

    def ao_clicar_icone(self, razao):
        # Verifica se a razão da ativação foi um clique simples (Trigger)
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            # Se foi clique simples, restaura a janela do Anki
            self.mostrar_janela()

    def mostrar_janela(self):
        """
        Restaura a janela do Anki, trazendo-a para frente e tornando-a visível.
        """
        # Registra no log que a janela foi solicitada para abrir
        self.registrar_log("AÇÃO: Restaurando janela principal.")
        
        # Comando Qt para tornar a janela visível
        mw.show()
        # Obtém o estado atual da janela
        estado_atual = mw.windowState()
        # Remove o estado de 'Minimizado' e adiciona o estado de 'Ativa', forçando a restauração
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        # Tenta ativar a janela no sistema operacional
        mw.activateWindow()
        # Traz a janela para o topo da pilha de janelas
        mw.raise_()
        
        # Se o ícone da bandeja existe, nós o escondemos
        if self.icone_bandeja: self.icone_bandeja.hide()

        # --- CORREÇÃO: RESETAR CONTAGEM ---
        # Como o usuário abriu a janela, ele está VENDO os cartões.
        # Avisamos o notificador para atualizar a referência agora.
        from .notifications import notificador
        notificador.resetar_contagem()

    def esconder_para_bandeja(self):
        """
        Oculta a janela principal e envia para a bandeja.
        Inclui lógica de segurança para sair do modo de revisão e agendamento de log.
        """
        # Registra no log o início da minimização
        self.registrar_log("AÇÃO: Minimizando para a bandeja.")

        # --- LÓGICA DE SEGURANÇA: SAIR DA REVISÃO ---
        # Verificamos em qual estado o Anki está ("review", "overview", "deckBrowser", etc.)
        estado_anki = mw.state
        
        # Registra o estado atual antes de minimizar
        self.registrar_log(f"ESTADO ANTERIOR: {estado_anki}")

        # Se o estado for "review" (usuário estudando um cartão)
        if estado_anki == "review":
            # Registra que o reset será executado
            self.registrar_log("Resetando da Revisão para o DeckBrowser.")
            # Comando do Anki que força a interface a voltar para a lista de baralhos
            mw.deckBrowser.show()
        
        # Verifica se a configuração de sincronização automática está ativada
        if self.obter_config("sincronizar_na_bandeja"):
            # Registra que a sincronia foi solicitada
            self.registrar_log("Iniciando sincronização automática.")
            # Chama a sincronização do Anki
            mw.onSync()
            
        # Se o ícone da bandeja estiver configurado, mostra ele agora
        if self.icone_bandeja: self.icone_bandeja.show()
        
        # Esconde a janela principal do Anki
        mw.hide()

        # --- AGENDAMENTO DO DEBUG (3 MINUTOS) ---
        # QTimer.singleShot executa uma função após X milissegundos
        # 3 minutos = 3 * 60 * 1000 = 180000 ms
        self.registrar_log("Agendando verificação de debug para daqui a 3 minutos.")
        QTimer.singleShot(180000, self.acao_adiada_debug)

        # --- CORREÇÃO: RESETAR CONTAGEM ---
        # Ao minimizar, definimos o estado atual como "visto".
        from .notifications import notificador
        notificador.resetar_contagem()

    def forcar_saida(self):
        # Registra a saída no log
        self.registrar_log("AÇÃO: Saída forçada pelo menu.")
        # Garante uma sincronização final antes de fechar
        mw.onSync()
        # Marca a flag de fechamento real como Verdadeira
        self.fechamento_real = True
        # Chama o fechamento da janela principal (que agora não será interceptado)
        mw.close()

    def configurar_ganchos(self):
        # Salva o evento original de fechamento do Anki para poder chamá-lo depois se necessário
        self.evento_fechar_original = mw.closeEvent
        # Substitui o evento de fechar do Anki pelo nosso método personalizado
        mw.closeEvent = self.ao_evento_fechar

    def ao_evento_fechar(self, evento):
        # Verifica se é um fechamento real (solicitado pelo menu "Sair Totalmente")
        if self.fechamento_real:
            # Chama o evento original e permite que o Anki feche
            self.evento_fechar_original(evento)
            return
        
        # Obtém a configuração do usuário sobre o que fazer ao fechar (Tray ou Quit)
        acao = self.obter_config("acao_ao_fechar")
        
        # Se a ação configurada for enviar para a bandeja
        if acao == ACAO_BANDEJA:
            # Ignora o evento de fechamento (impede o programa de encerrar)
            evento.ignore()
            # Chama nossa função de minimizar
            self.esconder_para_bandeja()
        else:
            # Se a configuração for sair ou padrão, deixa o Anki fechar normalmente
            self.evento_fechar_original(evento)

# Instancia o gerenciador de bandeja globalmente
gerenciador_bandeja = GerenciadorBandeja()