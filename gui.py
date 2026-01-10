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
    Utiliza um Wrapper VBS para garantir a minimização correta no boot.
    """
    
    SHORTCUT_NAME = "AnkiTrayPro_AutoStart.lnk"
    VBS_NAME = "run_minimized.vbs"

    @staticmethod
    def _obter_pasta_startup_real():
        """
        Descobre a pasta de inicialização real do usuário via Registro.
        """
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
    def _obter_executavel_anki():
        """
        Define qual .exe o atalho vai abrir.
        Prioridade: 1. Pastas Padrão -> 2. Registro -> 3. Processo Atual
        """
        caminho_atual = os.path.abspath(sys.executable)
        
        # 1. Pastas Padrão (Prioridade Máxima)
        locais = []
        if os.getenv('LOCALAPPDATA'):
            locais.append(os.path.join(os.getenv('LOCALAPPDATA'), r"Programs\Anki\anki.exe"))
        if os.getenv('ProgramFiles'):
            locais.append(os.path.join(os.getenv('ProgramFiles'), r"Anki\anki.exe"))
        if os.getenv('ProgramFiles(x86)'):
            locais.append(os.path.join(os.getenv('ProgramFiles(x86)'), r"Anki\anki.exe"))

        for path in locais:
            if os.path.exists(path):
                return path

        # 2. Registro (Fallback secundário)
        try:
            chave = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Anki"
            for hkey in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
                try:
                    with winreg.OpenKey(hkey, chave) as key:
                        pasta, _ = winreg.QueryValueEx(key, "InstallLocation")
                        exe = os.path.join(pasta, "anki.exe")
                        if os.path.exists(exe):
                            return exe
                except: pass
        except: pass

        # 3. Fallback final
        return caminho_atual

    @staticmethod
    def _gerar_script_wrapper(caminho_anki):
        """
        Cria o script VBS intermediário que injeta a variável de ambiente.
        """
        try:
            base_dir = os.path.dirname(__file__)
            vbs_path = os.path.join(base_dir, StartupManager.VBS_NAME)
            
            conteudo_vbs = f"""
            Set oShell = CreateObject("WScript.Shell")
            oShell.Environment("PROCESS")("ANKI_TRAY_STARTUP") = "1"
            oShell.Run "{caminho_anki}", 1, False
            """
            
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(conteudo_vbs)
            
            return vbs_path
        except Exception as e:
            raise e

    @staticmethod
    def criar_atalho(caminho_exe, caminho_link, iniciar_minimizado):
        try:
            pasta_link = os.path.dirname(caminho_link)
            if not os.path.exists(pasta_link):
                os.makedirs(pasta_link)

            # Se o usuário quer iniciar minimizado, usamos o WRAPPER VBS
            if iniciar_minimizado:
                alvo_final = StartupManager._gerar_script_wrapper(caminho_exe)
                
                target = os.path.join(os.getenv('SystemRoot'), "System32", "wscript.exe")
                # Aspas duplas escapadas para o VBScript aceitar o caminho com espaços
                args = f'""{alvo_final}""'
                icon = caminho_exe 
                desc = "Anki Tray Pro (Minimizado)"
                window_style = 7 
            else:
                # Modo normal: atalho direto
                target = caminho_exe
                args = "" if "python" not in os.path.basename(caminho_exe).lower() else "-m aqt"
                icon = target
                desc = "Iniciado automaticamente pelo Anki Tray Pro"
                window_style = 1

            script_gen = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            Set oLink = oWS.CreateShortcut("{caminho_link}")
            oLink.TargetPath = "{target}"
            oLink.Arguments = "{args}"
            oLink.IconLocation = "{icon},0"
            oLink.WindowStyle = {window_style}
            oLink.Description = "{desc}"
            oLink.Save
            """
            
            gen_path = os.path.join(os.getenv('TEMP'), "anki_shortcut_gen.vbs")
            with open(gen_path, "w", encoding="utf-8") as file:
                file.write(script_gen)
            
            cscript = os.path.join(os.getenv('SystemRoot'), "System32", "cscript.exe")
            # Executa sem janela
            subprocess.run([cscript, '//Nologo', gen_path], check=True, creationflags=0x08000000)
            
            if os.path.exists(gen_path):
                os.remove(gen_path)

        except Exception as e:
            raise e

    @staticmethod
    def definir_inicio(ativar, iniciar_minimizado):
        try:
            caminho_atalho = StartupManager._obter_caminho_atalho()
            
            if ativar:
                exe_alvo = StartupManager._obter_executavel_anki()
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

        grupo_sinc = QGroupBox(tr("grupo_sinc"))
        layout_sinc = QVBoxLayout()
        self.check_sincronizar = QCheckBox(tr("chk_sincronizar"))
        self.check_sincronizar.setChecked(self.configuracao.get("sincronizar_na_bandeja"))
        layout_sinc.addWidget(self.check_sincronizar)
        grupo_sinc.setLayout(layout_sinc)
        layout_principal.addWidget(grupo_sinc)

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
        
        StartupManager.definir_inicio(
            self.check_iniciar_sistema.isChecked(),
            self.check_iniciar_min.isChecked()
        )
        
        notificador.iniciar_temporizador()
        self.accept()

def mostrar_configuracoes():
    dialogo = DialogoConfiguracoes()
    dialogo.exec()