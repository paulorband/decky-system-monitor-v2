# steam-system-monitor

Plugin Decky Loader: monitor de recursos + gerenciador de processos para o Game Mode
(SteamOS, Bazzite, CachyOS Handheld). Aparelho de teste: ROG Xbox Ally X com Bazzite.

## Processo
Spec Driven Development — leia `specs/README.md` e `specs/constitution.md` antes de mudar comportamento.
Nova funcionalidade = nova spec em `specs/NNN-nome/spec.md`; um commit por spec concluída.

## Comandos
- `pnpm build` — bundle do frontend em `dist/`
- `pnpm typecheck` — checagem TypeScript
- `pnpm test:py` — testes do backend (raiz `/proc`/`/sys` falsa gerada por `tests/fakefs.py`)
- `pnpm run deploy:ssh` — build + envio via SSH + restart do Decky (config em `.env.deploy`, veja `.env.deploy.example`)
- `pnpm run package` — gera `out/steam-system-monitor.zip` para instalar manualmente

## Estrutura
- `main.py` — entrada do backend Decky (fino, delega para `py_modules/sysmon`)
- `py_modules/sysmon/` — coleta de métricas e processos (stdlib apenas)
- `src/` — frontend React (`@decky/ui`, `@decky/api`)
- `scripts/deploy.sh` — empacotamento e deploy SSH (`scripts/bash.mjs` acha o Git Bash no Windows; o `bash` do PATH é o WSL)
