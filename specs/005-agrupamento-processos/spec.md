# Spec 005 — Agrupamento de processos

- **Status:** Concluída — AC-5/AC-6 dependem de teste no Ally X
- **Depende de:** 003

## Contexto
No aparelho, a lista fica poluída com várias instâncias do mesmo programa (ex.: 8× `steamwebhelper`),
o que esconde quem realmente consome recursos e exige muita rolagem com o D-pad.

## Histórias de usuário
- Como jogador, quero ver processos com o mesmo nome agrupados em uma linha com CPU e RAM somados.
- Como jogador, quero expandir um grupo para ver cada instância.
- Como jogador, quero poder desligar o agrupamento e ver a lista plana.

## Requisitos funcionais
- **FR-1** `get_processes(sort_key, descending, limit, include_kernel, group)` ganha o parâmetro `group`.
- **FR-2** Cada item da resposta tem o formato abaixo — com ou sem agrupamento, para que o frontend use um único
  componente:
  ```jsonc
  { "key": "name:steamwebhelper",      // "pid:<pid>" quando não agrupado
    "name": "steamwebhelper", "count": 8,
    "pid": 13041,                      // instância principal (menor PID)
    "cpu": 3.4, "mem_mb": 912.0, "mem_percent": 3.8, "threads": 140,
    "state": "S", "ppid": 1300, "cmd": "...",   // da instância principal
    "members": [ /* processos (formato da spec 003), por CPU desc; vazio se count = 1; até 50 */ ] }
  ```
- **FR-3** Agrupamento pela chave `name` (spec 003, FR-4). CPU, RAM, % de RAM e threads são somados.
- **FR-4** Ordenação e `limit` se aplicam aos grupos. A resposta inclui `total` (itens após agrupar) e
  `process_count` (processos individuais).
- **FR-5 Tela:** botão "Agrupar" / "Desagrupar" na barra de ferramentas; preferência persistida; **ligado por padrão**.
- **FR-6** Linha de grupo mostra o selo `×N` ao lado do nome e "N proc." na coluna PID.
  **A** expande as instâncias como sub-linhas recuadas e focáveis; **A** numa sub-linha mostra os detalhes dela.
- **FR-7** Resumo do topo mostra o número de processos e, quando agrupado, o de grupos.

## Requisitos não funcionais
- **NFR-1** Agrupamento no backend: o frontend continua renderizando no máximo `limit` linhas principais.
- **NFR-2** O estado expandido usa a `key` do item, então permanece aberto quando a ordem muda.

## Critérios de aceite
- [x] **AC-1** Três processos `steamwebhelper` viram um item `count=3` com CPU/RAM somados e `pid` = menor PID.
- [x] **AC-2** Processo único agrupado tem `count=1` e `members` vazio.
- [x] **AC-3** Ordenação por CPU/RAM/nome considera os valores do grupo; `limit` corta grupos.
- [x] **AC-4** `group=False` mantém a lista plana, com `key` igual a `pid:<pid>`.
- [ ] **AC-5** Na tela, o grupo expande/recolhe com A e as sub-linhas são navegáveis pelo D-pad. _(validar no aparelho)_
- [ ] **AC-6** A preferência "Agrupar" persiste entre aberturas da tela. _(validar no aparelho)_
- [x] **AC-7** `pnpm test:py`, `pnpm typecheck` e `pnpm build` passam.

## Design
- `ProcessSampler.sample(..., group)` monta as linhas como antes e depois aplica `_group()` ou `_single()`
  antes de ordenar.
- `ProcessTable.tsx`: `ProcessRow` recebe um item; `MemberRow` mostra as instâncias.

## Tarefas
- [x] T1 Agrupamento no backend (FR-1..FR-4)
- [x] T2 Testes (AC-1..AC-4)
- [x] T3 UI: toggle, selo, sub-linhas (FR-5..FR-7)
- [x] T4 Build/typecheck/testes (AC-7)

## Fora de escopo
- Agrupar por jogo/AppID da Steam (todos os processos do Proton de um jogo); é candidato a spec futura.
