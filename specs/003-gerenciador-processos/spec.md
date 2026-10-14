# Spec 003 — Gerenciador de processos

- **Status:** Concluída — ACs marcados com _(validar no aparelho)_ dependem de teste no Ally X
- **Depende de:** 001, 002

## Contexto
Quando um jogo engasga ou a bateria cai rápido, o jogador quer saber *quem* está consumindo.
Precisamos de uma tela cheia, estilo gerenciador de tarefas, navegável 100% pelo controle.

## Histórias de usuário
- Como jogador, quero ver os processos em execução com uso de CPU e RAM de cada um, em uma tabela.
- Como jogador, quero ordenar por nome, CPU ou RAM, e inverter a ordem.
- Como jogador, quero congelar a lista para conseguir navegar sem que as linhas mudem de lugar.
- Como jogador, quero ver detalhes de um processo (linha de comando, threads, estado).

## Requisitos funcionais
- **FR-1 Backend:** `get_processes(sort_key, descending, limit, include_kernel)` retorna:
  ```jsonc
  { "total": 312, "shown": 40, "cpu_count": 16, "mem_total_mb": 23900,
    "processes": [ { "pid": 4242, "name": "Cyberpunk2077.exe", "cpu": 61.3, "mem_mb": 5120.4,
                     "mem_percent": 21.4, "threads": 87, "state": "R", "ppid": 4100,
                     "cmd": "Z:\\...\\Cyberpunk2077.exe --launcher-skip" } ] }
  ```
  `sort_key ∈ {"name","cpu","mem"}`; `total` conta todos os processos após o filtro de kernel.
- **FR-2 CPU %** = Δ(utime+stime) / (Δtempo × CLK_TCK × nº de CPUs) × 100 — percentual da máquina inteira
  (0–100, como o Gerenciador de Tarefas do Windows). Primeira amostra de um processo retorna 0.
- **FR-3 RAM** = RSS (`/proc/[pid]/stat` campo 24 × tamanho de página), em MB e % da RAM total.
- **FR-4 Nome** = basename de `argv[0]` (aceita `/` e `\` — processos Wine/Proton), senão `comm`.
- **FR-5** Threads de kernel (filhos de `kthreadd`, PID 2) ficam ocultas por padrão.
- **FR-6 Tela:** rota cheia `/steam-system-monitor/processes`, aberta pelo botão do dashboard.
  Tabela com colunas **Processo | PID | CPU | RAM**, cabeçalho fixo e linhas zebradas.
- **FR-7 Ordenação:** cabeçalhos Nome, CPU e RAM são botões; **A** escolhe a coluna e, se já ativa, inverte a ordem.
  Indicador ▲/▼ na coluna ativa. Padrão: CPU decrescente. Nome começa ascendente; CPU/RAM decrescente.
- **FR-8 Atalhos de controle:** **X** alterna a coluna de ordenação; **Y** pausa/retoma a atualização;
  **B** volta ao jogo/tela anterior. Legendas aparecem no rodapé da Steam.
- **FR-9 Detalhes:** **A** sobre uma linha expande linha de comando, PPID, threads e estado.
- **FR-10 Paginação:** 40 linhas iniciais; botão "Mostrar mais" acrescenta 40.
- **FR-11** Botão para mostrar/ocultar processos do kernel.
- **FR-12** Barra de resumo com total de processos, CPU total e RAM usada.

## Requisitos não funcionais
- **NFR-1** Uma leitura de `/proc/[pid]/stat` por processo por amostra; `cmdline` lido uma vez por processo
  (cache por `(pid, starttime)`, limpo quando o processo some).
- **NFR-2** Ordenação e corte no backend → o frontend renderiza no máximo `limit` linhas.
- **NFR-3** Atualização a cada 2 s, só enquanto a tela está aberta.
- **NFR-4** Linhas indexadas por PID para o foco acompanhar o processo quando a ordem muda.
- **NFR-5** Não requer root: só lê arquivos públicos de `/proc`.

## Critérios de aceite
- [x] **AC-1** Dadas duas amostras, CPU % segue FR-2 (teste com `/proc` falso).
- [x] **AC-2** Processo Wine com `argv[0]="C:\\Games\\game.exe"` aparece como `game.exe`.
- [x] **AC-3** Com `include_kernel=False`, filhos do PID 2 não aparecem e `total` não os conta.
- [x] **AC-4** Ordenação por nome (case-insensitive), CPU e RAM, nas duas direções, respeitando `limit`.
- [x] **AC-5** Processo que some entre amostras não gera erro e sai do cache.
- [ ] **AC-6** Na tela, D-pad navega cabeçalho → linhas → "Mostrar mais"; A no cabeçalho ordena/inverte. _(validar no aparelho)_
- [ ] **AC-7** X alterna coluna, Y pausa, B volta. _(validar no aparelho)_
- [x] **AC-8** `pnpm test:py`, `pnpm typecheck` e `pnpm build` passam.

## Design
- `py_modules/sysmon/processes.py` — `ProcessSampler(root="/")` com estado da amostra anterior
  `{(pid, starttime): ticks}` e cache de nomes.
- `main.py` — `async get_processes(...)`.
- `src/views/ProcessManager.tsx` — tela; `src/components/ProcessTable.tsx` — cabeçalho e linhas.
- `src/index.tsx` — registra a rota com `routerHook.addRoute` e remove em `onDismount`.
- Atalhos X/Y via `onSecondaryButton`/`onOptionsButton` do `Focusable` raiz (eventos sobem do item focado).

## Tarefas
- [x] T1 Amostrador de processos (FR-1..FR-5, NFR-1, NFR-2)
- [x] T2 Testes do amostrador (AC-1..AC-5)
- [x] T3 Rota e tela (FR-6, FR-12)
- [x] T4 Cabeçalho ordenável + atalhos (FR-7, FR-8)
- [x] T5 Linhas expansíveis e paginação (FR-9..FR-11)
- [x] T6 Build/typecheck/testes (AC-8)

## Fora de escopo
- Encerrar processos (exigiria root e confirmação; avaliar em spec futura).
- Árvore de processos / agrupamento por aplicativo.
