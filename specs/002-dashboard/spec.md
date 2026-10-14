# Spec 002 — Dashboard de resumo (Quick Access Menu)

- **Status:** Concluída — validada no Ally X; pendentes: AC-4 (hardware sem GPU/bateria) e AC-5 (persistência após reiniciar o Steam)
- **Depende de:** 001

## Contexto
A tela principal fica no painel do plugin no Quick Access Menu (botão `…`), acessível por cima do jogo.
Ela deve mostrar o estado do sistema de relance e permitir aprofundar sem sair do jogo.

## Histórias de usuário
- Como jogador, quero ver CPU, GPU, RAM e bateria em um relance, com cores que indiquem se algo está no limite.
- Como jogador, quero ver a tendência recente (último minuto) de CPU e GPU.
- Como jogador, quero expandir um cartão para ver detalhes (núcleos, VRAM, saúde da bateria) só quando eu quiser.
- Como jogador, quero ajustar a frequência de atualização para economizar recursos.
- Como jogador, quero abrir o gerenciador de processos a partir do resumo.

## Requisitos funcionais
- **FR-1 Faixa de resumo:** 4 blocos no topo — CPU %, GPU %, RAM %, Bateria % — com cor semântica.
- **FR-2 Cartão CPU:** uso %, temperatura, frequência média, barra e sparkline; expandido: barras por núcleo, load average e modelo.
- **FR-3 Cartão GPU:** uso %, temperatura, clock, potência (APU W), barra e sparkline; expandido: VRAM e GTT com barras.
- **FR-4 Cartão Memória:** usado/total em GB, %, barra; swap com barra própria.
- **FR-5 Cartão Bateria:** %, status traduzido, potência (W) e tempo estimado; expandido: saúde.
- **FR-6 Cartão Ventoinhas:** RPM de cada ventoinha (oculto se não houver).
- **FR-7** Botão "Gerenciador de processos" no topo que navega para a tela da spec 003 e fecha o QAM.
- **FR-8 Configuração:** intervalo de atualização (0,5 s / 1 s / 2 s / 5 s), persistido no aparelho (`localStorage`).
- **FR-9** Histórico de 60 amostras por métrica mantido em memória enquanto o plugin estiver carregado.
- **FR-10** Métrica `null` aparece como "—"; cartões de hardware ausente (GPU, bateria, ventoinhas) são ocultados.

## Requisitos não funcionais
- **NFR-1** Polling só enquanto o QAM está visível (`useQuickAccessVisible`), sem chamadas sobrepostas (cadeia de `setTimeout`).
- **NFR-2 Controle:** cada cartão é `Focusable`; **A** expande/recolhe (legenda "Detalhes"); foco destacado por borda.
  O scroll do painel acompanha o foco, então todo cartão é alcançável pelo D-pad.
- **NFR-3** Sem bibliotecas de gráfico; sparkline é um `<svg>` com `polyline`.
- **NFR-4** Cores: verde < 60%, amarelo 60–85%, vermelho > 85%; temperaturas < 70 / 70–85 / > 85 °C.

## Critérios de aceite
- [x] **AC-1** Ao abrir o QAM, os valores aparecem em até 1 intervalo e atualizam periodicamente. _(validado no Ally X, 2026-10-14)_
- [x] **AC-2** Fechando o QAM, nenhuma chamada `get_metrics` é feita (o hook depende de `visible`).
- [x] **AC-3** Com o D-pad é possível focar cada cartão em sequência; **A** alterna detalhes. _(validado no Ally X, 2026-10-14)_
- [ ] **AC-4** Em hardware sem bateria/GPU os cartões correspondentes não aparecem e nada quebra. _(validar no aparelho)_
- [ ] **AC-5** O intervalo escolhido persiste após reiniciar o Steam. _(validar no aparelho)_
- [x] **AC-6** `pnpm typecheck` e `pnpm build` passam.

## Design
- `src/api.ts` — tipos do contrato da spec 001 e `callable`s.
- `src/hooks/usePolling.ts` — polling encadeado, pausável.
- `src/store.ts` — histórico em memória (ring buffer de 60) fora do React.
- `src/settings.ts` — leitura/escrita do intervalo em `localStorage`.
- `src/format.ts` — formatação (%, GB, MHz, W, tempo) e cores semânticas.
- `src/components/` — `Bar`, `Sparkline`, `MetricCard`, `SummaryStrip`.
- `src/styles.ts` — CSS escopado com prefixo `ssm-`.
- `src/views/Dashboard.tsx` — composição.

## Tarefas
- [x] T1 Tipos e chamadas da API (FR-1..FR-6)
- [x] T2 Hook de polling + store de histórico (FR-9, NFR-1)
- [x] T3 Componentes visuais (NFR-3, NFR-4)
- [x] T4 Cartões e faixa de resumo (FR-1..FR-6, FR-10)
- [x] T5 Navegação para processos e configuração (FR-7, FR-8)
- [x] T6 Build e typecheck (AC-6)

## Fora de escopo
- Overlay permanente durante o jogo (isso é papel do MangoHud / overlay de desempenho da Steam).
