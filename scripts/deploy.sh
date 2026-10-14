#!/usr/bin/env bash
# Build, package and deploy the plugin to a handheld over SSH (specs/004-deploy-ssh).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PLUGIN_NAME="steam-system-monitor"
OUT_DIR="$ROOT/out"
STAGE="$OUT_DIR/$PLUGIN_NAME"

usage() {
  cat <<EOF
Uso: scripts/deploy.sh [opções]

Compila o plugin, envia por SSH e reinicia o Decky Loader no aparelho.
Configuração em .env.deploy (veja .env.deploy.example).

Opções:
  --package-only   apenas gera out/$PLUGIN_NAME.zip (instalação manual pelo Decky)
  --skip-build     não roda 'pnpm build'
  --no-restart     não reinicia o plugin_loader após instalar
  --logs           acompanha o log do Decky (journalctl) após o deploy
  --host HOST      sobrescreve DECK_HOST
  --user USER      sobrescreve DECK_USER
  -h, --help       mostra esta ajuda
EOF
}

log() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merro:\033[0m %s\n' "$*" >&2; exit 1; }

# Values from the environment win over .env.deploy
ENV_HOST="${DECK_HOST:-}"; ENV_USER="${DECK_USER:-}"; ENV_PORT="${DECK_PORT:-}"
ENV_KEY="${DECK_KEY:-}"; ENV_PASS="${DECK_SUDO_PASS:-}"
if [[ -f "$ROOT/.env.deploy" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.env.deploy"
fi
DECK_HOST="${ENV_HOST:-${DECK_HOST:-}}"
DECK_USER="${ENV_USER:-${DECK_USER:-}}"
DECK_PORT="${ENV_PORT:-${DECK_PORT:-22}}"
DECK_KEY="${ENV_KEY:-${DECK_KEY:-}}"
DECK_SUDO_PASS="${ENV_PASS:-${DECK_SUDO_PASS:-}}"

PACKAGE_ONLY=0; SKIP_BUILD=0; RESTART=1; FOLLOW_LOGS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --package-only) PACKAGE_ONLY=1 ;;
    --skip-build) SKIP_BUILD=1 ;;
    --no-restart) RESTART=0 ;;
    --logs) FOLLOW_LOGS=1 ;;
    --host) DECK_HOST="${2:?--host requer um valor}"; shift ;;
    --user) DECK_USER="${2:?--user requer um valor}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "opção desconhecida: $1" ;;
  esac
  shift
done

if [[ $PACKAGE_ONLY -eq 0 ]]; then
  [[ -n "$DECK_HOST" ]] || die "DECK_HOST não definido. Copie .env.deploy.example para .env.deploy e preencha."
  [[ -n "$DECK_USER" ]] || die "DECK_USER não definido em .env.deploy."
fi

# ---------------------------------------------------------------- build

if [[ $SKIP_BUILD -eq 0 ]]; then
  log "Compilando frontend"
  pnpm build >/dev/null || die "build falhou (rode 'pnpm build' para ver os erros)"
fi
[[ -f dist/index.js ]] || die "dist/index.js não existe; rode sem --skip-build"

# ---------------------------------------------------------------- package

log "Empacotando em out/$PLUGIN_NAME"
rm -rf "$STAGE"
mkdir -p "$STAGE/dist"
cp dist/index.js "$STAGE/dist/"
cp main.py plugin.json package.json LICENSE "$STAGE/"
[[ -f README.md ]] && cp README.md "$STAGE/"
cp -r py_modules "$STAGE/"
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} +

make_zip() {
  local zip_path="$OUT_DIR/$PLUGIN_NAME.zip"
  rm -f "$zip_path"
  if command -v zip >/dev/null 2>&1; then
    (cd "$OUT_DIR" && zip -qr "$zip_path" "$PLUGIN_NAME")
  elif [[ -x /c/Windows/System32/tar.exe ]]; then
    (cd "$OUT_DIR" && /c/Windows/System32/tar.exe -a -cf "$PLUGIN_NAME.zip" "$PLUGIN_NAME")
  else
    powershell.exe -NoProfile -Command \
      "Compress-Archive -Path '$(cygpath -w "$STAGE")' -DestinationPath '$(cygpath -w "$zip_path")'"
  fi
  log "Pacote: $zip_path"
}

if [[ $PACKAGE_ONLY -eq 1 ]]; then
  make_zip
  exit 0
fi

TARBALL="$OUT_DIR/$PLUGIN_NAME.tar.gz"
# Relative paths: GNU tar would treat "C:/..." as a remote host on Windows.
(cd "$OUT_DIR" && tar -czf "$PLUGIN_NAME.tar.gz" "$PLUGIN_NAME")

# ---------------------------------------------------------------- deploy

SSH_OPTS=(-p "$DECK_PORT" -o ConnectTimeout=10)
SCP_OPTS=(-P "$DECK_PORT" -o ConnectTimeout=10)
if [[ -n "$DECK_KEY" ]]; then
  SSH_OPTS+=(-i "$DECK_KEY")
  SCP_OPTS+=(-i "$DECK_KEY")
fi
TARGET="$DECK_USER@$DECK_HOST"
REMOTE_TMP="/tmp/$PLUGIN_NAME-deploy"

log "Enviando para $TARGET"
ssh "${SSH_OPTS[@]}" "$TARGET" "mkdir -p $REMOTE_TMP" || die "falha ao conectar em $TARGET (SSH ativo? chave configurada?)"
scp -q "${SCP_OPTS[@]}" "$TARBALL" scripts/remote-install.sh "$TARGET:$REMOTE_TMP/"

# $HOME is expanded by the remote user's shell before sudo (sudo may reset HOME to /root).
REMOTE_CMD="bash $REMOTE_TMP/remote-install.sh '$PLUGIN_NAME' \"\$HOME/homebrew/plugins\" '$REMOTE_TMP/$PLUGIN_NAME.tar.gz' $RESTART"

log "Instalando (sudo)"
if [[ -n "$DECK_SUDO_PASS" ]]; then
  printf '%s\n' "$DECK_SUDO_PASS" | ssh "${SSH_OPTS[@]}" "$TARGET" "sudo -S -p '' $REMOTE_CMD"
else
  ssh -t "${SSH_OPTS[@]}" "$TARGET" "sudo $REMOTE_CMD"
fi

log "Deploy concluído em $TARGET"

if [[ $FOLLOW_LOGS -eq 1 ]]; then
  log "Log do Decky (Ctrl+C para sair)"
  ssh -t "${SSH_OPTS[@]}" "$TARGET" "journalctl -u plugin_loader -f -n 50"
fi
