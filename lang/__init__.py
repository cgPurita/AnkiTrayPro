# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: lang/__init__.py
# -------------------------------------------------------------------------
import importlib
from aqt import mw  # Importa a janela principal do Anki para acessar configurações

# Variável global para armazenar as traduções carregadas na memória.
# Funciona como um "cache" para não ler arquivos toda vez.
_traducoes_atuais = {}

def carregar_traducoes():
    """
    Descobre o idioma do Anki e carrega o arquivo de tradução correspondente 
    (pt.py, en.py etc.) para a memória.
    """
    global _traducoes_atuais
    
    # Se o dicionário já estiver preenchido, não precisamos fazer nada (retorna).
    if _traducoes_atuais:
        return

    # 1. Obtém o código de idioma configurado no Anki (ex: 'pt_BR', 'en_US', 'es_ES')
    # Se não encontrar, assume 'en' (inglês) como padrão.
    codigo_idioma = mw.pm.meta.get("defaultLang", "en")
    
    # 2. Pega apenas as duas primeiras letras para simplificar (ex: 'pt' de 'pt_BR')
    idioma_curto = codigo_idioma[:2]

    # 3. Tenta importar o módulo de tradução dinamicamente
    try:
        # Tenta carregar: .pt, .en, etc. dentro deste pacote (package=__name__)
        modulo = importlib.import_module(f".{idioma_curto}", package=__name__)
        
        # Se der certo, pega o dicionário 'traducoes' de dentro do arquivo
        _traducoes_atuais = modulo.traducoes
        
    except ImportError:
        # Se der erro (ex: o arquivo 'fr.py' não existe), usamos o Inglês como segurança (fallback)
        try:
            modulo = importlib.import_module(".en", package=__name__)
            _traducoes_atuais = modulo.traducoes
        except ImportError:
            # Caso extremo: nem o arquivo en.py existe. Deixamos vazio.
            _traducoes_atuais = {}

def tr(chave):
    """
    Função principal de tradução.
    Recebe uma 'chave' (string) e retorna o texto traduzido.
    """
    # Garante que as traduções foram carregadas antes de procurar
    if not _traducoes_atuais:
        carregar_traducoes()
    
    # Tenta buscar a chave no dicionário. 
    # Se não achar, retorna a própria chave entre colchetes para alertar que falta tradução.
    return _traducoes_atuais.get(chave, f"[{chave}]")