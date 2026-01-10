# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------

# Importa o módulo datetime para trabalhar com timestamps
import datetime
# Importa a instância principal do Anki (MainWindow) e componentes Qt
from aqt import mw
from aqt.qt import *
# Importa a função de tradução para mensagens localizadas
from .lang import tr

class GerenciadorNotificacao:
    """
    Gerencia as notificações e a sincronização silenciosa.
    Força a atualização da interface (UI) para evitar números defasados na Home.
    """
    def __init__(self):
        # [cite_start]Cria um temporizador vinculado à janela principal [cite: 40]
        self.temporizador = QTimer(mw)
        # [cite_start]Define a função que será chamada periodicamente [cite: 40]
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        # [cite_start]Armazena o valor da última contagem para detectar novos cartões [cite: 41]
        self.referencia_anterior = 0
        # [cite_start]Inicia o timer com base nas configurações do usuário [cite: 41]
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """Lê o intervalo de tempo das configurações e inicia o timer."""
        # [cite_start]Acessa o arquivo de configuração do complemento no Anki [cite: 42]
        config = mw.addonManager.getConfig(__name__)
        # [cite_start]Verifica se o usuário ativou o sistema de notificações [cite: 42]
        if config.get("notificacoes_ativadas"):
            # [cite_start]Converte minutos para milissegundos [cite: 42]
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            # [cite_start]Dispara o temporizador [cite: 42]
            self.temporizador.start(ms)
        else:
            # [cite_start]Para o temporizador se as notificações estiverem desligadas [cite: 42]
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Consulta o banco de dados SQL por IDs únicos de cartões Learn e Due.
        Ignora cartões 'New' para focar apenas no que precisa ser revisado.
        """
        try:
            # [cite_start]Verifica se a coleção de cartões está carregada [cite: 43]
            if not mw.col:
                return 0

            # [cite_start]Atualiza o agendador para processar cartões que venceram por tempo [cite: 45]
            mw.col.reset()

            # Obtém o horário atual do sistema
            agora_timestamp = int(datetime.datetime.now().timestamp())
            
            # Query SQL para buscar cartões nas filas 1, 2 e 3 (Learn/Review) vencidos
            query = "SELECT count(id) FROM cards WHERE queue IN (1, 2, 3) AND due <= ?"
            # [cite_start]Executa a busca direta no banco de dados da coleção [cite: 43]
            total = mw.col.db.scalar(query, agora_timestamp) or 0
            
            return total
        except:
            # [cite_start]Retorna zero em caso de falha técnica no acesso ao banco [cite: 44]
            return 0
    
    def resetar_contagem(self):
        """Atualiza a referência interna para o estado atual da coleção."""
        # [cite_start]Sincroniza o valor anterior com o valor real presente no banco agora [cite: 45]
        self.referencia_anterior = self.obter_contagem_relevante()

    def verificar_inicializacao(self, iniciado_minimizado):
        """Executado no momento do carregamento do perfil do usuário."""
        # [cite_start]Zera a contagem inicial para não notificar pendências do passado [cite: 47]
        self.resetar_contagem()
        # [cite_start]Se iniciou minimizado e há tarefas, mostra o resumo de boas-vindas [cite: 47]
        if iniciado_minimizado and self.referencia_anterior > 0:
            msg = tr("msg_boot").format(self.referencia_anterior)
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """Ciclo de execução do timer: Sincronia silenciosa e atualização de UI."""
        # [cite_start]Ações executadas apenas quando o Anki está oculto na bandeja [cite: 51]
        if not mw.isVisible():
            try:
                if mw.col:
                    # [cite_start]Executa sincronização de baixo nível (sem pop-ups de interface) [cite: 50]
                    mw.col.sync()
                    # FORÇA A ATUALIZAÇÃO DA TELA INICIAL (UI):
                    # Isso garante que ao abrir o Anki, os números já estejam atualizados
                    mw.moveToState("deckBrowser")
            except:
                pass
            
            # [cite_start]Agenda a verificação de novas pendências para 3 segundos após a sincronia [cite: 49]
            QTimer.singleShot(3000, self.verificar_novas_pendencias)
        else:
            # [cite_start]Se a janela está aberta, apenas verifica os cartões [cite: 51]
            self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """Compara o banco com a referência anterior e decide se notifica."""
        # [cite_start]Se o usuário está com a janela aberta, ele já está vendo o progresso [cite: 51]
        if mw.isVisible():
            self.resetar_contagem()
            return

        try:
            # [cite_start]Obtém a contagem atualizada do banco de dados [cite: 52]
            atual = self.obter_contagem_relevante()
            # [cite_start]Calcula quantos cartões novos surgiram desde a última verificação [cite: 52]
            delta = atual - self.referencia_anterior
            
            # [cite_start]Se houver novos cartões vencidos [cite: 53]
            if delta > 0:
                # [cite_start]Formata a mensagem baseada na quantidade (singular/plural) [cite: 53]
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                
                # [cite_start]Dispara a notificação visual e sonora na bandeja [cite: 54]
                self.mostrar_notificacao(msg)
                # [cite_start]Atualiza a referência para só notificar o próximo aumento [cite: 54]
                self.referencia_anterior = atual
            elif delta < 0:
                # [cite_start]Se o número diminuiu, atualiza a referência silenciosamente [cite: 54]
                self.referencia_anterior = atual
            
        except:
            # [cite_start]Ignora erros de processamento para manter o app estável [cite: 55]
            pass

    def mostrar_notificacao(self, mensagem):
        """Exibe o balão de alerta na bandeja do sistema através do Qt."""
        # [cite_start]Toca o bipe sonoro do Windows [cite: 56]
        QApplication.beep()
        # [cite_start]Importa o gerenciador de bandeja localmente para evitar erros de importação [cite: 56]
        from .tray import gerenciador_bandeja
        # [cite_start]Se o ícone estiver ativo, exibe a mensagem flutuante [cite: 56]
        if gerenciador_bandeja.icone_bandeja:
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

# Instancia o objeto global que monitora as notificações
notificador = GerenciadorNotificacao()