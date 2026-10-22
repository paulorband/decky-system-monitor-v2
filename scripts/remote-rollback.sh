#!/usr/bin/env bash
# Runs on the handheld as root (via sudo). Called by `scripts/deploy.sh --rollback` (spec 009 REQ-714):
# restores the rollback copy even when the plugin UI does not load.
# Usage: remote-rollback.sh <plugin-name> <plugins-dir> <restart:0|1>
set -euo pipefail

NAME="$1"
PLUGINS_DIR="$2"
RESTART="${3:-1}"
PAYLOAD=(plugin.json package.json main.py LICENSE README.md CHANGELOG.md build.json dist py_modules)

INSTALLED="$PLUGINS_DIR/$NAME"
SETTINGS_DIR="$(dirname "$PLUGINS_DIR")/settings/$NAME"
ROLLBACK="$SETTINGS_DIR/rollback"

for need in plugin.json main.py dist/index.js; do
  [[ -e "$ROLLBACK/$need" ]] || { echo "erro: não há versão anterior válida em $ROLLBACK (falta $need)" >&2; exit 1; }
done
grep -q '"System Monitor"' "$ROLLBACK/plugin.json" || { echo "erro: $ROLLBACK não é do System Monitor" >&2; exit 1; }

# Build the restored folder aside, then swap it in, so a failure never leaves a half-restored plugin.
STAGING="$SETTINGS_DIR/rollback.apply"
rm -rf "$STAGING"
if [[ -d "$INSTALLED" ]]; then cp -a "$INSTALLED" "$STAGING"; else mkdir -p "$STAGING"; fi
for item in "${PAYLOAD[@]}"; do
  rm -rf "${STAGING:?}/$item"
  if [[ -e "$ROLLBACK/$item" ]]; then cp -a "$ROLLBACK/$item" "$STAGING/"; fi
done

rm -rf "$SETTINGS_DIR/rollback.prev"
if [[ -d "$INSTALLED" ]]; then mv "$INSTALLED" "$SETTINGS_DIR/rollback.prev"; fi
mv "$STAGING" "$INSTALLED"
chmod -R u+rwX,go+rX "$INSTALLED"
rm -rf "$SETTINGS_DIR/rollback.prev" "$ROLLBACK"
echo "restaurado em $INSTALLED: $(grep -o '"version"[^,}]*' "$INSTALLED/package.json")"

if [[ "$RESTART" == "1" ]]; then
  systemctl restart plugin_loader
  echo "plugin_loader reiniciado"
fi
