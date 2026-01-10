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
    Força a atualização do agendador e usa a árvore de baralhos para contagem global.
    """
    def __init__(self):
        self.caminho_log = os.path.join(os.path.dirname(__file__), "debug_log.txt")
        self.temporizador = QTimer(mw)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        self.referencia_anterior = 0
        self.iniciar_temporizador()

    def registrar_log(self, mensagem):
        try:
            agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.caminho_log, "a", encoding="utf-8") as f:
                f.write(f"[{agora}] [NOTIFIER] {mensagem}\n")
        except:
            pass

    def iniciar_temporizador(self):
        config = mw.addonManager.getConfig(__name__)
        if config.get("notificacoes_ativadas"):
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            self.registrar_log(f"Timer iniciado. Intervalo: {minutos} min.")
            self.temporizador.start(ms)
        else:
            self.registrar_log("Notificações desativadas.")
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Percorre a árvore de baralhos para somar Review + Learn de TODA a coleção.
        CRUCIAL: Força o reset do scheduler antes para atualizar cartões de tempo (Learn).
        """
        try:
            if not mw.col:
                return 0

            # --- O PULO DO GATO ---
            # Força o Anki a recalcular as filas de 'Learn' baseadas no tempo atual.
            # Sem isso, ele acha que o tempo parou quando foi minimizado.
            mw.col.reset()

            # Obtém a árvore completa de baralhos
            arvore = mw.col.sched.deck_due_tree()
            
            total_learn = 0
            total_review = 0
            total_new = 0
            
            # Função recursiva para somar os totais da árvore
            def somar_no(no):
                nonlocal total_learn, total_review, total_new
                
                total_new += getattr(no, 'new_count', 0)
                total_learn += getattr(no, 'learn_count', 0)
                total_review += getattr(no, 'review_count', 0)
                
                for filho in no.children:
                    somar_no(filho)

            for no_raiz in arvore:
                somar_no(no_raiz)

            # Soma apenas Learn e Review (Ignora New conforme solicitado)
            total_relevante = total_learn + total_review
            
            self.registrar_log(f"SCAN: Novos(Ignorados)={total_new} | Learn={total_learn} | Due={total_review} -> TOTAL={total_relevante}")
            
            return total_relevante

        except Exception as e:
            self.registrar_log(f"ERRO ao ler árvore: {str(e)}")
            return 0
    
    def resetar_contagem(self):
        # Chama a contagem (que agora faz o reset interno) para pegar o valor real atual
        atual = self.obter_contagem_relevante()
        self.referencia_anterior = atual
        self.registrar_log(f"RESET: Referência atualizada para {self.referencia_anterior}.")

    def verificar_inicializacao(self, iniciado_minimizado):
        self.resetar_contagem()
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        self.registrar_log("TIMER: Verificando...")
        self.verificar_novas_pendencias()
        
        # O reset() dentro da verificação já atualiza o banco, 
        # mas mantemos o sync se configurado.
        if not mw.isVisible():
            mw.onSync()

    def verificar_novas_pendencias(self):
        if mw.isVisible():
            self.registrar_log("Janela visível. Resetando referência.")
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
                
                self.registrar_log(f"DISPARO: Notificando '{msg}'")
                self.mostrar_notificacao(msg)
                self.referencia_anterior = atual
            
        except Exception as e:
            self.registrar_log(f"ERRO CHECK: {str(e)}")

    def mostrar_notificacao(self, mensagem):
        QApplication.beep()
        from .tray import gerenciador_bandeja
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

notificador = GerenciadorNotificacao()