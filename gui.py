# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: gui.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from .lang import tr  # Função de tradução
from .consts import * # Constantes (ACAO_BANDEJA, etc)
from .notifications import notificador # Para reiniciar o timer após salvar

class DialogoConfiguracoes(QDialog):
    """Janela de opções acessível pelo menu Ferramentas."""
    
    def __init__(self):
        super().__init__(mw) # Define a janela principal do Anki como "pai"
        self.setWindowTitle(tr("nome_menu"))
        
        # Carrega a configuração atual (cópia modificável)
        self.configuracao = mw.addonManager.getConfig(__name__)
        
        # Constrói os elementos visuais
        self.configurar_interface()

    def configurar_interface(self):
        """Monta o layout, botões e campos."""
        layout_principal = QVBoxLayout()

        # --- Grupo: Comportamento da Janela ---
        grupo_comportamento = QGroupBox(tr("grupo_comportamento"))
        formulario_comp = QFormLayout()

        # 1. Dropdown para Ação ao Fechar (Botão X)
        self.combo_fechar = QComboBox()
        # Adiciona item (Texto Visível, Valor Interno)
        self.combo_fechar.addItem(tr("opcao_bandeja"), ACAO_BANDEJA)
        self.combo_fechar.addItem(tr("opcao_sair"), ACAO_SAIR)
        
        # Encontra qual está salvo atualmente e seleciona
        indice_atual = self.combo_fechar.findData(self.configuracao.get("acao_ao_fechar"))
        self.combo_fechar.setCurrentIndex(indice_atual)

        # 2. Dropdown para Ação ao Minimizar (_)
        self.combo_minimizar = QComboBox()
        self.combo_minimizar.addItem(tr("opcao_bandeja"), ACAO_BANDEJA)
        self.combo_minimizar.addItem(tr("opcao_padrao"), ACAO_PADRAO)
        
        indice_min = self.combo_minimizar.findData(self.configuracao.get("acao_ao_minimizar"))
        self.combo_minimizar.setCurrentIndex(indice_min)

        # Adiciona as linhas ao formulário
        formulario_comp.addRow(tr("lbl_fechar"), self.combo_fechar)
        formulario_comp.addRow(tr("lbl_minimizar"), self.combo_minimizar)
        grupo_comportamento.setLayout(formulario_comp)
        
        layout_principal.addWidget(grupo_comportamento)

        # --- Grupo: Sincronização ---
        grupo_sinc = QGroupBox(tr("grupo_sinc"))
        layout_sinc = QVBoxLayout()
        
        self.check_sincronizar = QCheckBox(tr("chk_sincronizar"))
        self.check_sincronizar.setChecked(self.configuracao.get("sincronizar_na_bandeja"))
        
        layout_sinc.addWidget(self.check_sincronizar)
        grupo_sinc.setLayout(layout_sinc)
        layout_principal.addWidget(grupo_sinc)

        # --- Grupo: Inicialização ---
        grupo_inicio = QGroupBox(tr("grupo_inicio"))
        layout_inicio = QVBoxLayout()
        
        self.check_iniciar_min = QCheckBox(tr("chk_inicio_min"))
        self.check_iniciar_min.setChecked(self.configuracao.get("iniciar_minimizado"))
        
        layout_inicio.addWidget(self.check_iniciar_min)
        grupo_inicio.setLayout(layout_inicio)
        layout_principal.addWidget(grupo_inicio)

        # --- Grupo: Notificações ---
        grupo_notificacao = QGroupBox(tr("grupo_notificacao"))
        formulario_notificacao = QFormLayout()
        
        self.check_ativar_notif = QCheckBox(tr("chk_ativar_notif"))
        self.check_ativar_notif.setChecked(self.configuracao.get("notificacoes_ativadas"))
        
        self.spin_intervalo = QSpinBox()
        self.spin_intervalo.setRange(1, 1440) # Limita entre 1 minuto e 24 horas (1440 min)
        self.spin_intervalo.setValue(self.configuracao.get("intervalo_notificacao"))
        
        formulario_notificacao.addRow(self.check_ativar_notif)
        formulario_notificacao.addRow(tr("lbl_intervalo"), self.spin_intervalo)
        grupo_notificacao.setLayout(formulario_notificacao)
        layout_principal.addWidget(grupo_notificacao)

        # --- Botões de Ação (OK / Cancelar) ---
        caixa_botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        caixa_botoes.accepted.connect(self.ao_clicar_ok)
        caixa_botoes.rejected.connect(self.reject)
        layout_principal.addWidget(caixa_botoes)

        self.setLayout(layout_principal)

    def ao_clicar_ok(self):
        """Salva as configurações e fecha a janela."""
        
        # Atualiza o dicionário de configuração com os valores da tela
        self.configuracao["acao_ao_fechar"] = self.combo_fechar.currentData()
        self.configuracao["acao_ao_minimizar"] = self.combo_minimizar.currentData()
        self.configuracao["sincronizar_na_bandeja"] = self.check_sincronizar.isChecked()
        self.configuracao["iniciar_minimizado"] = self.check_iniciar_min.isChecked()
        self.configuracao["notificacoes_ativadas"] = self.check_ativar_notif.isChecked()
        self.configuracao["intervalo_notificacao"] = self.spin_intervalo.value()

        # Grava no disco
        mw.addonManager.writeConfig(__name__, self.configuracao)
        
        # Avisa o notificador para reiniciar o timer (pois o intervalo pode ter mudado)
        notificador.iniciar_temporizador()
        
        self.accept() # Fecha a janela com sucesso

def mostrar_configuracoes():
    """Função auxiliar para instanciar e mostrar a janela."""
    dialogo = DialogoConfiguracoes()
    dialogo.exec_()