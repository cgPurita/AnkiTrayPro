# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: __init__.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from aqt import gui_hooks

from .tray import gerenciador_bandeja
from .gui import mostrar_configuracoes
from .lang import tr
from .notifications import notificador

def ao_carregar_perfil():
    """
    Executado assim que o perfil do usuário é carregado.
    Detecta se o Anki foi iniciado via atalho minimizado.
    """
    # Não lemos mais a configuração aqui. Confiamos no estado da janela.
    # Se o atalho foi configurado com WindowStyle=7 (Minimizado), 
    # o Qt reportará a janela como minimizada.
    
    # Verifica se a janela principal está minimizada
    if mw.isMinimized():
        # Se sim, movemos para a bandeja (escondemos da barra de tarefas)
        gerenciador_bandeja.esconder_para_bandeja()

def configurar_menu():
    """Adiciona a opção de configuração no menu 'Ferramentas' do Anki."""
    acao = QAction(tr("nome_menu"), mw)
    acao.triggered.connect(mostrar_configuracoes)
    mw.form.menuTools.addAction(acao)
    
# --- Registro dos Ganchos ---

gui_hooks.profile_did_open.append(ao_carregar_perfil)
configurar_menu()