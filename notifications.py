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
    Adicionada proteção para não notificar números instáveis durante sincronização.
    """
    def __init__(self):
        self.caminho_log = os.path.join(os.path.dirname(__file__), "debug_log.txt")
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        self.referencia_anterior = 0
        self.iniciar_temporizador()

    def registrar_log(self, mensagem):
        """Registra eventos no arquivo de debug."""
        try:
            agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.caminho_log, "a", encoding="utf-8") as f:
                f.write(f"[{agora}] [NOTIFIER] {mensagem}\n")
        except:
            pass

    def iniciar_temporizador(self):
        """Inicia o timer de verificação."""
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            self.registrar_log(f"Timer configurado: {minutos} min.")
            self.temporizador.start(ms)
        else:
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """Lê a árvore de baralhos somando Learn + Due."""
        try:
            if not mw.col:
                return 0

            # Atualiza o agendador para ver cartões que venceram por tempo
            mw.col.reset()

            raiz = mw.col.sched.deck_due_tree()
            total_learn = 0
            total_review = 0
            
            def processar_no(no):
                nonlocal total_learn, total_review
                total_learn += getattr(no, 'learn_count', 0)
                total_review += getattr(no, 'review_count', 0)
                if hasattr(no, 'children'):
                    for filho in no.children:
                        processar_no(filho)

            processar_no(raiz)
            total = total_learn + total_review
            self.registrar_log(f"SCAN: Learn={total_learn} | Due={total_review} -> TOTAL={total}")
            return total
        except Exception as e:
            self.registrar_log(f"ERRO SCAN: {str(e)}")
            return 0
    
    def resetar_contagem(self):
        """Sincroniza a referência com o estado atual."""
        self.referencia_anterior = self.obter_contagem_relevante()
        self.registrar_log(f"RESET: Referência em {self.referencia_anterior}.")

    def verificar_inicializacao(self, iniciado_minimizado):
        """Verifica pendências no boot."""
        self.resetar_contagem()
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """Ciclo do timer: Primeiro sincroniza, depois verifica para garantir números reais."""
        self.registrar_log("TIMER: Iniciando ciclo...")
        
        # Se estiver minimizado, sincroniza primeiro para atualizar os dados do servidor
        if not mw.isVisible():
            self.registrar_log("TIMER: Sincronizando antes de contar...")
            mw.onSync()
            # Aguarda um pequeno instante para o Anki processar os dados baixados
            QTimer.singleShot(2000, self.verificar_novas_pendencias)
        else:
            self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """Verifica se há novos cartões após a estabilização dos dados."""
        if mw.isVisible():
            self.resetar_contagem()
            return

        try:
            atual = self.obter_contagem_relevante()
            delta = atual - self.referencia_anterior
            
            self.registrar_log(f"CHECK: Atual={atual} | Anterior={self.referencia_anterior} | Delta={delta}")
            
            if delta > 0:
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                
                self.registrar_log(f"DISPARO: Notificando {delta} novos cartões.")
                self.mostrar_notificacao(msg)
                self.referencia_anterior = atual
            elif delta < 0:
                # Se o número diminuiu (você estudou em outro lugar), apenas atualiza a referência
                self.registrar_log(f"Ajuste: Pendências diminuíram para {atual}. Atualizando referência.")
                self.referencia_anterior = atual
            
        except Exception as e:
            self.registrar_log(f"ERRO CHECK: {str(e)}")

    def mostrar_notificacao(self, mensagem):
        """Exibe o alerta visual."""
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", mensagem, QSystemTrayIcon.MessageIcon.Information, 5000
            )

notificador = GerenciadorNotificacao()