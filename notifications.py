# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita.
# Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------

# Importa o módulo para manipulação de datas e carimbos de tempo (timestamps)
import datetime
# Importa a instância principal do Anki (MainWindow) através do objeto mw
from aqt import mw
# Importa as classes e componentes da interface gráfica Qt para Python
from aqt.qt import *
# Importa a função de tradução localizada do nosso próprio add-on
from .lang import tr

class GerenciadorNotificacao:
    """
    Classe responsável por monitorar as revisões pendentes e disparar alertas.
    Utiliza consultas SQL para precisão e sincroniza o estado com o servidor.
    """
    def __init__(self):
        # Cria um objeto de temporizador vinculado à janela principal do Anki
        self.temporizador = QTimer(mw)
        # Define qual função será executada toda vez que o tempo do timer acabar
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        # Variável para guardar o número de cartões da última verificação realizada
        self.referencia_anterior = 0
        # Executa a configuração inicial para ligar o temporizador se necessário
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """
        Configura o intervalo de execução do monitoramento baseando-se nas opções.
        """
        # Lê o arquivo de configuração do add-on carregado pelo Anki
        config = mw.addonManager.getConfig(__name__)
        # Verifica se a opção de notificações está ligada no painel de opções
        if config.get("notificacoes_ativadas"):
            # Obtém o intervalo em minutos e converte para milissegundos (padrão Qt)
            minutos = config.get("intervalo_notificacao", 30)
            ms = minutos * 60 * 1000
            # Liga o temporizador com o tempo configurado pelo usuário
            self.temporizador.start(ms)
        else:
            # Desliga o temporizador caso o usuário tenha desativado as notificações
            self.temporizador.stop()

    def obter_contagem_relevante(self):
        """
        Realiza uma contagem direta no banco de dados para evitar duplicatas.
        Busca apenas cartões em aprendizado ou prontos para revisão (Due).
        """
        try:
            # Verifica se o banco de dados da coleção está carregado e disponível
            if not mw.col:
                return 0

            # Atualiza o agendador interno para processar cartões baseados em tempo
            mw.col.reset()

            # Captura o horário atual do sistema no formato de segundos (Unix Timestamp)
            agora_timestamp = int(datetime.datetime.now().timestamp())
            
            # Define a consulta SQL para buscar cartões únicos nas filas de estudo
            # queue 1, 2, 3 correspondem aos estados de Aprendizado e Revisão
            query = "SELECT count(id) FROM cards WHERE queue IN (1, 2, 3) AND due <= ?"
            
            # Executa a busca no banco de dados e retorna o valor numérico resultante
            total = mw.col.db.scalar(query, agora_timestamp) or 0
            
            # Retorna a contagem total de cartões que precisam ser feitos agora
            return total
            
        except:
            # Retorna zero em caso de qualquer erro de acesso ao banco de dados
            return 0
    
    def resetar_contagem(self):
        """
        Sincroniza a memória do notificador com a realidade atual dos baralhos.
        """
        # Pega a contagem exata no momento e define como a nova base de comparação
        self.referencia_anterior = self.obter_contagem_relevante()

    def verificar_inicializacao(self, iniciado_minimizado):
        """
        Lógica executada no momento em que o Anki termina de carregar o perfil.
        """
        # Realiza um reset inicial para não notificar pendências que já existiam
        self.resetar_contagem()
        # Se o app iniciou escondido e já há tarefas, dispara a notificação de boas-vindas
        if iniciado_minimizado and self.referencia_anterior > 0:
            # Formata a mensagem traduzida com o número de cartões encontrados
            msg = tr("msg_boot").format(self.referencia_anterior)
            # Chama a exibição visual da mensagem
            self.mostrar_notificacao(msg)

    def ao_bater_relogio(self):
        """
        Função principal disparada periodicamente pelo cronômetro do sistema.
        """
        # Verifica se a janela principal não está visível para o usuário
        if not mw.isVisible():
            # Inicia o processo de sincronização nativa do Anki com o AnkiWeb
            mw.onSync()
            # Agenda a verificação de cartões para 3 segundos depois da sincronia
            QTimer.singleShot(3000, self.verificar_novas_pendencias)
        else:
            # Se o usuário estiver usando o Anki, apenas executa a verificação direta
            self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """
        Calcula a diferença de cartões e decide se deve enviar uma notificação.
        """
        # Se o usuário abriu o Anki, ele já viu os cartões, então cancelamos o alerta
        if mw.isVisible():
            # Atualiza a referência silenciosamente para o estado atual
            self.resetar_contagem()
            # Encerra a função sem disparar notificações
            return

        try:
            # Obtém o número atual de cartões pendentes no banco de dados
            atual = self.obter_contagem_relevante()
            # Calcula a diferença entre o que existe agora e o que existia antes
            delta = atual - self.referencia_anterior
            
            # Se o número de cartões aumentou, novos prazos venceram
            if delta > 0:
                # Escolhe entre a mensagem no singular (1 cartão) ou plural
                if delta == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(delta)
                
                # Dispara o alerta sonoro e visual para o usuário
                self.mostrar_notificacao(msg)
                # Atualiza a referência para que o próximo alerta use o novo valor
                self.referencia_anterior = atual
            # Se o número diminuiu, significa que o usuário estudou em outro dispositivo
            elif delta < 0:
                # Apenas atualiza o valor de referência para acompanhar o novo estado
                self.referencia_anterior = atual
            
        except:
            # Ignora falhas silenciosamente para manter a estabilidade do programa
            pass

    def mostrar_notificacao(self, mensagem):
        """
        Exibe o balão de mensagem oficial do Windows na bandeja do sistema.
        """
        # Toca o som de alerta padrão configurado no sistema operacional
        QApplication.beep()
        # Importa o gerenciador de bandeja para acessar o objeto do ícone
        from .tray import gerenciador_bandeja
        # Verifica se o ícone da bandeja está ativo e disponível
        if gerenciador_bandeja.icone_bandeja:
            # Exibe a notificação flutuante por 5 segundos no canto da tela
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000
            )

# Cria a instância única do notificador que ficará ativa durante a sessão
notificador = GerenciadorNotificacao()