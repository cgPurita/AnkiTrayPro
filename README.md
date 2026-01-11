# Anki Tray Pro 📥

> **Minimize o Anki para a bandeja, receba notificações de estudos e mantenha seu fluxo focado.**

O **Anki Tray Pro** é um add-on projetado para quem estuda o dia todo e precisa que o Anki fique "invisível", mas acessível. Ele permite minimizar o aplicativo para a bandeja do sistema (perto do relógio), sincronizar automaticamente ao esconder e notificar quando houver revisões pendentes.

---

### ⚠️ Requisitos de Sistema & Compatibilidade

Este software foi desenvolvido e testado **exclusivamente para o Windows 11**.

* **✅ Windows 11:** Totalmente suportado e otimizado.
* **❓ Windows 10:** Não garantido. Pode funcionar, mas não há garantia de estabilidade.
* **❌ macOS / Linux:** **INCOMPATÍVEL.** Este add-on utiliza bibliotecas exclusivas do Windows (`winreg`, `VBScript`) e comportamentos de bandeja que não funcionam em outros sistemas.

---

## 📥 Instalação

### Opção 1: Via AnkiWeb (Recomendado)
1. Abra o Anki e vá em **Ferramentas** -> **Complementos** (Add-ons).
2. Clique em **Obter Complementos**.
3. Cole o código abaixo:

```text
1106373954
```

### Opção 2: Instalação Manual (Desenvolvedor)
1. Baixe este repositório ou clone via Git.
2. Copie a pasta `AnkiTrayPro` para dentro da pasta `addons21` do seu Anki.
3. Reinicie o Anki.

---

## ✨ Recursos Principais

| Funcionalidade | Descrição |
| :--- | :--- |
| **Minimizar para a Bandeja** | Ao clicar no **X** ou minimizar, o Anki vai para a área de notificação (perto do relógio) em vez de fechar. |
| **Sincronização Automática** | Configure para sincronizar sua coleção automaticamente toda vez que o Anki for enviado para a bandeja. |
| **Notificações Inteligentes** | Receba alertas visuais e sonoros discretos (nativos do Windows) quando houver cartões vencidos. |
| **Inicialização Silenciosa** | Opção para iniciar o Anki automaticamente junto com o Windows, já minimizado na bandeja. |
| **Totalmente em Português** | Interface e menus de configuração nativos em PT-BR. |

---

## ⚙️ Configuração

Acesse o menu **Ferramentas** -> **Opções do Anki Tray Pro** para personalizar:

### 1. Comportamento da Janela
* **Ao clicar no 'X' (Fechar):** Escolha entre enviar para a bandeja (padrão) ou encerrar o programa definitivamente.
* **Ao minimizar (_):** Escolha se o botão padrão de minimizar deve enviar para a bandeja ou manter na barra de tarefas.

### 2. Sincronização
* **Sincronizar ao enviar para o Tray:** Garante que seus dados estejam salvos na nuvem sempre que você "esconder" o Anki.

### 3. Notificações
* Ative ou desative os avisos de revisão.
* **Intervalo de Verificação:** Defina a frequência (em minutos) que o add-on verifica se há novos cartões.
* *Nota:* As notificações só aparecem se o Anki estiver minimizado, para não incomodar enquanto você já está estudando.

---

## 🛠️ Tecnologias

* **Python 3.9+**
* **Qt6 / PyQt6** (Interface Gráfica do Anki)
* **Windows API** (WinReg e VBScript para processos em segundo plano)

---

## © Direitos Autorais e Licença

**Copyright © 2025 Caio Graco Purita.**
Todos os direitos reservados.

Este projeto foi desenvolvido para facilitar a rotina de estudos contínuos.