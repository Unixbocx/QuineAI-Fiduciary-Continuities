#!/usr/bin/env bash
# sync.sh — two-way sync between the package folder (this repo)
# and the installed copy (~/.config/opencode).
#
# Usage:
#   ./sync.sh install  — push package -> install (same as install.sh, no AGENTS.md)
#   ./sync.sh pull     — pull changed installed files back into the package
#   ./sync.sh          — default: install
#
# Which dirs: plugin/ plugins/ | scripts/ session-tools/ | skills/ | agents/ |
# commands/ | ontology/ (model files both ways; ledgers pull-only — install
# never overwrites the installed append-only records)

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
MODE="${1:-install}"

# Locate the package folder. Priority: $ALOP_PACKAGE_DIR -> remembered path
# (.alop-package-dir beside this script) -> script lives at <pkg>/ itself.
# Never guess from script location alone: the installed copy lives in
# session-tools/ and must NOT treat session-tools/ as the package.
PKG_REF="$SCRIPT_DIR/.alop-package-dir"
if [ -n "${ALOP_PACKAGE_DIR:-}" ]; then
  PACKAGE_DIR="$ALOP_PACKAGE_DIR"
elif [ -f "$PKG_REF" ]; then
  PACKAGE_DIR="$(cat "$PKG_REF")"
elif [ -d "$SCRIPT_DIR/plugin" ] || [ -d "$SCRIPT_DIR/../plugin" ]; then
  PACKAGE_DIR="$SCRIPT_DIR"
fi
if [ -z "${PACKAGE_DIR:-}" ] || [ ! -d "$PACKAGE_DIR" ]; then
  echo "error: package folder unknown — run once with ALOP_PACKAGE_DIR=<path>" >&2
  exit 1
fi
echo "$PACKAGE_DIR" > "$PKG_REF"

# Model files ship in the package; ledger files are per-install history.
ONTOLOGY_MODEL="SELF.md META.md ONTOLOGY.md ANTI-ONTOLOGY.md BEHAVIOR.md BEHAVIOR-reduced.md"

case "$MODE" in
  install)
    cp "$PACKAGE_DIR"/plugin/*.js "$CFG/plugins/" 2>/dev/null || true
    cp "$PACKAGE_DIR"/scripts/* "$CFG/session-tools/" 2>/dev/null || true
    for d in "$PACKAGE_DIR"/skills/*/; do
      [ -d "$d" ] && { rm -rf "$CFG/skills/$(basename "$d")"; cp -r "$d" "$CFG/skills/"; }
    done
    cp "$PACKAGE_DIR"/agents/*.md "$CFG/agent/" 2>/dev/null || true
    cp "$PACKAGE_DIR"/commands/*.md "$CFG/command/" 2>/dev/null || true
    for f in $ONTOLOGY_MODEL; do
      [ -f "$PACKAGE_DIR/ontology/$f" ] && cp "$PACKAGE_DIR/ontology/$f" "$CFG/ontology/" || true
    done
    ;;
  pull)
    cp -u "$CFG"/plugins/*.js "$PACKAGE_DIR/plugin/" 2>/dev/null || true
    cp -u "$CFG"/session-tools/* "$PACKAGE_DIR/scripts/" 2>/dev/null || true
    for d in "$CFG"/skills/*/; do
      [ -d "$d" ] && { rm -rf "$PACKAGE_DIR/skills/$(basename "$d")"; cp -r "$d" "$PACKAGE_DIR/skills/"; }
    done
    cp -u "$CFG"/agent/*.md "$PACKAGE_DIR/agents/" 2>/dev/null || true
    cp -u "$CFG"/command/*.md "$PACKAGE_DIR/commands/" 2>/dev/null || true
    mkdir -p "$PACKAGE_DIR/ontology"
    cp -u "$CFG"/ontology/*.md "$PACKAGE_DIR/ontology/" 2>/dev/null || true
    ;;
  *) echo "usage: $0 [install|pull]" >&2; exit 1;;
esac
echo "sync $MODE done"