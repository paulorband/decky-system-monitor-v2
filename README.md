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
| **A** num grupo (`steamwebhelper ×8`) ou jogo | mostra os processos do grupo |
| **A** na linha | mostra linha de comando, PPID, threads e estado |
| Botão de agrupamento | alterna **Agrupar: jogos** (padrão: todos os processos de um jogo — `.exe`, wineserver, xalia… — numa linha com selo JOGO e o nome da Steam) → **Agrupar: nome** → **Sem grupos** |
| **B** | volta |

CPU % de um processo é relativo à máquina inteira (100% = todos os núcleos ocupados), como no Gerenciador de Tarefas do Windows.

## Atualizações

O plugin verifica as [releases do GitHub](https://github.com/paulorband/decky-system-monitor-v2/releases) ao iniciar
e avisa com uma notificação quando há versão nova. Em **Atualizações** (fim do painel) dá para verificar e instalar
pelo controle; o Decky reinicia sozinho para carregar a nova versão.

- A instalação confere origem, SHA-256 do arquivo e conteúdo do zip, e restaura a versão anterior se algo falhar.
- **Incluir builds de teste** (desligado por padrão) oferece o build automático do último commit — pode conter erros.
- Por isso o backend roda como root (`flags: ["root"]`): a pasta `~/homebrew/plugins` pertence ao root.

**Publicar uma versão:** atualize `version` no `package.json`, faça o commit e envie a tag correspondente:

```bash
git tag v0.2.0
```

```bash
git push origin main --tags
```

O workflow `.github/workflows/release.yml` testa, empacota e publica `steam-system-monitor.zip` (a tag precisa ser
igual a `v` + versão do `package.json`). Cada push em `main` também atualiza o pré-release `test-build`.

## Idiomas

Português do Brasil, Inglês e Espanhol. Por padrão o plugin segue o idioma da Steam (inglês se não for suportado);
dá para escolher outro em **Configurações → Idioma** no painel.

**Adicionar um idioma:** copie `src/locales/en.json` para `src/locales/<código>.json` (ex.: `fr.json`), traduza os
valores e ajuste o `_meta`:

```jsonc
"_meta": { "name": "Français", "steamLanguages": ["french"] }   // nome nativo + idiomas da Steam correspondentes
```

O build inclui o arquivo automaticamente. Valide com:

```bash
pnpm check:i18n
```

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

GPL-3.0-or-later — veja [LICENSE](LICENSE).
