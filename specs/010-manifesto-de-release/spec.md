# Spec 010 — Atualização sem a API do GitHub (manifesto de release)

- **Status:** Concluída — AC-7 depende de teste no Ally X
- **Depende de:** 008, 009

## Contexto
No Ally X a verificação parou com "Limite de requisições do GitHub atingido". A API sem autenticação
(`api.github.com`) permite **60 requisições/hora por IP público**, e esse limite é dividido por tudo na rede: o
próprio Decky Loader verificando atualizações, outros plugins, computadores. Medido em 2026-10-22: 60/60 usadas,
API respondendo 403, enquanto os downloads de release (`github.com/…/releases/download/…`) continuavam com HTTP 200.
O cache `ETag` (REQ-661) não ajuda: respostas `304` só deixam de contar quando a requisição é autenticada.

## Requisitos funcionais
- **REQ-800 Manifesto**: cada release (estável e `test-build`) publica, além do zip, o asset `release.json`:
  ```jsonc
  { "schema": 1, "tag": "v0.4.0", "version": "0.4.0", "kind": "stable",   // "test" no test-build
    "commit": "<sha de 40>", "asset": "steam-system-monitor.zip",
    "sha256": "<64 hex do zip>", "size": 57167, "notes": "### Novidades\n- …" }
  ```
- **REQ-801 Leitura sem API**: a verificação lê
  `https://github.com/paulorband/decky-system-monitor-v2/releases/latest/download/release.json` (a release estável mais
  recente; pré-releases nunca são "latest") e, com o canal de teste ligado,
  `…/releases/download/test-build/release.json`. Esses endereços não contam no limite da API.
- **REQ-802 Origem e integridade**: a URL do zip é **montada** pelo plugin (`…/releases/download/<tag>/steam-system-monitor.zip`),
  nunca lida do manifesto; `tag` precisa ser `v` + SemVer (ou `test-build` no canal de teste), `sha256` precisa ter
  64 hex e o zip baixado precisa conferir (falha fechada, como REQ-632). Manifesto maior que 64 KiB, JSON inválido
  ou `schema` desconhecido é rejeitado.
- **REQ-803 Reserva**: se o manifesto não existir (HTTP 404, ou inválido) — releases anteriores à v0.4.0 — o plugin usa a API
  como antes (spec 008), só para o que faltou. Falhas de rede no manifesto **não** caem para a API (evita gastar o limite à toa).
- **REQ-804** Mesmas regras de decisão da spec 008 (REQ-601, 653, 654, 657): o commit vem do manifesto, então a
  regra "test-build do mesmo commit da estável" passa a valer sempre (antes dependia do `target_commitish`).
- **REQ-805** O CI gera `release.json` com `scripts/release-manifest.mjs` (SHA-256 calculado do zip publicado; notas do
  `CHANGELOG.md` para a estável e do corpo do `test-build` para o teste).

## Segurança
O SHA-256 passa a vir de um asset publicado pelo mesmo CI que publica o zip, em vez do `digest` calculado pela API.
Quem consegue publicar assets na release consegue trocar ambos em qualquer um dos modelos; origem fixa (REQ-802),
HTTPS e a validação do conteúdo (REQ-633/634) continuam iguais.

## Critérios de aceite
- [x] **AC-1** Com manifestos publicados, uma verificação faz **zero** requisições à API (estável e teste).
- [x] **AC-2** `install` baixa o zip da URL montada e confere o SHA-256 do manifesto; divergência recusa.
- [x] **AC-3** Manifesto com `tag` fora do padrão, `sha256` inválido, `schema` desconhecido ou grande demais é ignorado.
- [x] **AC-4** Sem manifesto (404), o resultado é o mesmo da spec 008 pela API; erro de rede no manifesto vira erro, sem chamar a API.
- [x] **AC-5** `test-build` do mesmo commit da estável é tratado como a estável usando o commit do manifesto.
- [x] **AC-6** `pnpm test:py`, `pnpm typecheck`, `pnpm build` passam; o manifesto gerado localmente confere com o zip.
- [x] **AC-8** Contra o GitHub real com a API esgotada (0/60): uma instalação `0.3.0` encontrou e instalou a
  `v0.4.0` com **zero** chamadas à API, guardando a `0.3.0` como cópia de rollback _(2026-10-22)_.
- [ ] **AC-7** No Ally X, com a API esgotada, a v0.4.0+ verifica e instala normalmente. _(validar no aparelho)_

## Limitações
- Quem está na v0.3.0 ou anterior ainda usa a API para descobrir a v0.4.0; depois de instalada, não depende mais dela.
