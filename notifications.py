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
    Usa a árvore de baralhos (Deck Tree) para contar pendências globais,
    exatamente como visto na tela inicial do Anki.
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
        Ignora cartões Novos (New).
        """
        try:
            if not mw.col:
                return 0

            # Obtém a árvore completa de baralhos (igual à tela 'Decks')
            # deck_due_tree() retorna uma lista de nós.
            arvore = mw.col.sched.deck_due_tree()
            
            total_learn = 0
            total_review = 0
            total_new = 0 # Contamos só para logar, mas não usamos na soma final
            
            # Função recursiva para somar os totais da árvore
            def somar_no(no):
                nonlocal total_learn, total_review, total_new
                # A estrutura do nó varia levemente entre versões, mas geralmente:
                # new_count, learn_count, review_count são atributos ou índices.
                # No Anki moderno (Qt6), são atributos do objeto.
                
                total_new += getattr(no, 'new_count', 0)
                total_learn += getattr(no, 'learn_count', 0)
                total_review += getattr(no, 'review_count', 0)
                
                # Percorre os filhos (sub-baralhos)
                for filho in no.children:
                    somar_no(filho)

            # Executa a soma em todos os nós raiz
            for no_raiz in arvore:
                somar_no(no_raiz)

            # A soma que importa para o Padre: Learn (Vermelho) + Due (Verde)
            total_relevante = total_learn + total_review
            
            self.registrar_log(f"SCAN GLOBAL: Novos(Ignorados)={total_new} | Learn={total_learn} | Due={total_review} -> TOTAL RELEVANTE={total_relevante}")
            
            return total_relevante

        except Exception as e:
            self.registrar_log(f"ERRO ao ler árvore: {str(e)}")
            return 0
    
    def resetar_contagem(self):
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