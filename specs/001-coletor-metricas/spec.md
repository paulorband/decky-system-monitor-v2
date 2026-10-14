# Spec 001 — Coletor de métricas (backend)

- **Status:** Concluída
- **Depende de:** 000

## Contexto
O dashboard precisa de um snapshot leve e consistente das métricas do sistema, funcionando em
SteamOS (Deck, APU AMD "Van Gogh"/"Sephiroth"), Bazzite e CachyOS Handheld (ROG Ally/Ally X com
Z1/Z1 Extreme, Legion Go, etc.), sem depender de bibliotecas nativas.

## Histórias de usuário
- Como jogador, quero ver uso de CPU/GPU/RAM, temperaturas, frequências, consumo e bateria, para entender o desempenho do jogo.
- Como jogador, quero que o monitor não pese no desempenho.

## Requisitos funcionais
- **FR-1** Método de backend `get_metrics()` retorna um snapshot no contrato abaixo.
- **FR-2 CPU:** uso total (%) e por núcleo calculados por delta de `/proc/stat` entre chamadas; temperatura
  (hwmon `k10temp`/`zenpower`/`coretemp`/`cpu_thermal`, preferindo `Tctl`/`Tdie`/`Package`); frequência média
  atual e máxima (`cpufreq`); modelo (`/proc/cpuinfo`); load average.
- **FR-3 GPU:** placa `drm/cardN` descoberta por `device/vendor`; AMD: uso (`gpu_busy_percent`), VRAM e GTT
  (`mem_info_*`), temperatura, clock (`freq1_input`) e potência do pacote (`power1_average` ou `power1_input`) via hwmon
  `amdgpu`. Intel: clock (`gt_cur_freq_mhz`) quando houver; demais campos `null`.
- **FR-4 Memória:** total, usado (total − disponível), disponível, % e swap (inclui zram) a partir de `/proc/meminfo`.
- **FR-5 Bateria:** primeira `power_supply` com `type=Battery` e `scope≠Device` (ignora baterias de controles).
  Percentual, status, potência (W; `power_now` ou `current_now×voltage_now`), tempo restante estimado (min) e saúde (%).
- **FR-6 Ventoinhas:** todas as entradas `fan*_input` de hwmon com rótulo (`fan*_label` ou nome do hwmon).
- **FR-7** Uptime (s).
- **FR-8** Qualquer métrica indisponível retorna `null` (ou lista vazia) sem lançar exceção.

## Contrato `get_metrics()`
```jsonc
{
  "ts": 1739999999.12,
  "uptime_s": 1234.5,
  "cpu": { "usage": 37.5, "per_core": [12.0, 80.1], "temp_c": 61.2, "freq_mhz": 2890,
           "freq_max_mhz": 5100, "cores": 16, "model": "AMD Ryzen Z1 Extreme", "load_avg": [1.2, 0.9, 0.7] },
  "gpu": { "name": "AMD", "usage": 92, "temp_c": 64.0, "freq_mhz": 2500, "vram_used_mb": 512,
           "vram_total_mb": 4096, "gtt_used_mb": 900, "gtt_total_mb": 12000, "power_w": 17.3 },     // ou null
  "memory": { "total_mb": 23900, "used_mb": 8000, "available_mb": 15900, "percent": 33.5,
              "swap_total_mb": 11900, "swap_used_mb": 0, "swap_percent": 0.0 },
  "battery": { "percent": 81, "status": "Discharging", "power_w": 19.8, "time_left_min": 192,
               "health_percent": 97.4 },                                                          // ou null
  "fans": [ { "label": "cpu_fan", "rpm": 3400 } ]
}
```

## Requisitos não funcionais
- **NFR-1** Somente stdlib; sem threads de fundo; coleta sob demanda.
- **NFR-2** Descoberta de sensores (hwmon, drm, power_supply) feita uma vez e reutilizada; leitura por chamada < 5 ms.
- **NFR-3** Testável com raiz de sistema de arquivos falsa (`MetricsCollector(root=...)`).

## Critérios de aceite
- [x] **AC-1** Dado `/proc/stat` em dois instantes, o uso de CPU total e por núcleo é o delta não-ocioso / delta total.
- [x] **AC-2** Na primeira chamada (sem amostra anterior) o uso de CPU é calculado desde o boot (nunca erro).
- [x] **AC-3** Dado hwmon `k10temp` com `Tctl`, `cpu.temp_c` usa esse sensor.
- [x] **AC-4** Dado GPU AMD, todos os campos de `gpu` são preenchidos em unidades MB/MHz/W/°C.
- [x] **AC-5** Bateria de controle (`scope=Device`) é ignorada; `power_w` cai para `current×voltage` quando não há `power_now`.
- [x] **AC-6** Sistema sem GPU/bateria/ventoinhas retorna `gpu: null`, `battery: null`, `fans: []`.
- [x] **AC-7** Testes `pnpm test:py` passam.

## Design
- `py_modules/sysmon/fsutil.py` — `read_str/read_int/read_float` tolerantes a erro.
- `py_modules/sysmon/metrics.py` — `MetricsCollector(root="/")` com estado da última amostra de `/proc/stat` e
  cache de descoberta (`_hwmon`, `_gpu_dev`, `_battery`).
- `main.py` mantém uma instância e expõe `async get_metrics()`.
- Potência da GPU AMD em APUs representa o pacote (SoC) — rotulada na UI como "APU".

## Tarefas
- [x] T1 Utilitários de leitura (FR-8)
- [x] T2 CPU (FR-2, AC-1, AC-2, AC-3)
- [x] T3 GPU (FR-3, AC-4)
- [x] T4 Memória, bateria, ventoinhas, uptime (FR-4..FR-7, AC-5, AC-6)
- [x] T5 Expor em `main.py` (FR-1)
- [x] T6 Testes com fixtures (AC-7)

## Fora de escopo
- GPUs NVIDIA dedicadas; histórico persistente; FPS (é do overlay da Steam/MangoHud).
