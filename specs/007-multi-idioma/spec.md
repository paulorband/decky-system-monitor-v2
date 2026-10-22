# Spec 007 — Multi-idioma

- **Status:** Concluída — validada no Ally X
- **Depende de:** 002, 003, 005, 006

## Contexto
A interface foi escrita direto em português. Para outros jogadores, o plugin deve seguir o idioma da Steam
e permitir trocar manualmente. Adicionar um idioma novo deve exigir só um arquivo de tradução.

## Histórias de usuário
- Como jogador, quero que o plugin já abra no idioma da minha Steam.
- Como jogador, quero escolher o idioma do plugin manualmente.
- Como colaborador, quero adicionar um idioma criando apenas um arquivo JSON.

## Requisitos funcionais
- **FR-1** Idiomas iniciais: Português do Brasil (`pt-BR`), Inglês (`en`) e Espanhol (`es`).
- **FR-2** Cada idioma é um arquivo `src/locales/<código>.json` com chaves planas (`"proc.title": "Processos"`) e um
  bloco `_meta`:
  ```jsonc
  { "_meta": { "name": "Português (Brasil)",          // nome nativo, exibido no seletor
               "steamLanguages": ["brazilian", "portuguese"] },  // idiomas da Steam que mapeiam para este arquivo
    "dashboard.settings": "Configurações", ... }
  ```
  O build inclui **automaticamente** todo `*.json` dessa pasta (módulo virtual `virtual:locales`); nenhum código
  muda ao adicionar um idioma.
- **FR-3 Idioma automático**: lê o idioma da Steam (`SteamClient.Settings.GetCurrentLanguage()`, senão
  `LocalizationManager.m_rgLocalesToUse[0]`, senão `navigator.language`) e escolhe o arquivo cujo
  `_meta.steamLanguages` o contém (ou cujo código bate com o prefixo de `navigator.language`).
  Sem correspondência → **inglês**.
- **FR-4 Seletor** em Configurações: "Automático (Steam)" + cada idioma pelo nome nativo; padrão Automático;
  persistido; a troca aplica na hora, inclusive na tela de processos.
- **FR-5** Chave ausente num idioma usa o texto em inglês; ausente também em inglês → a própria chave.
- **FR-6** Parâmetros por `{nome}` (`"proc.more": "Mostrar mais ({count} restantes)"`).
- **FR-7** Números seguem o idioma (`Intl.NumberFormat`): `0,5 s` / `1,2 GB` em pt-BR/es, `0.5 s` / `1.2 GB` em en.
- **FR-8** Siglas técnicas (CPU, GPU, RAM, VRAM, GTT, APU, PID, RPM, Swap) ficam no código, sem tradução.
- **FR-9** `pnpm check:i18n` compara cada idioma com `en.json` e falha se faltar chave, sobrar chave,
  faltar `_meta` ou um `{parâmetro}` diferir.

## Requisitos não funcionais
- **NFR-1** Sem bibliotecas de i18n: ~60 linhas próprias (store + hook `useI18n`).
- **NFR-2** Traduções embutidas no bundle (sem requisições em tempo de execução); o bundle cresce poucos KB.
- **NFR-3** Formatadores `Intl` em cache por idioma/casas decimais.

## Critérios de aceite
- [x] **AC-1** `pnpm build` inclui os três idiomas; um quarto `xx.json` entraria sem mudar código (plugin do rollup lê a pasta).
- [x] **AC-2** `pnpm check:i18n` passa para pt-BR, en e es e falha se uma chave for removida de um deles.
- [x] **AC-3** Nenhum texto de interface em português permanece fixo nos componentes (`src/**/*.tsx`, `format.ts`).
- [x] **AC-4** Steam em `brazilian` → pt-BR; `latam`/`spanish` → es; `german` → en (lógica de `matchLanguage`).
- [x] **AC-5** `pnpm typecheck` e `pnpm build` passam.
- [x] **AC-6** No Ally X, com a Steam em português, o plugin abre em pt-BR; mudando para inglês no seletor, painel e
  tela de processos mudam na hora. _(validado no Ally X, 2026-10-14)_
- [x] **AC-7** A escolha de idioma persiste após reiniciar. _(validado no Ally X, 2026-10-21)_

## Design
- `rollup.config.js` — plugin `ssm-locales` resolve `virtual:locales` lendo `src/locales/*.json` (com watch).
- `src/i18n-match.ts` — `matchLanguage()` puro (sem imports), testado pelo `check-locales.mjs` via Node.
- `src/i18n.ts` — `initI18n()` (chamado no `definePlugin`), `setLanguagePreference()`, `t()`, `useI18n()`,
  `fmtNumber()`.
- `src/format.ts` — usa `fmtNumber` e `t` para status de bateria e ventoinhas.
- `scripts/check-locales.mjs` — validação de FR-9.

## Tarefas
- [x] T1 Plugin rollup + tipos do módulo virtual (FR-2)
- [x] T2 Runtime de i18n e detecção da Steam (FR-3, FR-5, FR-6, FR-7)
- [x] T3 Extrair textos para `en`, `pt-BR`, `es` (FR-1, FR-8, AC-3)
- [x] T4 Seletor de idioma (FR-4)
- [x] T5 Script de verificação (FR-9, AC-2)
- [x] T6 Build/typecheck (AC-5)

## Fora de escopo
- Traduzir mensagens de erro vindas do backend (são técnicas e raras).
- Idiomas da direita para a esquerda.
