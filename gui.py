# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: gui.py
# -------------------------------------------------------------------------
import sys
import os
import winreg  # Módulo para interação com o Registro do Windows
from aqt import mw
from aqt.qt import *
from .lang import tr
from .consts import *
from .notifications import notificador

class StartupManager:
    """
    Classe utilitária responsável por gerenciar a entrada do aplicativo
    no Registro do Windows, permitindo a inicialização automática com o sistema.
    """
    
    # Define o caminho da chave de registro para execução automática no usuário atual
    KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    # Define o nome interno da chave para nossa aplicação
    APP_NAME = "AnkiTrayPro_Launcher"

    @staticmethod
    def esta_no_inicio():
        """
        Verifica se a chave de registro do aplicativo já existe.
        Retorna True se estiver configurado para iniciar, False caso contrário.
        """
        try:
            # Tenta abrir a chave de registro em modo somente leitura
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, StartupManager.KEY_PATH, 0, winreg.KEY_READ)
            # Tenta ler o valor associado ao nome do aplicativo
            winreg.QueryValueEx(key, StartupManager.APP_NAME)
            # Fecha a chave após a leitura
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            # Retorna False se a chave ou valor não existirem
            return False
        except Exception:
            # Retorna False em caso de outros erros de permissão ou acesso
            return False

    @staticmethod
    def definir_inicio(ativar):
        """
        Cria ou remove a entrada no registro do Windows conforme o parâmetro 'ativar'.
        """
        try:
            # Abre a chave de registro com permissão total de acesso (leitura e escrita)
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, StartupManager.KEY_PATH, 0, winreg.KEY_ALL_ACCESS)
            
            if ativar:
                # Se deve ativar, obtém o caminho do executável Python/Anki atual
                exe_path = f'"{sys.executable}"'
                # Grava o valor no registro como uma string (REG_SZ)
                winreg.SetValueEx(key, StartupManager.APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                # Se deve desativar, tenta excluir o valor do registro
                try:
                    winreg.DeleteValue(key, StartupManager.APP_NAME)
                except FileNotFoundError:
                    # Se o valor já não existe, ignora o erro
                    pass
            
            # Fecha a chave de registro para efetivar as alterações
            winreg.CloseKey(key)
        except Exception as e:
            # Em caso de erro, imprime no console (útil para debug)
            print(f"Erro ao configurar registro: {e}")

class DialogoConfiguracoes(QDialog):
    """
    Janela de diálogo para configuração das preferências do usuário.
    """
    
    def __init__(self):
        # Inicializa a classe base QDialog, definindo a janela principal como pai
        super().__init__(mw)
        # Define o título da janela usando a tradução
        self.setWindowTitle(tr("nome_menu"))
        
        # Carrega as configurações atuais do arquivo JSON
        self.configuracao = mw.addonManager.getConfig(__name__)
        
        # Constrói e organiza os widgets da interface
        self.configurar_interface()

    def configurar_interface(self):
        """
        Cria os grupos, layouts e controles da interface gráfica.
        """
        # Layout vertical principal que conterá todos os grupos
        layout_principal = QVBoxLayout()

        # --- Grupo: Comportamento da Janela ---
        grupo_comportamento = QGroupBox(tr("grupo_comportamento"))
        formulario_comp = QFormLayout()

        # Cria combobox para a ação de fechar
        self.combo_fechar = QComboBox()
        self.combo_fechar.addItem(tr("opcao_bandeja"), ACAO_BANDEJA)
        self.combo_fechar.addItem(tr("opcao_sair"), ACAO_SAIR)
        
        # Define o item selecionado com base na configuração salva
        indice_atual = self.combo_fechar.findData(self.configuracao.get("acao_ao_fechar"))
        self.combo_fechar.setCurrentIndex(indice_atual)

        # NOTA: A opção de configurar o botão minimizar (-) foi removida.
        # O comportamento agora é sempre padrão do sistema.

        # Adiciona as linhas ao layout de formulário
        formulario_comp.addRow(tr("lbl_fechar"), self.combo_fechar)
        
        # Define o layout do grupo
        grupo_comportamento.setLayout(formulario_comp)
        layout_principal.addWidget(grupo_comportamento)

        # --- Grupo: Sincronização ---
        grupo_sinc = QGroupBox(tr("grupo_sinc"))
        layout_sinc = QVBoxLayout()
        
        # Checkbox para sincronização
        self.check_sincronizar = QCheckBox(tr("chk_sincronizar"))
        self.check_sincronizar.setChecked(self.configuracao.get("sincronizar_na_bandeja"))
        
        layout_sinc.addWidget(self.check_sincronizar)
        grupo_sinc.setLayout(layout_sinc)
        layout_principal.addWidget(grupo_sinc)

        # --- Grupo: Inicialização ---
        grupo_inicio = QGroupBox(tr("grupo_inicio"))
        layout_inicio = QVBoxLayout()
        
        # Checkbox: Iniciar com o Windows
        # O estado inicial é verificado diretamente no registro do sistema
        self.check_iniciar_sistema = QCheckBox(tr("chk_iniciar_sistema"))
        self.check_iniciar_sistema.setChecked(StartupManager.esta_no_inicio())
        
        # Checkbox: Iniciar minimizado
        # O estado inicial vem do arquivo de configuração
        self.check_iniciar_min = QCheckBox(tr("chk_inicio_min"))
        self.check_iniciar_min.setChecked(self.configuracao.get("iniciar_minimizado"))
        
        # Define a dependência: só permite marcar "Iniciar Minimizado" se "Iniciar com Windows" estiver ativo
        self.check_iniciar_min.setEnabled(self.check_iniciar_sistema.isChecked())
        
        # Conecta o sinal de mudança do primeiro checkbox ao método de controle
        self.check_iniciar_sistema.toggled.connect(self.ao_alternar_inicio_sistema)
        
        # Adiciona os checkboxes ao layout
        layout_inicio.addWidget(self.check_iniciar_sistema)
        layout_inicio.addWidget(self.check_iniciar_min)
        grupo_inicio.setLayout(layout_inicio)
        layout_principal.addWidget(grupo_inicio)

        # --- Grupo: Notificações ---
        grupo_notificacao = QGroupBox(tr("grupo_notificacao"))
        formulario_notificacao = QFormLayout()
        
        # Checkbox para ativar notificações
        self.check_ativar_notif = QCheckBox(tr("chk_ativar_notif"))
        self.check_ativar_notif.setChecked(self.configuracao.get("notificacoes_ativadas"))
        
        # Campo numérico para o intervalo (1 a 1440 minutos)
        self.spin_intervalo = QSpinBox()
        self.spin_intervalo.setRange(1, 1440)
        self.spin_intervalo.setValue(self.configuracao.get("intervalo_notificacao"))
        
        formulario_notificacao.addRow(self.check_ativar_notif)
        formulario_notificacao.addRow(tr("lbl_intervalo"), self.spin_intervalo)
        grupo_notificacao.setLayout(formulario_notificacao)
        layout_principal.addWidget(grupo_notificacao)

        # --- Botões de Confirmação ---
        # Cria a caixa de botões padrão (OK e Cancelar)
        botoes = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        caixa_botoes = QDialogButtonBox(botoes)
        
        # Conecta os botões aos métodos aceitar e rejeitar
        caixa_botoes.accepted.connect(self.ao_clicar_ok)
        caixa_botoes.rejected.connect(self.reject)
        layout_principal.addWidget(caixa_botoes)

        # Define o layout principal na janela
        self.setLayout(layout_principal)

    def ao_alternar_inicio_sistema(self, marcado):
        """
        Executado quando o usuário altera o checkbox 'Iniciar com Windows'.
        Habilita ou desabilita o checkbox dependente 'Iniciar Minimizado'.
        """
        # Habilita ou desabilita o segundo checkbox
        self.check_iniciar_min.setEnabled(marcado)
        
        # Se o usuário desmarcar o início com o sistema, desmarca automaticamente o início minimizado
        if not marcado:
            self.check_iniciar_min.setChecked(False)

    def ao_clicar_ok(self):
        """
        Executado ao clicar em OK. Salva todas as configurações e fecha a janela.
        """
        
        # Atualiza o dicionário de configuração com os dados dos widgets
        self.configuracao["acao_ao_fechar"] = self.combo_fechar.currentData()
        # NOTA: Não salvamos mais "acao_ao_minimizar" pois a opção foi removida
        
        self.configuracao["sincronizar_na_bandeja"] = self.check_sincronizar.isChecked()
        self.configuracao["iniciar_minimizado"] = self.check_iniciar_min.isChecked()
        self.configuracao["notificacoes_ativadas"] = self.check_ativar_notif.isChecked()
        self.configuracao["intervalo_notificacao"] = self.spin_intervalo.value()

        # Escreve as configurações no arquivo JSON do addon
        mw.addonManager.writeConfig(__name__, self.configuracao)
        
        # Chama o gerenciador para aplicar a alteração no Registro do Windows
        StartupManager.definir_inicio(self.check_iniciar_sistema.isChecked())

        # Reinicia o temporizador de notificações para refletir possíveis mudanças de intervalo
        notificador.iniciar_temporizador()
        
        # Fecha a janela de diálogo com resultado positivo
        self.accept()

def mostrar_configuracoes():
    """
    Função auxiliar para instanciar e exibir a janela de configurações.
    """
    dialogo = DialogoConfiguracoes()
    dialogo.exec()