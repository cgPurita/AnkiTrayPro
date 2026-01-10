# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: __init__.py
# -------------------------------------------------------------------------
import os  # Importa módulo para interagir com o sistema operacional e variáveis de ambiente
from aqt import mw  # Importa a janela principal do Anki (MainWindow)
from aqt.qt import * # Importa componentes da interface gráfica Qt
from aqt import gui_hooks  # Importa o sistema de ganchos (hooks) do Anki para eventos

# Importações dos módulos locais do nosso projeto
from .tray import gerenciador_bandeja  # Importa o gerenciador da bandeja do sistema
from .gui import mostrar_configuracoes, StartupManager  # Importa a tela de config e o gerenciador de boot
from .lang import tr  # Importa a função de tradução
from .notifications import notificador  # Importa o gerenciador de notificações

def foi_iniciado_pelo_atalho_minimizado():
    """
    Verifica se a variável de ambiente 'ANKI_TRAY_STARTUP' está presente.
    Esta variável é injetada exclusivamente pelo nosso wrapper VBS (run_minimized.vbs).
    Se ela existir (valor '1'), significa que o boot foi automático pelo Windows e deve minimizar.
    """
    # Tenta obter o valor da variável de ambiente definida pelo script VBS
    flag_startup = os.environ.get("ANKI_TRAY_STARTUP")
    
    # Se a flag for igual a "1", confirmamos que foi um boot automático do nosso plugin
    if flag_startup == "1":
        return True
    
    # Caso contrário, foi uma abertura manual normal
    return False

def ao_carregar_perfil():
    """
    Executado assim que o perfil do usuário é carregado no Anki.
    Este é o momento ideal para decidir se escondemos a janela e mostramos notificações.
    """
    # Verifica se o Anki foi iniciado através do nosso atalho de inicialização automática
    iniciado_min = foi_iniciado_pelo_atalho_minimizado()

    # Se detectarmos que viemos do wrapper VBS (boot automático)
    if iniciado_min:
        # Chama o gerenciador de bandeja para esconder a janela principal imediatamente
        gerenciador_bandeja.esconder_para_bandeja()
        
        # --- CORREÇÃO AQUI ---
        # Chamamos explicitamente a verificação de inicialização do notificador.
        # Passamos 'True' para indicar que foi um boot minimizado, o que permite
        # que a notificação de "Boas-vindas / Resumo do dia" seja disparada.
        notificador.verificar_inicializacao(True)

def configurar_menu():
    """Adiciona a opção de configuração no menu 'Ferramentas' do Anki."""
    # Cria uma nova ação (item de menu) com o texto traduzido
    acao = QAction(tr("nome_menu"), mw)
    # Conecta o clique dessa ação à função que abre a janela de configurações
    acao.triggered.connect(mostrar_configuracoes)
    # Adiciona a ação ao menu 'Tools' (Ferramentas) da janela principal
    mw.form.menuTools.addAction(acao)
    
# --- Execução Imediata (Auto-Cura) ---
# O código abaixo roda no momento em que o Anki lê este arquivo (antes mesmo de abrir a janela).
try:
    # Verifica a integridade dos arquivos (se o run_minimized.vbs existe).
    # Se o usuário tiver deletado o VBS ou for a primeira instalação, ele é recriado aqui.
    StartupManager.verificar_integridade()
except:
    # Se houver erro na verificação (ex: falta de permissão), ignoramos para não travar o Anki
    pass

# --- Registro dos Ganchos ---

# Adiciona nossa função 'ao_carregar_perfil' à lista de funções que o Anki executa
# quando um perfil de usuário é carregado com sucesso.
gui_hooks.profile_did_open.append(ao_carregar_perfil)

# Configura o menu de ferramentas para que o usuário possa acessar as opções
configurar_menu()