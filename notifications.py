# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------
from aqt import mw
from aqt.qt import *
from .lang import tr

class GerenciadorNotificacao:
    """
    Gerencia as notificações inteligentes e a sincronização periódica.
    """
    def __init__(self):
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        
        # Armazena o número de revisões conhecidas para detectar apenas novas
        self.revisoes_conhecidas = 0
        
        # Inicia a contagem baseada na configuração
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            # Converte minutos para milissegundos
            ms = config.get("intervalo_notificacao", 30) * 60 * 1000
            self.temporizador.start(ms)
        else:
            self.temporizador.stop()

    def verificar_inicializacao(self, iniciado_minimizado):
        """
        Executado apenas UMA vez ao abrir o Anki.
        Define o marco zero das revisões e notifica se foi boot automático.
        """
        try:
            # counts() retorna: (novos, aprendizado, revisao)
            contagens = mw.col.sched.counts()
            total_geral = sum(contagens)
            total_revisao = contagens[2]
            
            # Define a linha de base: já sabemos que esses existem, não avisar de novo.
            self.revisoes_conhecidas = total_revisao
            
            # Regra 1: Se iniciou com o Windows (minimizado) e tem cartões, avisa.
            if iniciado_minimizado and total_geral > 0:
                # Usa tradução dinâmica
                msg = tr("msg_boot").format(total_geral)
                self.mostrar_notificacao(msg)
                
        except:
            # Se der erro (ex: perfil não carregado), zera tudo
            self.revisoes_conhecidas = 0

    def ao_bater_relogio(self):
        """
        Executado a cada intervalo (ex: 30 min).
        Sincroniza e verifica se cartões 'venceram' recentemente.
        """
        # 1. Executa a Sincronização (Regra: fazer sync periódico)
        mw.onSync()
        
        # 2. Verifica as pendências
        self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        # Se o usuário está com a janela aberta, não interrompa com notificações
        if mw.isVisible():
            try:
                # Atualizamos a contagem para não acumular notificações quando ele minimizar
                self.revisoes_conhecidas = mw.col.sched.counts()[2]
            except: pass
            return

        try:
            contagens = mw.col.sched.counts()
            revisoes_atuais = contagens[2] # Apenas fila de Revisão (Verde)
            
            # Regra 2: Só avisa se a contagem de REVISÃO aumentou.
            if revisoes_atuais > self.revisoes_conhecidas:
                novos = revisoes_atuais - self.revisoes_conhecidas
                
                # Seleciona a mensagem correta (singular ou plural)
                if novos == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(novos)
                
                self.mostrar_notificacao(msg)
            
            # Atualiza a referência para a próxima verificação
            self.revisoes_conhecidas = revisoes_atuais
            
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
                5000 # Duração em milissegundos
            )

notificador = GerenciadorNotificacao()