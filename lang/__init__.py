# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: lang/__init__.py
# -------------------------------------------------------------------------
import importlib
from aqt import mw

_traducoes_atuais = {}

def carregar_traducoes():
    global _traducoes_atuais
    if _traducoes_atuais:
        return

    # Obtém o idioma da interface (ex: 'pt_BR', 'en_US', 'de')
    codigo_idioma = getattr(mw, "lang", "en")
    
    # Simplifica para as duas primeiras letras (ex: 'pt', 'en', 'de')
    idioma_curto = codigo_idioma[:2].lower()

    try:
        # Tenta carregar o arquivo com o nome do idioma (ex: pt.py)
        # Se você criar um arquivo es.py ou fr.py no futuro, funcionará automaticamente.
        modulo = importlib.import_module(f".{idioma_curto}", package=__name__)
        _traducoes_atuais = modulo.traducoes
    except ImportError:
        # Se o arquivo do idioma não existir, usa o inglês como fallback padrão
        try:
            modulo = importlib.import_module(".en", package=__name__)
            _traducoes_atuais = modulo.traducoes
        except:
            _traducoes_atuais = {}

def tr(chave):
    if not _traducoes_atuais:
        carregar_traducoes()
    return _traducoes_atuais.get(chave, f"[{chave}]")