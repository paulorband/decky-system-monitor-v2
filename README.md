# System Monitor — plugin Decky Loader

Monitor de recursos do sistema para o **Game Mode**: CPU, GPU, RAM, bateria, temperaturas e ventoinhas
no Quick Access Menu, mais um **gerenciador de processos** em tela cheia. Leve (Python stdlib, coleta sob demanda)
e 100% navegável pelo controle.

Funciona em SteamOS (Steam Deck), Bazzite e CachyOS Handheld (ROG Ally / Ally X, Legion Go…).

## Uso

**Dashboard** — botão `…` (Quick Access) → ícone do plugin.

| Controle | Ação |
|---|---|
| D-pad / analógico | navega entre os cartões |
| **A** no cartão | expande/recolhe detalhes (núcleos, VRAM/GTT, saúde da bateria) |
| **A** em "Gerenciador de processos" | abre a tela de processos |

**Gerenciador de processos**

| Controle | Ação |
|---|---|
| **A** no cabeçalho (Processo / CPU / RAM) | ordena pela coluna; de novo inverte a ordem |
| **X** | alterna a coluna de ordenação (CPU → RAM → Nome) |
| **Y** | pausa/retoma a atualização (útil para navegar sem a lista mudar) |
| **A** num grupo (`steamwebhelper ×8`) | mostra as instâncias do grupo |
| **A** na linha | mostra linha de comando, PPID, threads e estado |
| "Agrupar" / "Desagrupar" | junta processos de mesmo nome somando CPU e RAM (ligado por padrão) |
| **B** | volta |

CPU % de um processo é relativo à máquina inteira (100% = todos os núcleos ocupados), como no Gerenciador de Tarefas do Windows.

## Desenvolvimento

Requisitos: Node 20+, pnpm, [uv](https://docs.astral.sh/uv/) (para os testes Python) e, no Windows, Git for Windows (Git Bash).

```bash
pnpm install
```

```bash
pnpm typecheck && pnpm build && pnpm test:py
```

O projeto segue **Spec Driven Development**: veja [`specs/`](specs/README.md) e a [constituição](specs/constitution.md).

## Deploy no aparelho (ROG Xbox Ally X com Bazzite)

### 1. Preparar o aparelho (uma vez)

No **Modo Desktop** do Bazzite, abra o terminal (Konsole):

```bash
sudo systemctl enable --now sshd
```

```bash
ip -4 addr show | grep inet
```

Garanta que o Decky Loader está instalado (`ujust setup-decky` no Bazzite) e, nas configurações do Decky,
ative o **Modo desenvolvedor** (permite instalar de ZIP e ver logs).

### 2. Configurar a chave SSH (no Windows, uma vez)

```bash
cat ~/.ssh/id_ed25519.pub | ssh SEU_USUARIO@IP_DO_ALLY "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. Configurar o deploy

Copie `.env.deploy.example` para `.env.deploy` e preencha `DECK_HOST` e `DECK_USER`.
`.env.deploy` é ignorado pelo git.

### 4. Enviar

```bash
pnpm run deploy:ssh
```

O script compila, empacota, envia por `scp`, instala em `~/homebrew/plugins/steam-system-monitor` com `sudo`
e reinicia o `plugin_loader`. Sem `DECK_SUDO_PASS`, a senha do sudo é pedida no terminal.

Outras opções (`node scripts/bash.mjs scripts/deploy.sh --help`):

| Comando | O que faz |
|---|---|
| `pnpm run deploy:logs` | deploy e acompanha o log do Decky |
| `pnpm run package` | só gera `out/steam-system-monitor.zip` para instalar pelo Decky (Modo desenvolvedor → Instalar plugin de ZIP) |
| `... deploy.sh --skip-build --no-restart` | reenviar sem compilar / sem reiniciar o Decky |

## Licença

BSD-3-Clause
