# Spec 000 — Fundação do projeto e processo

- **Status:** Concluída
- **Depende de:** —

## Contexto
Precisamos de um esqueleto de plugin Decky Loader funcional e de um processo (SDD) que guie
as próximas funcionalidades.

## Histórias de usuário
- Como desenvolvedor, quero um projeto que compile num bundle Decky válido, para iterar rápido.
- Como desenvolvedor, quero um processo de especificação claro, para que cada funcionalidade tenha critérios de aceite.

## Requisitos funcionais
- **FR-1** Estrutura padrão Decky (API v1): `plugin.json`, `package.json`, `main.py`, `src/index.tsx`, `rollup.config.js`, `tsconfig.json`.
- **FR-2** Build com `pnpm build` gera `dist/index.js` usando `@decky/rollup`.
- **FR-3** Backend Python organizado em pacote `py_modules/sysmon` (Decky adiciona `py_modules` ao `sys.path`).
- **FR-4** Documentação do processo SDD (`specs/README.md`, `_template.md`, `constitution.md`) e `CLAUDE.md`.

## Requisitos não funcionais
- **NFR-1** Sem dependências de runtime além de `@decky/api`, `react-icons` e `tslib`.
- **NFR-2** Plugin não requer root (`flags: []`).

## Critérios de aceite
- [x] **AC-1** `pnpm install && pnpm build` gera `dist/index.js` sem erros.
- [x] **AC-2** `pnpm typecheck` passa.
- [x] **AC-3** `specs/` contém processo, template e constituição.

## Design
- Plugin `api_version: 1` → frontend usa `definePlugin`/`callable` de `@decky/api`; backend expõe `class Plugin` com métodos `async`.
- `main.py` é fino: apenas delega para `sysmon`.
- Testes Python com `unittest` (stdlib) rodados via `uv` (`pnpm test:py`) para não exigir Python instalado no Windows.

## Tarefas
- [x] T1 Configuração de build e dependências (FR-1, FR-2, AC-1)
- [x] T2 Esqueleto `main.py` + `src/index.tsx` (FR-1, FR-3)
- [x] T3 Documentos SDD + CLAUDE.md (FR-4, AC-3)

## Fora de escopo
- Funcionalidades de monitoramento (specs 001+).
