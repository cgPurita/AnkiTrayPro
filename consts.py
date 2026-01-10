# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: consts.py
# -------------------------------------------------------------------------

# --- Definição das Ações Possíveis (Constantes) ---
# Estas constantes são usadas para decidir o que o programa fará 
# ao fechar ou minimizar a janela.

# Ação: Enviar para a bandeja do sistema (perto do relógio)
ACAO_BANDEJA = "tray"

# Ação: Encerrar o aplicativo completamente
ACAO_SAIR = "quit"

# Ação: Comportamento padrão (ficar na barra de tarefas ou fechar normal)
ACAO_PADRAO = "standard"

# --- Textos e Títulos da Aplicação ---

# Nome oficial que aparecerá nos menus e janelas
NOME_APP = "Anki Tray Pro"

# Texto que aparece quando passamos o mouse sobre o ícone na bandeja
DICA_BANDEJA = "O Anki está rodando em segundo plano"

# Modelo de mensagem para quando houver cartões (o {} será substituído pelo número)
MSG_NAO_LIDA = "Você tem {} cartões para revisar!"