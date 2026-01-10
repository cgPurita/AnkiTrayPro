# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: gui.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from .lang import tr
from .consts import *
from .notifications import notificador

class DialogoConfiguracoes(QDialog):
    """
    Janela de opções acessível pelo menu Ferramentas.
    Gerencia a interface gráfica para alteração das preferências do usuário.
    """
    
    def __init__(self):
        # Inicializa a janela herdando as propriedades do Anki (mw)
        super().__init__(mw)
        self.setWindowTitle(tr("nome_menu"))
        
        # Carrega a configuração atual para a memória
        self.configuracao = mw.addonManager.getConfig(__name__)
        
        # Constrói os elementos visuais
        self.configurar_interface()

    def configurar_interface(self):
        """Monta o layout, cria os grupos, dropdowns e botões."""
        layout_principal = QVBoxLayout()

        # --- Grupo: Comportamento ---
        grupo_comportamento = QGroupBox(tr("grupo_comportamento"))
        formulario_comp = QFormLayout()

        # Dropdown para Ação ao Fechar (Botão X)
        self.combo_fechar = QComboBox()
        self.combo_fechar.addItem(tr("opcao_bandeja"), ACAO_BANDEJA)
        self.combo_fechar.addItem(tr("opcao_sair"), ACAO_SAIR)
        
        # Define a seleção atual baseada na config salva
        indice_atual = self.combo_fechar.findData(self.configuracao.get("acao_ao_fechar"))
        self.combo_fechar.setCurrentIndex(indice_atual)

        # Dropdown para Ação ao Minimizar (Botão _)
        self.combo_minimizar = QComboBox()
        self.combo_minimizar.addItem(tr("opcao_bandeja"), ACAO_BANDEJA)
        self.combo_minimizar.addItem(tr("opcao_padrao"), ACAO_PADRAO)
        
        # Define a seleção atual
        indice_min = self.combo_minimizar.findData(self.configuracao.get("acao_ao_minimizar"))
        self.combo_minimizar.setCurrentIndex(indice_min)

        # Adiciona os campos ao formulário
        formulario_comp.addRow(tr("lbl_fechar"), self.combo_fechar)
        formulario_comp.addRow(tr("lbl_minimizar"), self.combo_minimizar)
        grupo_comportamento.setLayout(formulario_comp)
        
        layout_principal.addWidget(grupo_comportamento)

        # --- Grupo: Sincronização ---
        grupo_sinc = QGroupBox(tr("grupo_sinc"))
        layout_sinc = QVBoxLayout()
        
        # Checkbox para habilitar sincronização ao minimizar
        self.check_sincronizar = QCheckBox(tr("chk_sincronizar"))
        self.check_sincronizar.setChecked(self.configuracao.get("sincronizar_na_bandeja"))
        
        layout_sinc.addWidget(self.check_sincronizar)
        grupo_sinc.setLayout(layout_sinc)
        layout_principal.addWidget(grupo_sinc)

        # --- Grupo: Inicialização ---
        grupo_inicio = QGroupBox(tr("grupo_inicio"))
        layout_inicio = QVBoxLayout()
        
        # Checkbox para iniciar minimizado
        self.check_iniciar_min = QCheckBox(tr("chk_inicio_min"))
        self.check_iniciar_min.setChecked(self.configuracao.get("iniciar_minimizado"))
        
        layout_inicio.addWidget(self.check_iniciar_min)
        grupo_inicio.setLayout(layout_inicio)
        layout_principal.addWidget(grupo_inicio)

        # --- Grupo: Notificações ---
        grupo_notificacao = QGroupBox(tr("grupo_notificacao"))
        formulario_notificacao = QFormLayout()
        
        # Checkbox global de notificações
        self.check_ativar_notif = QCheckBox(tr("chk_ativar_notif"))
        self.check_ativar_notif.setChecked(self.configuracao.get("notificacoes_ativadas"))
        
        # Campo numérico para o intervalo em minutos
        self.spin_intervalo = QSpinBox()
        self.spin_intervalo.setRange(1, 1440) # Limita entre 1 min e 24h
        self.spin_intervalo.setValue(self.configuracao.get("intervalo_notificacao"))
        
        formulario_notificacao.addRow(self.check_ativar_notif)
        formulario_notificacao.addRow(tr("lbl_intervalo"), self.spin_intervalo)
        grupo_notificacao.setLayout(formulario_notificacao)
        layout_principal.addWidget(grupo_notificacao)

        # --- Botões de Ação ---
        # Define os botões padrão de OK e Cancelar
        botoes = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        caixa_botoes = QDialogButtonBox(botoes)
        
        # Conecta os sinais de clique aos métodos da classe
        caixa_botoes.accepted.connect(self.ao_clicar_ok)
        caixa_botoes.rejected.connect(self.reject)
        layout_principal.addWidget(caixa_botoes)

        self.setLayout(layout_principal)

    def ao_clicar_ok(self):
        """Salva as alterações e fecha a janela."""
        
        # Atualiza o dicionário de configuração com os valores da interface
        self.configuracao["acao_ao_fechar"] = self.combo_fechar.currentData()
        self.configuracao["acao_ao_minimizar"] = self.combo_minimizar.currentData()
        self.configuracao["sincronizar_na_bandeja"] = self.check_sincronizar.isChecked()
        self.configuracao["iniciar_minimizado"] = self.check_iniciar_min.isChecked()
        self.configuracao["notificacoes_ativadas"] = self.check_ativar_notif.isChecked()
        self.configuracao["intervalo_notificacao"] = self.spin_intervalo.value()

        # Persiste os dados no disco
        mw.addonManager.writeConfig(__name__, self.configuracao)
        
        # Reinicia o serviço de notificação para aplicar o novo intervalo imediatamente
        notificador.iniciar_temporizador()
        
        # Fecha o diálogo retornando sucesso
        self.accept()

def mostrar_configuracoes():
    """Instancia e exibe a janela de configurações de forma modal."""
    dialogo = DialogoConfiguracoes()
    dialogo.exec()