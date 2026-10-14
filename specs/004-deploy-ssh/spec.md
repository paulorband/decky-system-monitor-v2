# Spec 004 — Deploy via SSH

- **Status:** Concluída — deploy validado no Ally X; pendente: AC-5 (`--logs`)
- **Depende de:** 000

## Contexto
O desenvolvimento acontece no Windows e o plugin roda no ROG Xbox Ally X com Bazzite (ou Steam Deck / CachyOS).
Precisamos de um comando único que compile, envie e recarregue o plugin no aparelho.

## Histórias de usuário
- Como desenvolvedor, quero rodar um comando e ver a nova versão no aparelho em segundos.
- Como desenvolvedor, quero gerar um `.zip` para instalar manualmente pelo Decky (modo desenvolvedor → instalar de ZIP).

## Requisitos funcionais
- **FR-1** `scripts/deploy.sh` (bash) executa: build → empacota → `scp` → instala com `sudo` → reinicia `plugin_loader`.
- **FR-2** Configuração por `.env.deploy` (ignorado pelo git) com `DECK_HOST`, `DECK_USER`, `DECK_PORT`, `DECK_KEY`,
  `DECK_SUDO_PASS` (opcional); variáveis de ambiente e flags sobrescrevem o arquivo. Exemplo em `.env.deploy.example`.
- **FR-3** Pacote contém apenas o necessário: `dist/index.js`, `main.py`, `plugin.json`, `package.json`, `LICENSE`,
  `README.md` e `py_modules/` (sem `__pycache__`).
- **FR-4** Instalação remota em `$HOME/homebrew/plugins/<nome>` (resolvido como o usuário, antes do `sudo`),
  substituindo a versão anterior, com permissões de leitura para todos.
- **FR-5** Flags: `--package-only` (gera `out/<nome>.zip`, sem SSH), `--skip-build`, `--no-restart`,
  `--logs` (acompanha `journalctl -u plugin_loader` após o deploy), `--host`, `--user`, `-h/--help`.
- **FR-6** Sem `DECK_SUDO_PASS`, o `sudo` pede senha interativamente (`ssh -t`); com ela, usa `sudo -S` via stdin
  (nunca em argumentos de linha de comando).
- **FR-7** Funciona no Windows (Git Bash) e no Linux/macOS: `pnpm run deploy:ssh` usa `scripts/bash.mjs`, que localiza o
  Git Bash no Windows (o `bash` do PATH costuma ser o WSL).

## Requisitos não funcionais
- **NFR-1** Falha cedo (`set -euo pipefail`) com mensagens claras (host ausente, build falhou, SSH falhou).
- **NFR-2** Uma única conexão interativa para `sudo` (instalação + restart no mesmo script remoto).

## Critérios de aceite
- [x] **AC-1** `pnpm run package` gera `out/steam-system-monitor.zip` contendo a pasta do plugin.
- [x] **AC-2** Sem `DECK_HOST`, o deploy aborta com mensagem orientando a criar `.env.deploy`.
- [x] **AC-3** `--help` lista as opções.
- [x] **AC-4** `pnpm run deploy:ssh` instala no Ally X e o plugin aparece no QAM após o restart. _(validado no Ally X, 2026-10-14)_
- [ ] **AC-5** `--logs` mostra o log do Decky. _(validar no aparelho)_

## Design
- `scripts/deploy.sh` — orquestra local; `scripts/remote-install.sh` — enviado junto e executado com `sudo` no aparelho.
- `scripts/bash.mjs` — launcher multiplataforma do bash.
- Staging em `out/<nome>/`; tarball para envio; zip via `zip`, `tar.exe -a` (Windows) ou `Compress-Archive`.

## Tarefas
- [x] T1 Script local com config e flags (FR-1, FR-2, FR-5, AC-2, AC-3)
- [x] T2 Empacotamento e zip (FR-3, AC-1)
- [x] T3 Instalação remota + restart (FR-4, FR-6, NFR-2)
- [x] T4 Launcher Windows (FR-7)
- [x] T5 README com passo a passo do Bazzite (SSH, chave, Decky dev mode)

## Fora de escopo
- Publicação na loja do Decky; CI.
