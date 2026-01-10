# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: __init__.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from aqt import gui_hooks # Ganchos do Anki (hooks)

# Importa nossos módulos (note que as variáveis agora estão em português)
from .tray import gerenciador_bandeja
from .gui import mostrar_configuracoes
from .lang import tr
from .notifications import notificador

def ao_carregar_perfil():
    """
    Executado assim que o perfil do usuário é carregado.
    Verifica se o usuário configurou para iniciar o Anki escondido.
    """
    configuracao = mw.addonManager.getConfig(__name__)
    
    if configuracao.get("iniciar_minimizado"):
        gerenciador_bandeja.esconder_para_bandeja()

def configurar_menu():
    """Adiciona a opção de configuração no menu 'Ferramentas' do Anki."""
    
    # Cria a ação no menu com o texto traduzido
    acao = QAction(tr("nome_menu"), mw)

        # Conecta o clique à função que abre a janela
    acao.triggered.connect(mostrar_configuracoes)

        # Adiciona a ação ao menu Tools (Ferramentas) da janela principal
    mw.form.menuTools.addAction(acao)
    
# --- Registro dos Ganchos (Start) ---

# Adiciona nossa função à lista de coisas a fazer quando o perfil abrir
gui_hooks.profile_did_open.append(ao_carregar_perfil)

# Configura o menu imediatamente
configurar_menu()