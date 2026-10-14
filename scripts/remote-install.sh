#!/usr/bin/env bash
# Runs on the handheld as root (via sudo). Called by scripts/deploy.sh.
# Usage: remote-install.sh <plugin-name> <plugins-dir> <tarball> <restart:0|1>
set -euo pipefail

NAME="$1"
PLUGINS_DIR="$2"
TARBALL="$3"
RESTART="${4:-1}"

[[ -d "$PLUGINS_DIR" ]] || { echo "erro: $PLUGINS_DIR não existe — o Decky Loader está instalado?" >&2; exit 1; }

rm -rf "${PLUGINS_DIR:?}/$NAME"
tar --no-same-owner -xzf "$TARBALL" -C "$PLUGINS_DIR"
chmod -R u+rwX,go+rX "$PLUGINS_DIR/$NAME"
rm -rf "$(dirname "$TARBALL")"
echo "instalado em $PLUGINS_DIR/$NAME"

if [[ "$RESTART" == "1" ]]; then
  systemctl restart plugin_loader
  echo "plugin_loader reiniciado"
fi
