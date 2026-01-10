# -------------------------------------------------------------------------
# Copyright © 2025 Caio Graco Purita. Todos os direitos reservados.
# ARQUIVO: notifications.py
# -------------------------------------------------------------------------
from aqt import mw  # Importa a janela principal do Anki (MainWindow)
from aqt.qt import * # Importa componentes da interface gráfica Qt
from .lang import tr  # Importa a função de tradução

class GerenciadorNotificacao:
    """
    Gerencia as notificações inteligentes e a sincronização periódica.
    Monitora o agendador do Anki para detectar quando cartões vencem.
    """
    def __init__(self):
        """
        Construtor da classe. Inicializa o temporizador e as contagens.
        """
        # Cria um temporizador (relógio) vinculado à janela principal
        self.temporizador = QTimer(mw)
        # Define qual função chamar quando o tempo acabar (tick do relógio)
        self.temporizador.timeout.connect(self.ao_bater_relogio)
        
        # Variável para armazenar o número TOTAL de cartões (Novos + Aprender + Revisar)
        # que já notificamos. Isso evita repetir a mesma notificação sem necessidade.
        self.total_conhecido = 0
        
        # Inicia a contagem baseada na configuração do usuário
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        """
        Lê as configurações do Add-on e inicia o timer se as notificações estiverem ativas.
        """
        config = mw.addonManager.getConfig(__name__)
        
        # Verifica se a opção "Ativar notificações" está marcada no menu
        if config.get("notificacoes_ativadas"):
            # Converte minutos para milissegundos (minutos * 60s * 1000ms)
            ms = config.get("intervalo_notificacao", 30) * 60 * 1000
            
            # Inicia o temporizador com o tempo definido
            self.temporizador.start(ms)
        else:
            # Se a configuração estiver desativada, paramos o relógio
            self.temporizador.stop()

    def verificar_inicializacao(self, iniciado_minimizado):
        """
        Executado apenas UMA vez ao abrir o Anki.
        Define o marco zero das pendências e notifica se foi boot automático.
        """
        try:
            # mw.col.sched.counts() retorna uma tupla: (novos, aprendizado, revisao)
            # Ex: (0, 1, 12) -> 0 novos, 1 aprendendo, 12 revisões
            contagens = mw.col.sched.counts()
            
            # Somamos TUDO. Se tiver qualquer coisa pendente, queremos saber.
            total_atual = sum(contagens)
            
            # Define a linha de base: já sabemos que esses cartões existem.
            self.total_conhecido = total_atual
            
            # Regra 1: Se o Anki iniciou minimizado (boot do Windows) e tem cartões, avisa.
            if iniciado_minimizado and total_atual > 0:
                # Busca a mensagem traduzida e formata com o número total
                msg = tr("msg_boot").format(total_atual)
                self.mostrar_notificacao(msg)
                
        except:
            # Se der erro (ex: perfil não carregado totalmente), zera tudo por segurança
            self.total_conhecido = 0

    def ao_bater_relogio(self):
        """
        Executado a cada intervalo de tempo configurado.
        Gerencia a sincronização e a verificação de novos cartões.
        """
        # --- LÓGICA DE SINCRONIZAÇÃO INTELIGENTE ---
        # Verificamos se a janela principal NÃO está visível (mw.isVisible() é False).
        # Isso significa que o Anki está minimizado na bandeja.
        if not mw.isVisible():
            # Só sincroniza se estiver "escondido", para não travar a tela enquanto você estuda.
            mw.onSync()
        
        # Após tentar sincronizar (ou não), verificamos se surgiram novos cartões
        self.verificar_novas_pendencias()

    def verificar_novas_pendencias(self):
        """
        Calcula se o número total de cartões a fazer aumentou desde a última checagem.
        """
        # Se o usuário está com a janela do Anki aberta e visível, não interrompemos com notificação
        # pois ele já está vendo os números na tela.
        if mw.isVisible():
            try:
                # Atualizamos a contagem silenciosamente para manter a referência atualizada
                self.total_conhecido = sum(mw.col.sched.counts())
            except: pass
            return

        try:
            # Obtém contagens atuais do agendador (Novos, Aprendizado, Revisão)
            contagens = mw.col.sched.counts()
            
            # --- CORREÇÃO CRUCIAL ---
            # Antes olhávamos apenas contagens[2] (Revisão Verde).
            # Agora somamos tudo. O seu cartão de teste de 1 minuto cai em contagens[1] (Aprendizado).
            total_atual = sum(contagens)
            
            # Regra 2: Só avisa se a contagem TOTAL aumentou.
            # Exemplo: Tinha 0. Passou 1 minuto. O cartão de teste venceu. Total agora é 1.
            # 1 > 0 -> Verdadeiro -> Notifica.
            if total_atual > self.total_conhecido:
                novos = total_atual - self.total_conhecido
                
                # Seleciona a mensagem correta (singular ou plural)
                if novos == 1:
                    msg = tr("msg_novos_um")
                else:
                    msg = tr("msg_novos_varios").format(novos)
                 
                # Chama a função que exibe o balão
                self.mostrar_notificacao(msg)
            
            # Atualiza a referência para a próxima verificação
            self.total_conhecido = total_atual
            
        except:
            # Em caso de erro na leitura do banco (ex: durante sync), ignora silenciosamente
            pass

    def mostrar_notificacao(self, mensagem):
        """
        Emite som e mostra o balão de notificação na bandeja do sistema.
        """
        # Emite o som padrão de aviso do sistema ("Bip")
        QApplication.beep()
        
        # Importa o gerenciador da bandeja (importação tardia para evitar erro circular)
        from .tray import gerenciador_bandeja
        
        if gerenciador_bandeja.icone_bandeja:
            # Mostra a mensagem usando o ícone padrão de informação ("i")
            # Isso garante que a notificação sempre apareça, mesmo em versões chatas do Windows
            gerenciador_bandeja.icone_bandeja.showMessage(
                "Anki Tray Pro", 
                mensagem, 
                QSystemTrayIcon.MessageIcon.Information, 
                5000 # Duração em milissegundos (5 segundos)
            )

# Instancia o gerenciador globalmente
notificador = GerenciadorNotificacao()