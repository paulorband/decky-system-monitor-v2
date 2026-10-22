# Spec 009 — Rollback e changelog

- **Status:** Concluída — validada no Ally X; pendente: AC-10 (`deploy.sh --rollback`)
- **Depende de:** 004, 008

## Contexto
Com a auto-atualização (spec 008), uma versão nova com defeito chega rápido ao aparelho. O jogador precisa voltar
para a versão anterior sem computador, e saber o que muda antes de instalar.

## Histórias de usuário
- Como jogador, quero voltar para a versão que eu usava antes, se a nova der problema.
- Como jogador, quero ler as novidades de uma versão antes de instalar.
- Como jogador, quero ver o histórico de versões do plugin.
- Como desenvolvedor, quero um caminho de rollback pelo SSH caso a interface do plugin nem carregue.

## Requisitos funcionais

### Cópia de rollback
- **REQ-700** Antes de aplicar qualquer atualização (spec 008, REQ-635), o backend guarda uma cópia completa da versão
  instalada (itens do `PAYLOAD`) em `<DECKY_PLUGIN_SETTINGS_DIR>/rollback/`. Só existe **uma** cópia: a da versão
  imediatamente anterior. A cópia é montada numa pasta temporária e trocada no fim (nunca fica pela metade).
- **REQ-701** Se a cópia não puder ser gravada, a atualização é **recusada** antes de tocar na instalação (sem
  atualização sem caminho de volta).
- **REQ-702** O deploy por SSH (spec 004) também guarda a versão instalada em `~/homebrew/settings/<pasta>/rollback/`
  antes de substituir.
- **REQ-703** `get_rollback_info()` → `{version, commit, kind}` da cópia, ou `null` se não houver cópia válida
  (`plugin.json` com `name` = `System Monitor`, `main.py`, `dist/index.js`) ou se ela for igual à instalada
  (mesma versão e mesmo commit).

### Restaurar
- **REQ-710** `rollback()` exige confirmação no frontend (`ConfirmModal`); no backend valida a cópia, aplica com a mesma
  troca-com-reversão da spec 008 (REQ-635) em modo **exato** (itens ausentes na cópia são removidos, ex.: um
  `build.json` que a versão antiga não tinha) e reinicia o Decky (REQ-636).
- **REQ-711** O rollback é de uso único: a cópia é apagada após restaurar (não se alterna entre versões).
- **REQ-712** Rollback e instalação compartilham a trava de concorrência (REQ-637) e a checagem de permissão (REQ-638).
- **REQ-713** Após o rollback, a verificação de atualização volta a oferecer a versão mais nova normalmente.
- **REQ-714** Rollback por SSH: `scripts/deploy.sh --rollback` restaura a cópia no aparelho e reinicia o Decky
  (funciona mesmo se a interface do plugin não abrir).

### Changelog
- **REQ-720** `CHANGELOG.md` na raiz, formato *Keep a Changelog* (`## [X.Y.Z] - AAAA-MM-DD`), em português, incluído
  no pacote.
- **REQ-721** O CI publica cada release com as notas = seção da versão no `CHANGELOG.md`; **falha** se a seção não
  existir. O `test-build` traz a lista de commits desde a última tag.
- **REQ-722** O estado de atualização inclui `notes` (corpo da release escolhida, até 8000 caracteres).
- **REQ-723** `get_changelog()` devolve o `CHANGELOG.md` instalado (até 64 KiB).
- **REQ-724 Modal**: "Novidades da vX" (quando há atualização) e "Histórico de versões" abrem um modal com o texto
  em Markdown simples (títulos, listas, negrito, links como texto). Cada bloco é focável para rolar com o D-pad;
  **B** fecha.

## Requisitos não funcionais
- **NFR-1** Sem dependências novas: renderizador de Markdown mínimo próprio.
- **NFR-2** A cópia de rollback ocupa o mesmo que uma instalação (~1–2 MB).

## Critérios de aceite
- [x] **AC-1** `install` cria a cópia com a versão anterior antes de aplicar; falha ao gravar a cópia aborta sem
  alterar a instalação.
- [x] **AC-2** `rollback` restaura exatamente a cópia (inclusive removendo `build.json` extra) e apaga a cópia.
- [x] **AC-3** Cópia inválida, ausente ou igual à instalada → `get_rollback_info()` = `null` e `rollback` recusa.
- [x] **AC-4** Falha no meio do rollback restaura a versão que estava instalada (REQ-635).
- [x] **AC-5** `notes` vem do corpo da release escolhida; `scripts/changelog-section.mjs` extrai a seção certa e falha
  sem ela.
- [x] **AC-6** `pnpm test:py`, `pnpm typecheck`, `pnpm check:i18n` e `pnpm build` passam; textos nos três idiomas.
- [x] **AC-7** `deploy.sh --help` lista `--rollback`; o pacote inclui `CHANGELOG.md`.
- [x] **AC-8** No Ally X aparece "Versão anterior" e o rollback restaura essa versão. _(validado no Ally X em
  2026-10-22 pelo caminho do próprio plugin: atualização v0.3.0 → v0.4.0 guardou a v0.3.0, e o rollback a restaurou)_
- [x] **AC-9** "Histórico de versões" e "Novidades" abrem o modal, rolam com o D-pad e fecham com B. _("Histórico de
  versões" validado no Ally X, 2026-10-22; "Novidades" usa o mesmo modal)_
- [ ] **AC-10** `deploy.sh --rollback` restaura a cópia pelo SSH. _(validar no aparelho)_

## Design
- `updater.py`: `save_rollback()`, `rollback_info()`, `rollback()`, `apply_package(..., exact=)`, `notes` no estado;
  `install(..., rollback_dir=)`.
- `main.py`: `get_rollback_info`, `rollback`, `get_changelog`; pasta `rollback/` em `DECKY_PLUGIN_SETTINGS_DIR`.
- `scripts/remote-install.sh` guarda a cópia; `scripts/remote-rollback.sh` + `deploy.sh --rollback` restauram.
- `scripts/changelog-section.mjs` + `release.yml` (notas da release, `fetch-depth: 0` para a lista de commits).
- Frontend: `ChangelogModal` (Markdown mínimo), botões e confirmação na `UpdateSection`.

## Limitações
- A primeira cópia de rollback criada **pelo próprio plugin** nasce na atualização seguinte à v0.3.0: quem atualiza
  da v0.2.0 usa o código da v0.2.0, que ainda não guardava cópia. O deploy por SSH (REQ-702) cobre isso.
- O changelog é escrito em português; não é traduzido conforme o idioma do plugin.

## Fora de escopo
- Guardar várias versões anteriores ou escolher qual restaurar.
- "Pular esta versão" após um rollback.
