# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: gui.py
# -------------------------------------------------------------------------

# Importa módulos do sistema para manipulação de arquivos e caminhos
import sys
import os
# Importa módulo para execução de subprocessos (necessário para criar o atalho)
import subprocess
# Importa módulo para ler o Registro do Windows
import winreg

# Importa a janela principal do Anki
from aqt import mw
# Importa os componentes gráficos da biblioteca Qt
from aqt.qt import *
# Importa funções utilitárias para exibir alertas (apenas em caso de erro)
from aqt.utils import showWarning

# Importa a função de tradução interna
from .lang import tr
# Importa as constantes globais
from .consts import *
# Importa o gerenciador de notificações
from .notifications import notificador

# Classe responsável por gerenciar a inicialização automática do Anki
class StartupManager:
    """
    Gerencia a criação do atalho na pasta de inicialização do Windows.
    Detecta dinamicamente a pasta real (seja Startup, Dfapps ou OneDrive) via Registro.
    """
    
    # Define o nome do arquivo de atalho que será criado
    SHORTCUT_NAME = "AnkiTrayPro_AutoStart.lnk"

    # Método estático para localizar a pasta de inicialização verdadeira do usuário
    @staticmethod
    def _obter_pasta_startup_real():
        """
        Consulta o Registro do Windows para descobrir qual é a pasta 'Startup' VERDADEIRA
        deste usuário, ignorando caminhos fixos que podem estar errados.
        """
        try:
            # Caminho da chave onde o Windows guarda a localização das pastas especiais
            chave_shell = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            
            # Abre a chave do usuário atual (HKEY_CURRENT_USER)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chave_shell) as key:
                # O valor "Startup" contém o caminho real configurado no sistema
                caminho_bruto, tipo = winreg.QueryValueEx(key, "Startup")
                
                # O caminho pode vir com variáveis de ambiente (ex: %USERPROFILE%\...)
                # A função expandvars resolve isso para o caminho completo (C:\Users\Caio\...)
                caminho_final = os.path.expandvars(caminho_bruto)
                
                return caminho_final
        except Exception as e:
            # Fallback de emergência caso o registro falhe (muito raro)
            return os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')

    # Método estático para obter o caminho completo do arquivo .lnk
    @staticmethod
    def _obter_caminho_atalho():
        # Obtém a pasta real
        pasta_real = StartupManager._obter_pasta_startup_real()
        # Junta com o nome do arquivo
        return os.path.join(pasta_real, StartupManager.SHORTCUT_NAME)

    # Verifica se o atalho já existe no disco (usado para marcar o checkbox na interface)
    @staticmethod
    def esta_no_inicio():
        return os.path.exists(StartupManager._obter_caminho_atalho())

    # Método auxiliar para ler o Registro do Windows em busca do anki.exe
    @staticmethod
    def _buscar_caminho_registro():
        # Lista de chaves possíveis onde o Anki pode ter gravado a instalação
        caminhos_registro = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Anki"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Anki"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Anki")
        ]
        # Itera sobre as chaves
        for hkey, subkey in caminhos_registro:
            try:
                with winreg.OpenKey(hkey, subkey) as chave_aberta:
                    # Lê o valor "InstallLocation"
                    pasta_instalacao, _ = winreg.QueryValueEx(chave_aberta, "InstallLocation")
                    caminho_exe = os.path.join(pasta_instalacao, "anki.exe")
                    # Confirma se existe
                    if os.path.exists(caminho_exe):
                        return caminho_exe
            except:
                continue
        return None

    # Método Principal de Detecção do Executável
    @staticmethod
    def _obter_executavel_anki():
        """
        Define qual arquivo .exe o atalho deve abrir.
        """
        caminho_atual = os.path.abspath(sys.executable)
        
        # Se não for python, confiamos no executável atual
        if "python" not in os.path.basename(caminho_atual).lower():
            return caminho_atual
        
        # Se for Python (ambiente dev), tenta achar a instalação real no registro
        caminho_registro = StartupManager._buscar_caminho_registro()
        if caminho_registro:
            return caminho_registro

        # Se falhar, usa o python mesmo
        return caminho_atual

    # Criação do Atalho via VBScript
    @staticmethod
    def criar_atalho(caminho_exe, caminho_link):
        try:
            pasta_link = os.path.dirname(caminho_link)
            
            # Se a pasta detectada não existir (raro, mas possível), cria
            if not os.path.exists(pasta_link):
                os.makedirs(pasta_link)

            # Argumentos: Se cairmos no fallback do Python, precisamos de '-m aqt'
            args = ""
            if "python" in os.path.basename(caminho_exe).lower():
                args = "-m aqt"

            # Cria o script VBS para gerar o atalho
            script_vbs = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{caminho_link}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{caminho_exe}"
            oLink.Arguments = "{args}"
            oLink.WorkingDirectory = "{os.path.dirname(caminho_exe)}"
            oLink.WindowStyle = 1
            oLink.Description = "Iniciado automaticamente pelo Anki Tray Pro"
            oLink.Save
            """
            
            # Salva o script temporário
            caminho_vbs = os.path.join(os.getenv('TEMP'), "anki_shortcut_gen.vbs")
            with open(caminho_vbs, "w", encoding="utf-8") as file:
                file.write(script_vbs)
            
            # Executa o script
            cscript_path = os.path.join(os.getenv('SystemRoot'), "System32", "cscript.exe")
            CREATE_NO_WINDOW = 0x08000000
            subprocess.run([cscript_path, '//Nologo', caminho_vbs], check=True, creationflags=CREATE_NO_WINDOW)
            
            # Limpa o arquivo temporário
            if os.path.exists(caminho_vbs):
                os.remove(caminho_vbs)
                
        except Exception as e:
            # Repassa a exceção se der erro
            raise e

    # Método externo chamado pela GUI
    @staticmethod
    def definir_inicio(ativar):
        try:
            caminho_atalho = StartupManager._obter_caminho_atalho()
            
            if ativar:
                # Descobre o executável correto
                exe_alvo = StartupManager._obter_executavel_anki()
                # Cria o atalho
                StartupManager.criar_atalho(exe_alvo, caminho_atalho)
                
                # REMOVIDO: O showInfo que exibia a mensagem de sucesso foi retirado.
                # Agora a operação é silenciosa.
            else:
                # Remove o atalho se existir
                if os.path.exists(caminho_atalho):
                    os.remove(caminho_atalho)
                    
        except Exception as e:
            # Em caso de erro crítico, mostra um aviso visual
            showWarning(f"Erro ao configurar inicialização:\n{str(e)}")

# Janela de Configurações
class DialogoConfiguracoes(QDialog):
    """
    Interface gráfica para o usuário alterar as preferências do Add-on.
    """
    def __init__(self):
        super().__init__(mw)
        self.setWindowTitle(tr("nome_menu"))
        self.configuracao = mw.addonManager.getConfig(__name__)
        self.configurar_interface()

    def configurar_interface(self):
        layout_principal = QVBoxLayout()
        
        # Grupo: Comportamento
        grupo_comportamento = QGroupBox(tr("grupo_comportamento"))
        formulario_comp = QFormLayout()
        self.combo_fechar = QComboBox()
        self.combo_fechar.addItem(tr("opcao_bandeja"), ACAO_BANDEJA)
        self.combo_fechar.addItem(tr("opcao_sair"), ACAO_SAIR)
        indice_atual = self.combo_fechar.findData(self.configuracao.get("acao_ao_fechar"))
        self.combo_fechar.setCurrentIndex(indice_atual)
        formulario_comp.addRow(tr("lbl_fechar"), self.combo_fechar)
        grupo_comportamento.setLayout(formulario_comp)
        layout_principal.addWidget(grupo_comportamento)

        # Grupo: Sincronização
        grupo_sinc = QGroupBox(tr("grupo_sinc"))
        layout_sinc = QVBoxLayout()
        self.check_sincronizar = QCheckBox(tr("chk_sincronizar"))
        self.check_sincronizar.setChecked(self.configuracao.get("sincronizar_na_bandeja"))
        layout_sinc.addWidget(self.check_sincronizar)
        grupo_sinc.setLayout(layout_sinc)
        layout_principal.addWidget(grupo_sinc)

        # Grupo: Inicialização
        grupo_inicio = QGroupBox(tr("grupo_inicio"))
        layout_inicio = QVBoxLayout()
        self.check_iniciar_sistema = QCheckBox(tr("chk_iniciar_sistema"))
        self.check_iniciar_sistema.setChecked(StartupManager.esta_no_inicio())
        self.check_iniciar_min = QCheckBox(tr("chk_inicio_min"))
        self.check_iniciar_min.setChecked(self.configuracao.get("iniciar_minimizado"))
        self.check_iniciar_min.setEnabled(self.check_iniciar_sistema.isChecked())
        self.check_iniciar_sistema.toggled.connect(self.ao_alternar_inicio_sistema)
        layout_inicio.addWidget(self.check_iniciar_sistema)
        layout_inicio.addWidget(self.check_iniciar_min)
        grupo_inicio.setLayout(layout_inicio)
        layout_principal.addWidget(grupo_inicio)

        # Grupo: Notificações
        grupo_notificacao = QGroupBox(tr("grupo_notificacao"))
        formulario_notificacao = QFormLayout()
        self.check_ativar_notif = QCheckBox(tr("chk_ativar_notif"))
        self.check_ativar_notif.setChecked(self.configuracao.get("notificacoes_ativadas"))
        self.spin_intervalo = QSpinBox()
        self.spin_intervalo.setRange(1, 1440)
        self.spin_intervalo.setValue(self.configuracao.get("intervalo_notificacao"))
        formulario_notificacao.addRow(self.check_ativar_notif)
        formulario_notificacao.addRow(tr("lbl_intervalo"), self.spin_intervalo)
        grupo_notificacao.setLayout(formulario_notificacao)
        layout_principal.addWidget(grupo_notificacao)

        # Botões
        botoes = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        caixa_botoes = QDialogButtonBox(botoes)
        caixa_botoes.accepted.connect(self.ao_clicar_ok)
        caixa_botoes.rejected.connect(self.reject)
        layout_principal.addWidget(caixa_botoes)
        self.setLayout(layout_principal)

    def ao_alternar_inicio_sistema(self, marcado):
        self.check_iniciar_min.setEnabled(marcado)
        if not marcado:
            self.check_iniciar_min.setChecked(False)

    def ao_clicar_ok(self):
        # Atualiza configurações na memória
        self.configuracao["acao_ao_fechar"] = self.combo_fechar.currentData()
        self.configuracao["sincronizar_na_bandeja"] = self.check_sincronizar.isChecked()
        self.configuracao["iniciar_minimizado"] = self.check_iniciar_min.isChecked()
        self.configuracao["notificacoes_ativadas"] = self.check_ativar_notif.isChecked()
        self.configuracao["intervalo_notificacao"] = self.spin_intervalo.value()
        
        # Grava configurações no disco
        mw.addonManager.writeConfig(__name__, self.configuracao)
        
        # Chama a função de inicialização (agora silenciosa)
        StartupManager.definir_inicio(self.check_iniciar_sistema.isChecked())
        
        # Reinicia notificador
        notificador.iniciar_temporizador()
        self.accept()

def mostrar_configuracoes():
    dialogo = DialogoConfiguracoes()
    dialogo.exec()