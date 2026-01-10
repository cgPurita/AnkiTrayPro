# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------

import os
import datetime
from aqt import mw
from aqt.qt import *
from .lang import tr

class GerenciadorNotificacao:
    """
    Gerencia as notificações inteligentes.
    Usa consultas SQL diretas para evitar contagens duplicadas do agendador do Anki.
    """
    def __init__(self):
        # Define o caminho do arquivo de log para diagnóstico
        self.caminho_log = os.path.join(os.path.dirname(__file__), "debug_log.txt")
        # Temporizador para verificações periódicas
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        # Referência para detectar novos cartões surgindo
        self.referencia_anterior = 0
        # Inicializa o timer baseado no config.json
        self.iniciar_temporizador()

    def registrar_log(self, mensagem):
        """Grava eventos no arquivo debug_log.txt."""
        try:
            agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.caminho_log, "a", encoding="utf-8") as f:
                f.write(f"[{agora}] [NOTIFIER] {mensagem}\n")
        except:
            pass

    def iniciar_temporizador(self):
        """Lê as configurações e inicia o timer."""
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            self.registrar_log(f"Timer configurado: {minutos} min.")
            self.temporizador.start(ms)
        else:
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Consulta o banco de dados por IDs únicos de cartões Learn e Due.
        Isso elimina o bug onde o Anki conta o mesmo cartão duas vezes na árvore.
        """
        try:
            if not mw.col:
                return 0

            # Força o processamento de cartões que venceram o tempo
            mw.col.reset()

            # Consultamos o banco de dados por cartões que NÃO são novos (queue != 0)
            # e que estão com o prazo de revisão (due) vencido em relação ao momento atual.
            # queue 1 = Learn, queue 2 = Review/Due, queue 3 = Day Learn.
            agora_timestamp = int(datetime.datetime.now().timestamp())
            
            # SQL para contar cartões únicos que estão em Learn ou Due
            # queue in (1, 2, 3) filtra para não pegar cartões Novos (queue 0)
            # due <= ? garante que só pegamos o que venceu agora
            query = "SELECT count(id) FROM cards WHERE queue IN (1, 2, 3) AND due <= ?"
            
            # Executa a consulta no banco de dados da coleção
            total = mw.col.db.scalar(query, agora_timestamp) or 0
            
            self.registrar_log(f"BANCO DE DADOS: Total de cartões únicos (Learn+Due) encontrados: {total}")
            return total
            
        except Exception as e:
            self.registrar_log(f"ERRO SQL: {str(e)}")
            return 0
    
    def resetar_contagem(self):
        """Sincroniza a referência com o estado real do banco."""
        self.referencia_anterior = self.obter_contagem_relevante()
        self.registrar_log(f"RESET: Referência em {self.referencia_anterior}.")

    def verificar_inicializacao(self, iniciado_minimizado):
        """Checagem inicial ao abrir o perfil."""
        self.resetar_contagem()
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """Ciclo do timer: Sincroniza e depois verifica."""
        self.registrar_log("TIMER: Iniciando ciclo...")
        
        if not mw.isVisible():
            self.registrar_log("TIMER: Sincronizando antes de contar...")
            mw.onSync()
            # Espera 3 segundos para o banco de dados estabilizar após a sync
            QTimer.singleShot(3000, self.verificar_novas_pendencias)
        else:
            self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """Compara a contagem do banco com a referência anterior."""
        if mw.isVisible():
            self.resetar_contagem()
            return

        try:
            atual = self.obter_contagem_relevante()
            delta = atual - self.referencia_anterior
            
            self.registrar_log(f"CHECK: Atual={atual} | Anterior={self.referencia_anterior} | Delta={delta}")
            
            if delta > 0:
                # Se o delta for positivo, novos cartões venceram
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                
                self.registrar_log(f"DISPARO: Notificando {delta} cartões.")
                self.mostrar_notificacao(msg)
                self.referencia_anterior = atual
            elif delta < 0:
                # Se estudou em outro lugar, apenas ajusta a referência para baixo
                self.registrar_log(f"AJUSTE: Pendências caíram para {atual}. Atualizando referência.")
                self.referencia_anterior = atual
            
        except Exception as e:
            self.registrar_log(f"ERRO CHECK: {str(e)}")

    def mostrar_notificacao(self, mensagem):
        """Chama a interface do sistema para exibir o alerta."""
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", mensagem, QSystemTrayIcon.MessageIcon.Information, 5000
            )

notificador = GerenciadorNotificacao()