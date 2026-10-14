# Constituição do projeto

Princípios não negociáveis. Toda spec e todo PR são avaliados contra eles.

## I. Leveza acima de tudo
O monitor não pode roubar desempenho do jogo.
- Backend em **Python stdlib** apenas (sem `psutil` ou dependências nativas): lê `/proc` e `/sys` diretamente.
- Coleta **sob demanda**: o backend só trabalha quando o frontend pede; nada de threads de fundo.
- O frontend só faz polling enquanto a tela está visível e com intervalo configurável (padrão 1 s para o resumo, 2 s para processos).
- Custo alvo de uma coleta de resumo: < 5 ms de CPU; lista de processos: < 30 ms.
- Sem bibliotecas de gráficos: sparklines em SVG puro.

## II. Controle primeiro (100% gamepad)
- Todo conteúdo relevante deve ser alcançável com D-pad/analógico; elementos são `Focusable` para que o scroll siga o foco.
- Ações têm botão físico e legenda no rodapé (A, B, X, Y) — nada depende de toque ou mouse.
- Foco sempre visível (realce de borda) e ordem de navegação previsível (de cima para baixo, esquerda para direita).
- **B** sempre volta / fecha.

## III. Multi-distro, degradação graciosa
Alvos: SteamOS (Steam Deck LCD/OLED), Bazzite e CachyOS Handheld (ROG Ally / Ally X, Legion Go, etc.).
- Nunca assumir nomes de dispositivos fixos: descobrir sensores por `hwmon/name`, `power_supply/type`, `drm/card*/device/vendor`.
- Métrica indisponível = `null` no contrato e "—" na UI. Nunca quebrar a tela por falta de um sensor.
- Não exigir root (`flags: []`): apenas leitura de arquivos públicos de `/proc` e `/sys`.

## IV. Legibilidade das métricas
- Números grandes para o valor principal, rótulo curto, unidade explícita.
- Cores semânticas consistentes por faixa: verde (< 60%), amarelo (60–85%), vermelho (> 85%); temperaturas: < 70 °C, 70–85 °C, > 85 °C.
- Barras e sparklines para tendência; nunca só cor (sempre acompanhada de número).

## V. Qualidade verificável
- Lógica de parsing no backend é testável com uma raiz falsa de `/proc`/`/sys` (`tests/fakefs.py`).
- `pnpm build` e `pnpm typecheck` devem passar antes de cada commit.
- Um commit por spec concluída.
