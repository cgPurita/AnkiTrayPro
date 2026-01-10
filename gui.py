# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: gui.py
# -------------------------------------------------------------------------
import sys
import os
import subprocess
import winreg
from aqt import mw
from aqt.qt import *
from aqt.utils import showWarning
from .lang import tr
from .consts import *
from .notifications import notificador

class StartupManager:
    """
    Gerencia a criação do atalho na pasta de inicialização do Windows.
    Configura o atalho para iniciar minimizado ou normal, dependendo da escolha do usuário.
    """
    
    SHORTCUT_NAME = "AnkiTrayPro_AutoStart.lnk"

    @staticmethod
    def _obter_pasta_startup_real():
        try:
            chave_shell = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chave_shell) as key:
                caminho_bruto, tipo = winreg.QueryValueEx(key, "Startup")
                return os.path.expandvars(caminho_bruto)
        except:
            return os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')

    @staticmethod
    def _obter_caminho_atalho():
        return os.path.join(StartupManager._obter_pasta_startup_real(), StartupManager.SHORTCUT_NAME)

    @staticmethod
    def esta_no_inicio():
        return os.path.exists(StartupManager._obter_caminho_atalho())

    @staticmethod
    def _buscar_caminho_registro():
        caminhos_registro = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Anki"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Anki"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Anki")
        ]
        for hkey, subkey in caminhos_registro:
            try:
                with winreg.OpenKey(hkey, subkey) as chave_aberta:
                    pasta_instalacao, _ = winreg.QueryValueEx(chave_aberta, "InstallLocation")
                    caminho_exe = os.path.join(pasta_instalacao, "anki.exe")
                    if os.path.exists(caminho_exe):
                        return caminho_exe
            except:
                continue
        return None

    @staticmethod
    def _obter_executavel_anki():
        caminho_atual = os.path.abspath(sys.executable)
        if "python" not in os.path.basename(caminho_atual).lower():
            return caminho_atual
        
        caminho_registro = StartupManager._buscar_caminho_registro()
        if caminho_registro:
            return caminho_registro

        return caminho_atual

    @staticmethod
    def criar_atalho(caminho_exe, caminho_link, minimizado=False):
        """
        Cria o atalho. Se 'minimizado' for True, define WindowStyle=7 (Minimizado).
        Caso contrário, WindowStyle=1 (Normal).
        """
        try:
            pasta_link = os.path.dirname(caminho_link)
            if not os.path.exists(pasta_link):
                os.makedirs(pasta_link)

            args = ""
            if "python" in os.path.basename(caminho_exe).lower():
                args = "-m aqt"

            # Define o estilo da janela: 7 = Minimizado, 1 = Normal
            estilo_janela = 7 if minimizado else 1

            script_vbs = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{caminho_link}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{caminho_exe}"
            oLink.Arguments = "{args}"
            oLink.WorkingDirectory = "{os.path.dirname(caminho_exe)}"
            oLink.WindowStyle = {estilo_janela}
            oLink.Description = "Iniciado automaticamente pelo Anki Tray Pro"
            oLink.Save
            """
            
            caminho_vbs = os.path.join(os.getenv('TEMP'), "anki_shortcut_gen.vbs")
            with open(caminho_vbs, "w", encoding="utf-8") as file:
                file.write(script_vbs)
            
            cscript_path = os.path.join(os.getenv('SystemRoot'), "System32", "cscript.exe")
            CREATE_NO_WINDOW = 0x08000000
            subprocess.run([cscript_path, '//Nologo', caminho_vbs], check=True, creationflags=CREATE_NO_WINDOW)
            
            if os.path.exists(caminho_vbs):
                os.remove(caminho_vbs)
                
        except Exception as e:
            raise e

    @staticmethod
    def definir_inicio(ativar, iniciar_minimizado):
        try:
            caminho_atalho = StartupManager._obter_caminho_atalho()
            
            if ativar:
                exe_alvo = StartupManager._obter_executavel_anki()
                # Passa a preferência de minimizar para a criação do atalho
                StartupManager.criar_atalho(exe_alvo, caminho_atalho, iniciar_minimizado)
            else:
                if os.path.exists(caminho_atalho):
                    os.remove(caminho_atalho)
                    
        except Exception as e:
            showWarning(f"Erro ao configurar inicialização:\n{str(e)}")

class DialogoConfiguracoes(QDialog):
    def __init__(self):
        super().__init__(mw)
        self.setWindowTitle(tr("nome_menu"))
        self.configuracao = mw.addonManager.getConfig(__name__)
        self.configurar_interface()

    def configurar_interface(self):
        layout_principal = QVBoxLayout()
        
        # Grupo Comportamento
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

        # Grupo Sincronização
        grupo_sinc = QGroupBox(tr("grupo_sinc"))
        layout_sinc = QVBoxLayout()
        self.check_sincronizar = QCheckBox(tr("chk_sincronizar"))
        self.check_sincronizar.setChecked(self.configuracao.get("sincronizar_na_bandeja"))
        layout_sinc.addWidget(self.check_sincronizar)
        grupo_sinc.setLayout(layout_sinc)
        layout_principal.addWidget(grupo_sinc)

        # Grupo Inicialização
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

        # Grupo Notificações
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
        self.configuracao["acao_ao_fechar"] = self.combo_fechar.currentData()
        self.configuracao["sincronizar_na_bandeja"] = self.check_sincronizar.isChecked()
        self.configuracao["iniciar_minimizado"] = self.check_iniciar_min.isChecked()
        self.configuracao["notificacoes_ativadas"] = self.check_ativar_notif.isChecked()
        self.configuracao["intervalo_notificacao"] = self.spin_intervalo.value()
        
        mw.addonManager.writeConfig(__name__, self.configuracao)
        
        # Passa os dois parâmetros: Se deve iniciar com o sistema E se deve ser minimizado
        StartupManager.definir_inicio(
            self.check_iniciar_sistema.isChecked(),
            self.check_iniciar_min.isChecked()
        )
        
        notificador.iniciar_temporizador()
        self.accept()

def mostrar_configuracoes():
    dialogo = DialogoConfiguracoes()
    dialogo.exec()