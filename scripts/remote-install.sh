#!/usr/bin/env bash
# Runs on the handheld as root (via sudo). Called by scripts/deploy.sh.
# Usage: remote-install.sh <plugin-name> <plugins-dir> <tarball> <restart:0|1>
set -euo pipefail

NAME="$1"
PLUGINS_DIR="$2"
TARBALL="$3"
RESTART="${4:-1}"
# Same items the in-plugin updater handles (py_modules/sysmon/updater.py PAYLOAD).
PAYLOAD=(plugin.json package.json main.py LICENSE README.md CHANGELOG.md build.json dist py_modules)

[[ -d "$PLUGINS_DIR" ]] || { echo "erro: $PLUGINS_DIR não existe — o Decky Loader está instalado?" >&2; exit 1; }

INSTALLED="$PLUGINS_DIR/$NAME"
WORK="$(dirname "$TARBALL")"
tar --no-same-owner -xzf "$TARBALL" -C "$WORK"
NEW="$WORK/$NAME"

# Spec 009 REQ-702: keep the installed version as the rollback copy (same folder the backend uses:
# DECKY_PLUGIN_SETTINGS_DIR = <homebrew>/settings/<plugin folder>). Redeploying the same build keeps the
# older copy instead of replacing it with an identical one.
SETTINGS_DIR="$(dirname "$PLUGINS_DIR")/settings/$NAME"
ROLLBACK="$SETTINGS_DIR/rollback"
if [[ -f "$INSTALLED/plugin.json" ]] && ! cmp -s "$INSTALLED/build.json" "$NEW/build.json"; then
  mkdir -p "$SETTINGS_DIR"
  rm -rf "$ROLLBACK.new"
  mkdir "$ROLLBACK.new"
  for item in "${PAYLOAD[@]}"; do
    if [[ -e "$INSTALLED/$item" ]]; then cp -a "$INSTALLED/$item" "$ROLLBACK.new/"; fi
  done
  rm -rf "$ROLLBACK"
  mv "$ROLLBACK.new" "$ROLLBACK"
  echo "versão anterior guardada em $ROLLBACK"
fi

rm -rf "${PLUGINS_DIR:?}/$NAME"
mv "$NEW" "$INSTALLED"
chmod -R u+rwX,go+rX "$INSTALLED"
rm -rf "$WORK"
echo "instalado em $INSTALLED"

if [[ "$RESTART" == "1" ]]; then
  systemctl restart plugin_loader
  echo "plugin_loader reiniciado"
fi
