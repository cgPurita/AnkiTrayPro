# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: __init__.py
# -------------------------------------------------------------------------
import os
from aqt import mw
from aqt.qt import *
from aqt import gui_hooks

from .tray import gerenciador_bandeja
from .gui import mostrar_configuracoes
from .lang import tr
from .notifications import notificador

def foi_iniciado_pelo_atalho_minimizado():
    """
    Verifica se a variável de ambiente 'ANKI_TRAY_STARTUP' está presente.
    Esta variável é injetada exclusivamente pelo nosso wrapper VBS.
    Se ela existir (valor '1'), significa que o boot foi automático e deve minimizar.
    """
    flag_startup = os.environ.get("ANKI_TRAY_STARTUP")
    
    if flag_startup == "1":
        return True
    
    return False

def ao_carregar_perfil():
    """
    Executado assim que o perfil do usuário é carregado.
    """
    # Verifica o tipo de inicialização
    iniciado_minimizado = foi_iniciado_pelo_atalho_minimizado()

    # 1. Configura a notificação inicial (passando se foi boot auto ou manual)
    notificador.verificar_inicializacao(iniciado_minimizado)

    # 2. Se for boot automático, minimiza para a bandeja
    if iniciado_minimizado:
        gerenciador_bandeja.esconder_para_bandeja()

def configurar_menu():
    """Adiciona a opção de configuração no menu 'Ferramentas' do Anki."""
    acao = QAction(tr("nome_menu"), mw)
    acao.triggered.connect(mostrar_configuracoes)
    mw.form.menuTools.addAction(acao)
    
# --- Registro dos Ganchos ---

gui_hooks.profile_did_open.append(ao_carregar_perfil)
configurar_menu()