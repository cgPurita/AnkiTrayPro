# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------
from aqt import mw  # Importa a janela principal do Anki
from aqt.qt import * # Importa componentes da interface gráfica Qt
from .lang import tr  # Importa a função de tradução

class GerenciadorNotificacao:
    """
    Gerencia as notificações inteligentes e a sincronização periódica.
    Foca exclusivamente no AUMENTO de cartões de Revisão e Aprendizagem.
    """
    def __init__(self):
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        
        # Armazena a contagem da última verificação.
        # Serve como "linha de base" para saber se surgiram novos.
        self.referencia_anterior = 0
        
        # Inicia a contagem baseada na configuração
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """Lê config e inicia o timer."""
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            ms = config.get("intervalo_notificacao", 30) * 60 * 1000
            self.temporizador.start(ms)
        else:
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Retorna a soma apenas de APRENDIZAGEM (Learn) e REVISÃO (Review).
        Ignora completamente os cartões NOVOS (New), pois o usuário já sabe que eles existem.
        """
        try:
            # counts() -> (Novos, Aprendizado, Revisão)
            # Ex: (5 novos, 1 learn, 10 review)
            c = mw.col.sched.counts()
            
            # Somamos apenas índice 1 e 2.
            return c[1] + c[2]
        except:
            return 0

    def verificar_inicializacao(self, iniciado_minimizado):
        """
        Executado ao iniciar. Define o 'marco zero'.
        """
        # Tira uma 'foto' de como estão os baralhos agora.
        # Qualquer cartão que já exista aqui será ignorado nas notificações futuras,
        # pois ele já faz parte do passado.
        self.referencia_anterior = self.obter_contagem_relevante()
        
        # Opcional: Se quiser manter o "Bom dia" avisando o total acumulado ao ligar o PC,
        # mantemos este bloco. Se quiser silêncio absoluto até surgir um NOVO, remova o if abaixo.
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """
        Executado a cada intervalo.
        """
        # 1. Sincroniza APENAS se estiver minimizado
        if not mw.isVisible():
            mw.onSync()
        
        # 2. Verifica se algo NOVO apareceu
        self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """
        Calcula o DELTA (Diferença) entre agora e a última checagem.
        """
        # Se a janela está aberta, apenas atualizamos a referência para não notificar
        # coisas que o usuário já está vendo.
        if mw.isVisible():
            self.referencia_anterior = self.obter_contagem_relevante()
            return

        try:
            # Pega o número atual de (Learn + Review)
            atual = self.obter_contagem_relevante()
            
            # A mágica acontece aqui:
            # Se eu tinha 10 (referencia_anterior) e agora tenho 11 (atual):
            # delta = 1. Notifica "1 cartão".
            # Se eu tinha 10, estudei pelo celular e agora tenho 5:
            # delta = -5. Não faz nada.
            delta = atual - self.referencia_anterior
            
            if delta > 0:
                # Temos novidades!
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                 
                self.mostrar_notificacao(msg)
            
            # ATUALIZA A REFERÊNCIA
            # Isso garante que esses cartões não disparem notificação de novo.
            # Daqui pra frente, só avisaremos se surgir MAIS cartões além destes.
            self.referencia_anterior = atual
            
        except:
            pass

    def mostrar_notificacao(self, mensagem):
        """Emite som e mostra o balão."""
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

# Instancia
notificador = GerenciadorNotificacao()