# Anki Tray Pro 📥

> **Minimize o Anki para a bandeja, receba notificações de estudos e mantenha seu fluxo focado.**

O **Anki Tray Pro** é um add-on projetado para quem estuda durante o dia todo e precisa que o Anki fique "invisível", mas acessível. Ele permite minimizar o aplicativo para a bandeja do sistema (perto do relógio), sincronizar automaticamente ao esconder e notificar quando houver revisões pendentes.

---

## 📥 Instalação

### Via AnkiWeb
1. Abra o Anki e vá em **Ferramentas** -> **Complementos** (Add-ons).
2. Clique em **Obter Complementos**.
3. Cole o código abaixo:

```text
(CÓDIGO_DO_ANKIWEB_AQUI)
```

### Instalação Manual (Desenvolvedor)
1. Baixe este repositório ou clone via Git.
2. Copie a pasta `AnkiTrayPro` para dentro da pasta `addons21` do seu Anki.
3. Reinicie o Anki.

---

## ✨ Recursos Principais

| Funcionalidade | Descrição |
| :--- | :--- |
| **Minimizar para a Bandeja** | Ao clicar no **X** ou minimizar, o Anki vai para o ícone perto do relógio (Tray) em vez de fechar. |
| **Sincronização Automática** | Configure para sincronizar seus decks toda vez que o Anki for enviado para a bandeja. |
| **Notificações de Estudo** | Receba um alerta visual e sonoro discreto a cada X minutos se houver cartões vencidos. |
| **Inicialização Silenciosa** | Opção para iniciar o Anki já minimizado (útil para iniciar junto com o sistema). |
| **Totalmente em Português** | Interface e configurações nativas em PT-BR. |

---

## ⚙️ Configuração

Acesse o menu **Ferramentas** -> **Opções do Anki Tray Pro** para personalizar:

### 1. Comportamento da Janela
* **Ao clicar no 'X' (Fechar):** Escolha entre enviar para a bandeja (padrão) ou fechar o programa realmente.
* **Ao minimizar (_):** Escolha se o botão de minimizar padrão do Windows deve enviar para a bandeja ou manter na barra de tarefas.

### 2. Sincronização
* **Sincronizar ao enviar para o Tray:** Garante que seus dados estejam salvos na nuvem sempre que você "esconder" o Anki.

### 3. Notificações
* Defina se quer ser avisado sobre revisões e escolha o **intervalo de verificação** (em minutos).
* *Nota:* As notificações só aparecem se o Anki estiver minimizado na bandeja, para não incomodar enquanto você já estuda.

---

## 🛠️ Tecnologias

* **Python 3.9+**
* **Qt6 / PyQt6** (Interface Gráfica do Anki)

---

## © Direitos Autorais e Licença

**Copyright © 2025 Caio Graco Purita.**
Todos os direitos reservados.

Este projeto foi desenvolvido para facilitar a rotina de estudos contínuos.