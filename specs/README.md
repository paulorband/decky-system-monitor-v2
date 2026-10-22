# Spec Driven Development

Todo comportamento do plugin nasce de uma spec. Código sem spec correspondente não entra.

## Fluxo

1. **Especificar** — criar `specs/NNN-nome/spec.md` a partir de [`_template.md`](_template.md):
   contexto, histórias de usuário, requisitos funcionais (`FR-x`), não funcionais (`NFR-x`)
   e critérios de aceite (`AC-x`) verificáveis.
2. **Planejar** — preencher a seção *Design* da spec (arquivos, contratos, decisões).
3. **Tarefas** — quebrar em checklist na seção *Tarefas*.
4. **Implementar** — cada tarefa referencia os `FR`/`AC` que atende.
5. **Verificar** — marcar cada `AC` como verificado (teste automatizado, build ou checagem no aparelho).
6. **Concluir** — status `Concluída` e **um commit por spec**: `feat(spec-NNN): <resumo>`.

Toda spec deve respeitar a [constituição](constitution.md).

## Índice

| Spec | Título | Status |
|------|--------|--------|
| [000](000-fundacao/spec.md) | Fundação do projeto e processo | Concluída |
| [001](001-coletor-metricas/spec.md) | Coletor de métricas (backend) | Concluída |
| [002](002-dashboard/spec.md) | Dashboard de resumo (QAM) | Concluída |
| [003](003-gerenciador-processos/spec.md) | Gerenciador de processos | Concluída |
| [004](004-deploy-ssh/spec.md) | Deploy via SSH | Concluída |
| [005](005-agrupamento-processos/spec.md) | Agrupamento de processos | Concluída |
| [006](006-agrupamento-por-jogo/spec.md) | Agrupamento por jogo (AppID) | Concluída |
| [007](007-multi-idioma/spec.md) | Multi-idioma | Concluída |
| [008](008-auto-atualizacao/spec.md) | Atualização automática | Concluída |
| [009](009-rollback-changelog/spec.md) | Rollback e changelog | Concluída |
