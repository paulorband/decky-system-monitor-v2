# steam-system-monitor

Plugin Decky Loader: monitor de recursos + gerenciador de processos para o Game Mode
(SteamOS, Bazzite, CachyOS Handheld). Aparelho de teste: ROG Xbox Ally X com Bazzite.

## Processo
Spec Driven Development — leia `specs/README.md` e `specs/constitution.md` antes de mudar comportamento.
Nova funcionalidade = nova spec em `specs/NNN-nome/spec.md`; um commit por spec concluída.

## Comandos
- `pnpm build` — bundle do frontend em `dist/`
- `pnpm typecheck` — checagem TypeScript
- `pnpm test:py` — testes do backend (fixtures de `/proc` e `/sys` em `tests/fixtures`)
- `pnpm deploy` — build + envio via SSH (config em `.env.deploy`, veja `.env.deploy.example`)

## Estrutura
- `main.py` — entrada do backend Decky (fino, delega para `py_modules/sysmon`)
- `py_modules/sysmon/` — coleta de métricas e processos (stdlib apenas)
- `src/` — frontend React (`@decky/ui`, `@decky/api`)
- `scripts/deploy.sh` — empacotamento e deploy SSH
