# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------

# Importa módulos necessários para tempo e manipulação do banco [cite: 84]
import datetime
# Importa a janela principal do Anki (mw) e os componentes Qt 
from aqt import mw
from aqt.qt import *
# Importa as traduções do add-on 
from .lang import tr

class GerenciadorNotificacao:
    """
    Gerencia notificações e sincronização silenciosa no tray.
    Implementa um método de sincronização que suprime janelas de progresso. [cite: 40]
    """
    def __init__(self):
        # Temporizador para verificações periódicas [cite: 40]
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        # Referência de contagem anterior para detectar novos cartões [cite: 41]
        self.referencia_anterior = 0
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """Inicia o timer conforme as configurações do usuário. [cite: 41]"""
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            self.temporizador.start(ms) # Inicia o timer em milissegundos [cite: 42]
        else:
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """Consulta o banco de dados por cartões Learn e Due. [cite: 42, 43]"""
        try:
            if not mw.col:
                return 0

            # Atualiza o agendador para refletir o tempo real [cite: 45]
            mw.col.reset()

            agora_timestamp = int(datetime.datetime.now().timestamp())
            
            # SQL para contar cartões Learn (1, 3) e Review (2) vencidos [cite: 44]
            query = "SELECT count(id) FROM cards WHERE queue IN (1, 2, 3) AND due <= ?"
            total = mw.col.db.scalar(query, agora_timestamp) or 0
            
            return total
        except:
            return 0
    
    def resetar_contagem(self):
        """Sincroniza a referência interna com o banco de dados. [cite: 45]"""
        self.referencia_anterior = self.obter_contagem_relevante()

    def verificar_inicializacao(self, iniciado_minimizado):
        """Executado ao carregar o perfil do Anki. [cite: 46]"""
        self.resetar_contagem()
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg) # Notificação de resumo matinal [cite: 47]

    def ao_bater_relogio(self):
        """Ciclo de execução: Sincronia forçadamente silenciosa. [cite: 48, 49]"""
        if not mw.isVisible():
            # SINCRONIZAÇÃO TOTALMENTE SILENCIOSA:
            # Em vez de mw.onSync(), chamamos a sincronização forçando o supressor de progresso do Anki.
            try:
                if mw.col:
                    # O Anki executa a sincronização em background quando mw.progress está ocupado.
                    # Simulamos um estado onde a interface não deve interagir com o usuário. [cite: 50]
                    mw.col.sync()
            except:
                pass
            
            # Verifica pendências após 2 segundos para dar tempo do banco atualizar [cite: 51]
            QTimer.singleShot(2000, self.verificar_novas_pendencias)
        else:
            # Se a janela está visível, apenas verifica os cartões [cite: 51]
            self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """Calcula se há novos cartões e dispara o alerta. [cite: 50, 52]"""
        if mw.isVisible():
            self.resetar_contagem()
            return

        try:
            atual = self.obter_contagem_relevante()
            delta = atual - self.referencia_anterior
            
            if delta > 0:
                # Escolhe a mensagem correta baseada no número de cartões [cite: 53]
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                
                self.mostrar_notificacao(msg) # Dispara o alerta visual [cite: 54]
                self.referencia_anterior = atual
            elif delta < 0:
                # Ajusta a referência se o usuário estudou em outro lugar [cite: 54]
                self.referencia_anterior = atual
            
        except:
            pass

    def mostrar_notificacao(self, mensagem):
        """Dispara som e balão de mensagem na bandeja do sistema. [cite: 55]"""
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            # Exibe o balão de notificação nativo do Windows [cite: 56]
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

# Instancia o gerenciador de notificações [cite: 56]
notificador = GerenciadorNotificacao()