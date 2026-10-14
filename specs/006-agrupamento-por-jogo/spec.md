# Spec 006 — Agrupamento de processos por jogo (AppID)

- **Status:** Concluída — validada no Ally X
- **Depende de:** 005

## Contexto
Um jogo rodando pelo Proton não é um processo só: há o `.exe` do jogo, `wineserver`, `services.exe`,
`explorer.exe`, `xalia.exe`, `reaper`, `pressure-vessel`… (visto no Ally X com God of War Ragnarök).
Agrupando só pelo nome (spec 005), o consumo do jogo fica espalhado pela lista.

## Histórias de usuário
- Como jogador, quero ver o jogo em execução como uma única linha "God of War Ragnarök" com CPU e RAM de todos os seus processos.
- Como jogador, quero expandir o jogo e ver os processos que o compõem.
- Como jogador, quero escolher entre agrupar por jogo, só por nome, ou não agrupar.

## Requisitos funcionais
- **FR-1 Detecção do AppID** de cada processo, nesta ordem:
  1. ambiente (`/proc/<pid>/environ`): `SteamAppId` ≠ 0, senão `STEAM_COMPAT_APP_ID` ≠ 0, senão `SteamGameId` ≠ 0;
  2. linha de comando `… AppId=<n> …` (processo `reaper SteamLaunch AppId=<n>`);
  3. herdado do processo pai mais próximo que tenha AppID (cobre filhos cujo ambiente não pode ser lido).
  Ambiente ilegível (outro usuário) não é erro: segue para os passos seguintes.
- **FR-2 Nome do jogo**: `name` do `appmanifest_<id>.acf` em qualquer biblioteca listada em
  `<steam>/steamapps/libraryfolders.vdf` (Steam em `~/.local/share/Steam` ou `~/.steam/steam`).
  AppID não encontrado (atalhos não-Steam, IDs de 64 bits) → nome do processo com mais RAM do grupo.
- **FR-3** `get_processes(..., group)` aceita `group ∈ {"app", "name", "none"}`; `true`/`false` continuam valendo
  como `"name"`/`"none"` (compatível com a spec 005).
- **FR-4 Modo `"app"`**: processos com AppID formam um item por jogo; os demais são agrupados por nome (spec 005).
- **FR-5 Item de jogo**: `key = "app:<id>"`, `kind = "game"`, `app_id`, `name` = nome do jogo, `count`, CPU/RAM/threads
  somados, campos `pid/cmd/state/ppid` do processo com mais RAM, `members` (até 50) por CPU desc.
  Itens recebem `kind ∈ {"game","group","process"}` e `app_id` (ou `null`) em todos os modos.
- **FR-6 Tela**: o botão de agrupamento alterna entre "Agrupar: jogos" → "Agrupar: nome" → "Sem grupos";
  padrão **jogos**; preferência persistida.
- **FR-7** Linha de jogo tem selo "JOGO" (cor de destaque) além de `×N`; **A** expande os processos do jogo.

## Requisitos não funcionais
- **NFR-1** `environ` e `cmdline` lidos uma vez por processo (cache por `(pid, starttime)`); leitura de `environ`
  limitada a 64 KiB.
- **NFR-2** Manifestos lidos uma vez por AppID (cache, inclusive de "não encontrado"); `libraryfolders.vdf` lido
  uma vez por instância.
- **NFR-3** Somente stdlib; parsing de VDF por regex (só precisamos de `path` e `name`).

## Critérios de aceite
- [x] **AC-1** Processos com `SteamAppId=2322010` (ambiente), `reaper … AppId=2322010` (cmdline) e um filho sem
  ambiente legível formam um único item `app:2322010` com o nome do manifesto e uso somado.
- [x] **AC-2** O manifesto é encontrado numa segunda biblioteca listada em `libraryfolders.vdf`.
- [x] **AC-3** Atalho não-Steam (`SteamAppId=0`, `SteamGameId` de 64 bits) vira um item de jogo com o nome do
  processo de maior RAM.
- [x] **AC-4** Processos sem AppID continuam agrupados por nome no modo `"app"`.
- [x] **AC-5** `group=True` ≡ `"name"`, `group=False` ≡ `"none"`; itens trazem `kind` e `app_id`.
- [x] **AC-6** `pnpm test:py`, `pnpm typecheck` e `pnpm build` passam.
- [x] **AC-7** No Ally X, com um jogo aberto, ele aparece como uma linha com selo JOGO e expande para seus processos. _(validado no Ally X com God of War Ragnarök: 17 processos, 2026-10-14)_
- [x] **AC-8** O botão alterna os três modos e a escolha persiste. _(validado no Ally X, persiste após reiniciar o aparelho, 2026-10-14)_

## Design
- `py_modules/sysmon/steamapps.py` — `SteamLibrary(root, steam_dirs)` com `game_name(app_id)`.
- `processes.py` — cache por processo passa a guardar `(nome, cmd, app_id próprio)`; após a varredura, AppIDs ausentes
  são resolvidos subindo pela cadeia de `ppid`; `_group_by_app()` antes do agrupamento por nome.
- `main.py` passa `decky.DECKY_USER_HOME` para localizar a Steam.
- Frontend: `GroupMode = "app" | "name" | "none"`, chave de preferência `procGroupMode`.

## Tarefas
- [x] T1 Leitura de bibliotecas/manifestos (FR-2, NFR-2)
- [x] T2 Detecção e herança de AppID (FR-1, NFR-1)
- [x] T3 Agrupamento por jogo + compatibilidade de `group` (FR-3..FR-5)
- [x] T4 Testes (AC-1..AC-5)
- [x] T5 UI: botão de modo, selo JOGO (FR-6, FR-7)
- [x] T6 Build/typecheck/testes (AC-6)

## Fora de escopo
- Nome de atalhos não-Steam via `shortcuts.vdf` (formato binário).
- Fixar o jogo no topo da lista independentemente da ordenação.
