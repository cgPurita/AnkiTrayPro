# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: tray.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from .consts import *
# Importa a função de tradução para usar nos menus
from .lang import tr

class GerenciadorBandeja:
    """
    Gerencia a interação com a bandeja do sistema (System Tray).
    """
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
        self.icone_bandeja.setToolTip(DICA_BANDEJA)
        
        menu = QMenu()
        
        # Usa a função de tradução (tr) em vez de texto fixo
        acao_mostrar = QAction(tr("menu_abrir"), menu)
        acao_mostrar.triggered.connect(self.mostrar_janela)
        menu.addAction(acao_mostrar)
        
        # Usa a função de tradução (tr) em vez de texto fixo
        acao_sinc = QAction(tr("menu_sincronizar"), menu)
        acao_sinc.triggered.connect(lambda: mw.onSync())
        menu.addAction(acao_sinc)

        menu.addSeparator()

        # Usa a função de tradução (tr) em vez de texto fixo
        acao_sair = QAction(tr("menu_sair_total"), menu)
        acao_sair.triggered.connect(self.forcar_saida)
        menu.addAction(acao_sair)

        self.icone_bandeja.setContextMenu(menu)
        self.icone_bandeja.activated.connect(self.ao_clicar_icone)

    def ao_clicar_icone(self, razao):
        if razao == QSystemTrayIcon.ActivationReason.Trigger:
            self.mostrar_janela()

    def mostrar_janela(self):
        mw.show()
        estado_atual = mw.windowState()
        mw.setWindowState(estado_atual & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        mw.activateWindow()
        mw.raise_()
        if self.icone_bandeja: self.icone_bandeja.hide()

    def esconder_para_bandeja(self):
        if self.obter_config("sincronizar_na_bandeja"):
            mw.onSync()
        if self.icone_bandeja: self.icone_bandeja.show()
        mw.hide()

    def forcar_saida(self):
        # Garante a sincronização antes de sair
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