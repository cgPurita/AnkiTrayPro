# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: tray.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from .consts import *
from .lang import tr

class GerenciadorBandeja:
    def __init__(self):
        self.icone_bandeja = None
        self.fechamento_real = False
        self.configurar_ganchos()
        self.configurar_icone_bandeja()

    def obter_config(self, chave):
        return mw.addonManager.getConfig(__name__).get(chave)

    def configurar_icone_bandeja(self):
        if self.icone_bandeja: return
        
        self.icone_bandeja = QSystemTrayIcon(mw)
        self.icone_bandeja.setIcon(mw.windowIcon())
        
        # Tooltip traduzido conforme solicitado
        self.icone_bandeja.setToolTip(tr("tooltip_tray"))
        
        menu = QMenu()
        acao_mostrar = QAction(tr("menu_abrir"), menu)
        acao_mostrar.triggered.connect(self.mostrar_janela)
        menu.addAction(acao_mostrar)
        
        acao_sinc = QAction(tr("menu_sincronizar"), menu)
        acao_sinc.triggered.connect(lambda: mw.onSync())
        menu.addAction(acao_sinc)

        menu.addSeparator()

        acao_sair = QAction(tr("menu_sair_total"), menu)
        acao_sair.triggered.connect(self.forcar_saida)
        menu.addAction(acao_sair)

        self.icone_bandeja.setContextMenu(menu)
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)
        self.icone_bandeja.messageClicked.connect(self.mostrar_janela)

    def ao_clicar_icone(self, razao):
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            self.mostrar_janela()

    def mostrar_janela(self):
        """Restaura a janela e força a atualização dos números na tela inicial."""
        mw.show()
        estado_atual = mw.windowState()
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        mw.activateWindow()
        mw.raise_()
        
        if self.icone_bandeja: self.icone_bandeja.hide()

        # --- AQUI ESTÁ A CORREÇÃO DA TELA INICIAL ---
        # Força o Anki a redesenhar a lista de baralhos agora que a janela está visível.
        # Isso garante que os números (2 vs 5) sejam corrigidos instantaneamente.
        mw.deckBrowser.refresh()

        from .notifications import notificador
        notificador.resetar_contagem()

    def esconder_para_bandeja(self):
        if mw.state == "review":
            mw.deckBrowser.show()
            
        if self.obter_config("sincronizar_na_bandeja"):
            mw.onSync()
            
        if self.icone_bandeja: self.icone_bandeja.show()
        mw.hide()

        from .notifications import notificador
        notificador.resetar_contagem()

    def forcar_saida(self):
        mw.onSync()
        self.fechamento_real = True
        mw.close()

    def configurar_ganchos(self):
        self.evento_fechar_original = mw.closeEvent
        mw.closeEvent = self.ao_evento_fechar

    def ao_evento_fechar(self, evento):
        if self.fechamento_real:
            self.evento_fechar_original(evento)
            return
        
        acao = self.obter_config("acao_ao_fechar")
        if acao == ACAO_BANDEJA:
            evento.ignore()
            self.esconder_para_bandeja()
        else:
            self.evento_fechar_original(evento)

gerenciador_bandeja = GerenciadorBandeja()