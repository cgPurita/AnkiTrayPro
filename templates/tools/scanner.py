# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# -------------------------------------------------------------------------
import os
from pathlib import Path
import datetime

# Configuração: Pastas e arquivos para IGNORAR
IGNORE_DIRS = {
    '.git', '.idea', '__pycache__', 'venv', 'env', 'node_modules', 
    'dist', 'build', '.vscode', '.DS_Store', '.gradle', '.navigation', 
    'captures', '.cxx', '.externalNativeBuild', 'google-services.json',
    '.dart_tool', '.pub', 'android', 'ios', 'web', 'linux', 'macos', 'windows' # Adicionado pastas de build flutter
}
IGNORE_FILES = {
    'package-lock.json', 'yarn.lock', '.DS_Store', 
    'resumo.txt', 'resumo_projeto.txt', 'scanner.py',  # Ignora a si mesmo
    'scanner.exe', 'db.sqlite3', 'pubspec.lock'
}
IGNORE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', 
    '.exe', '.dll', '.so', '.dylib', '.zip', '.tar', '.gz', '.pyc',
    '.jar', '.apk', '.aab', '.ttf', '.otf'
}

def is_text_file(filename):
    """Verifica se o arquivo é provavelmente texto baseado na extensão."""
    return not any(filename.lower().endswith(ext) for ext in IGNORE_EXTENSIONS)

def generate_context_file():
    # 1. Identifica onde o script está (templates/tools/)
    script_path = Path(__file__).resolve()
    
    # 2. Define onde salvar (na mesma pasta do script - LEI 44)
    output_filename = script_path.parent / "resumo_projeto.txt"
    
    # 3. Define a RAIZ DO PROJETO (Sobe 2 níveis: tools -> templates -> RAIZ)
    # Se o script estiver na raiz, isso não quebra, ele só sobe se der.
    # Ajuste: Assumindo que está em templates/tools, precisamos de 2 parents.
    project_root = script_path.parent.parent.parent
    
    # Fallback de segurança: Se subir demais e sair do projeto, usa o parent simples
    if not (project_root / 'pubspec.yaml').exists():
         # Tenta achar onde está o pubspec.yaml
         if (script_path.parent / 'pubspec.yaml').exists():
             project_root = script_path.parent
    
    print(f"Iniciando Scanner...")
    print(f"Script em: {script_path.parent}")
    print(f"Lendo Projeto em: {project_root}")
    print(f"Salvando Resumo em: {output_filename}")

    with open(output_filename, 'w', encoding='utf-8') as outfile:
        # A. Cabeçalho
        outfile.write(f"=== RAIO-X DO PROJETO: {project_root.name} ===\n")
        outfile.write(f"Gerado em: {datetime.datetime.now()}\n")
        outfile.write(f"Copyright © 2025 Caio Graco Purita\n")
        outfile.write("="*50 + "\n\n")

        # B. Estrutura de Pastas (Tree)
        outfile.write("--- ESTRUTURA DE ARQUIVOS ---\n")
        for root, dirs, files in os.walk(project_root):
            # Filtra pastas ignoradas
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            level = root.replace(str(project_root), '').count(os.sep)
            indent = ' ' * 4 * (level)
            outfile.write(f"{indent}[{os.path.basename(root)}/]\n")
            
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if f not in IGNORE_FILES and is_text_file(f):
                    outfile.write(f"{subindent}{f}\n")
        
        outfile.write("\n" + "="*50 + "\n\n")

        # C. Conteúdo dos Arquivos
        outfile.write("--- CONTEÚDO DOS ARQUIVOS ---\n\n")
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for filename in files:
                if filename in IGNORE_FILES:
                    continue
                
                if not is_text_file(filename):
                    continue
                
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, project_root)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        
                    outfile.write(f"FILE: {relative_path}\n")
                    outfile.write("-" * 20 + "\n")
                    outfile.write(content)
                    outfile.write("\n" + "=" * 50 + "\n\n")
                    print(f"Lendo: {relative_path}")
                    
                except Exception as e:
                    outfile.write(f"FILE: {relative_path} [ERRO AO LER: {str(e)}]\n")
                    outfile.write("\n" + "=" * 50 + "\n\n")

    print(f"\nSucesso! Resumo salvo em: {output_filename}")

if __name__ == "__main__":
    generate_context_file()