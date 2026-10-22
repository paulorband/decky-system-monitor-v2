# Spec 008 — Atualização automática

- **Status:** Concluída — validada no Ally X (v0.1.0 → v0.2.0); pendente: AC-11 (canal de teste)
- **Depende de:** 004, 007
- **Referência:** porta da spec 009 do plugin anterior (`decky-system-monitor`), já validada lá; os IDs `REQ-6xx`
  abaixo são os mesmos para facilitar a comparação.

## Contexto
Hoje a única forma de atualizar é o deploy por SSH (spec 004) ou instalar um ZIP manualmente. O plugin deve
avisar quando houver versão nova no GitHub e se instalar sozinho, com segurança, pelo controle.

## Origem das versões
Repositório `paulorband/decky-system-monitor-v2`. Asset de cada release: `steam-system-monitor.zip`, com a pasta
`steam-system-monitor/` na raiz (mesmo layout do `pnpm run package`).

## Requisitos

### Verificação
- **REQ-600** Ao iniciar (se `auto_check` ligado), o frontend pede ao backend para consultar as releases do GitHub;
  só releases estáveis contam (pré-releases e `test-build` são ignorados, salvo canal de teste).
- **REQ-601** Versões SemVer (`vX.Y.Z`); há atualização se `latest > current`. Tags inválidas são ignoradas. A versão
  atual vem do `package.json` instalado.
- **REQ-602** Falha de rede/API é silenciosa na inicialização; só aparece em "Verificar agora".
- **REQ-603** Consulta fora do loop principal (executor), timeout ≤ 10 s, sem repetição automática; resultado em cache
  por 6 h; "Verificar agora" ignora o cache.
- **REQ-604** `auto_check` (padrão: ligado) configurável; desligado, nenhuma requisição sem ação do usuário.

### Notificação
- **REQ-610** Havendo atualização na verificação de inicialização, toast do Decky no idioma do plugin (spec 007), uma
  vez por inicialização.

### Tela
- **REQ-620** Seção "Atualizações" no fim do painel: versão atual; versão nova (se houver); estado ("Atualizado" /
  "Ainda não verificado"); botão **Instalar vX.Y.Z** ou **Verificar atualizações**.
- **REQ-622** Tudo focável e operável por controle; botões desabilitados durante a operação; mensagem de resultado
  como linha focável.

### Instalação
- **REQ-630** Só por clique; o backend **rebusca** a release (não confia no frontend) e exige `latest > current`.
- **REQ-631 Origem**: asset `steam-system-monitor.zip` com URL iniciando em
  `https://github.com/paulorband/decky-system-monitor-v2/releases/download/`.
- **REQ-632 Integridade**: `digest` `sha256:` do asset (API do GitHub) obrigatório e conferido; senão recusa
  (falha fechada). Limite de 10 MB.
- **REQ-633 Zip seguro**: sem caminhos absolutos, `..`, `\` ou symlinks; tudo sob `steam-system-monitor/`; limite
  descompactado de 30 MB.
- **REQ-634 Validação**: `plugin.json` com `name` = `System Monitor`, `main.py` e `dist/index.js`; release estável
  exige `package.json` com a versão da tag.
- **REQ-635 Aplicação com rollback**: `plugin.json`, `package.json`, `main.py`, `LICENSE`, `README.md`, `build.json`,
  `dist/`, `py_modules/` são copiados sobre a pasta instalada, com backup restaurado se algo falhar.
- **REQ-636** Após sucesso, reinício destacado do Decky (`systemctl restart plugin_loader`, atraso de 3 s) com ambiente
  limpo (sem `LD_LIBRARY_PATH` do Decky) e log em `restart.log`. A UI informa antes e, se o Decky não reiniciar em
  ~20 s, orienta a reiniciar manualmente.
- **REQ-637** Instalações concorrentes são recusadas.
- **REQ-638 Privilégio**: `~/homebrew/plugins` pertence ao root, então `plugin.json` declara `"flags": ["root"]`.
  Pasta sem escrita → falha **antes de tocar em arquivos**, com mensagem explícita.

### Publicação (CI)
- **REQ-640** Workflow `.github/workflows/release.yml`: em push de tag `v*` publica a release (falha se a tag ≠
  `v` + versão do `package.json`); em push de branch atualiza o pré-release rolante `test-build`. Roda typecheck,
  `check:i18n` e testes antes de empacotar.

### Canal de teste (opt-in)
- **REQ-650** `test_channel` (padrão desligado) passa a considerar também o pré-release `test-build`.
- **REQ-651** Ligar exige confirmação em `ConfirmModal` com o aviso de risco; desligar é imediato; com o canal ligado
  um aviso âmbar focável fica nas configurações.
- **REQ-652** Todo zip traz `build.json` (`version`, `commit`); o commit do `test-build` vem do corpo da release
  (`commit: <sha>`) ou de `target_commitish`.
- **REQ-653** Há build de teste novo se o commit difere do instalado e a versão não é menor que a instalada.
- **REQ-654** Canal ligado: build de teste novo vence; senão, estável mais nova. Canal desligado: `test-build`
  ignorado.
- **REQ-655** Mesma segurança da instalação estável; o backend lê `test_channel` das **suas** configurações.
- **REQ-656** UI rotula o build de teste ("v0.2.0 · teste ab12cd3", âmbar); botão "Instalar build de teste".
- **REQ-657** `test-build` do mesmo commit da estável mais recente é tratado como a estável.

### Limite do GitHub e identidade
- **REQ-660** Uma única chamada `GET /repos/…/releases?per_page=15` por verificação.
- **REQ-661** Cache `ETag` em disco (`http-cache.json`); `304` não conta no limite.
- **REQ-662** Limite atingido (403 com limite zerado, ou 429) → `error = "RateLimited"` + `retry_minutes`; UI mostra
  "tente de novo em ~N min".
- **REQ-663** Instalação grava `kind` (`stable`|`test`) no `build.json`; instalações manuais inferem pelo commit.
- **REQ-664** "Versão atual" mostra `v0.2.0 · teste fb361f2` (âmbar) para teste e `v0.2.0 · fb361f2` quando a origem
  é desconhecida.

### Configurações no backend
- **REQ-670** `auto_check` e `test_channel` ficam em `settings.json` na pasta de configurações do plugin
  (sanitizadas), lidas/gravadas por `get_settings`/`set_settings`. As demais preferências de UI seguem no
  `localStorage` (specs 002/005/006/007).

## Critérios de aceite
- [x] **AC-1** Testes portados do plugin anterior passam (`pnpm test:py`): versões, verificação, origem, digest,
  zip seguro, validação, rollback, permissão, ambiente limpo, canal de teste, `ETag`, limite, `kind`.
- [x] **AC-2** Configurações do backend: valores inválidos voltam ao padrão.
- [x] **AC-3** `pnpm package` gera o zip com `build.json` (`version`, `commit`).
- [x] **AC-4** `pnpm typecheck`, `pnpm check:i18n` e `pnpm build` passam; textos novos nos três idiomas.
- [x] **AC-5** `plugin.json` declara `flags: ["root"]` e a constituição registra a exceção.
- [x] **AC-6** CI publica `v0.1.0` (release) e `test-build` (pré-release) com `steam-system-monitor.zip` e digest
  `sha256` _(GitHub Actions, 2026-10-22)_.
- [x] **AC-7** Ponta a ponta contra o GitHub real: instalação simulada `0.0.1` → `check` encontra `0.1.0`;
  `install` baixa, confere o SHA-256, valida e aplica, gravando `build.json` com `kind: stable` _(2026-10-22)_.
- [x] **AC-8** Canal de teste com `test-build` do mesmo commit da `v0.1.0` é tratado como a estável (REQ-657) _(2026-10-22)_.
- [x] **AC-9** Com uma release `v0.2.0` publicada e `v0.1.0` instalada, o toast aparece ao iniciar. _(validado no Ally X, 2026-10-22)_
- [x] **AC-10** "Instalar v0.2.0" instala, o Decky reinicia e o painel mostra a nova versão. _(validado no Ally X, 2026-10-22)_
- [ ] **AC-11** Canal de teste: confirmação por modal e instalação do `test-build`. _(validar no aparelho)_

## Design
- `py_modules/sysmon/updater.py` — porta de `sm_updater.py` (constantes do novo repositório/asset; `README.md` no payload).
- `py_modules/sysmon/settings.py` — `auto_check`, `test_channel` (REQ-670).
- `main.py` — `get_update_state`, `check_update`, `install_update`, `get_settings`, `set_settings`.
- `src/updates.ts` — `startupUpdateCheck()` (após `initI18n`) e hook `useUpdates()`.
- `src/components/UpdateSection.tsx` + toggles em Configurações no `Dashboard`.
- `scripts/deploy.sh` grava `build.json` no pacote; `.github/workflows/release.yml` publica.
- Testes passam a rodar com `pytest` (que também executa os `unittest` existentes).

## Fora de escopo
- Repositório privado ou sem rede: sem atualização.
- Reverter para uma versão anterior pela UI.
