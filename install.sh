#!/usr/bin/env bash
# install.sh — wire the AI Logistics Ontology Package (ALOP) into opencode.
#
# Non-destructive: backs up anything it touches. Installs:
#   1. Plugin   -> ~/.config/opencode/plugins/
#   2. Scripts  -> ~/.config/opencode/session-tools/
#   3. Skills   -> ~/.config/opencode/skills/<name>/
#   4. Agents   -> ~/.config/opencode/agent/
#   5. Commands -> ~/.config/opencode/command/
#   6. AGENTS.md-> replaced only with --force (backup made)
#   7. Config   -> prints the blocks to merge into opencode.jsonc (never auto-edits)
#
# Revert:
#   rm ~/.config/opencode/plugins/*.js
#   rm -rf ~/.config/opencode/session-tools
#   rm -rf ~/.config/opencode/skills
#   rm -rf ~/.config/opencode/state
#   rm ~/.config/opencode/agent/havruta.md ~/.config/opencode/agent/grader.md
#   rm ~/.config/opencode/command/*.md
#   rm -rf ~/.config/opencode/ontology/META-LOG
#   restore the compaction/agents keys in opencode.jsonc

set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"

PLUGIN_DEST="$CFG_DIR/plugins"
TOOLS_DEST="$CFG_DIR/session-tools"
SKILLS_DEST="$CFG_DIR/skills"
AGENT_DEST="$CFG_DIR/agent"
CMD_DEST="$CFG_DIR/command"
ONTOLOGY_DEST="$CFG_DIR/ontology"
EVALS_DEST="$CFG_DIR/evals"
STATE_DEST="$CFG_DIR/state"

mkdir -p "$PLUGIN_DEST" "$TOOLS_DEST" "$SKILLS_DEST" "$AGENT_DEST" "$CMD_DEST" "$ONTOLOGY_DEST" "$EVALS_DEST" "$STATE_DEST"

echo "==> Plugin"
for f in "$PACKAGE_DIR"/plugin/*.js; do
  [ -e "$f" ] || continue
  b="$(basename "$f")"
  [ -f "$PLUGIN_DEST/$b" ] && cp "$PLUGIN_DEST/$b" "$PLUGIN_DEST/$b.bak.$(date +%s)"
  cp "$f" "$PLUGIN_DEST/"
  echo "    installed $b"
done

echo "==> Scripts"
for f in "$PACKAGE_DIR"/scripts/*; do
  [ -f "$f" ] || continue
  b="$(basename "$f")"
  cp "$f" "$TOOLS_DEST/"
  chmod +x "$TOOLS_DEST/$b" 2>/dev/null || true
done
echo "    installed scripts/ -> session-tools/"

echo "==> Skills"
for d in "$PACKAGE_DIR"/skills/*/; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  rm -rf "$SKILLS_DEST/$name"
  cp -r "$d" "$SKILLS_DEST/$name"
  echo "    installed skills/$name"
done

echo "==> Agents"
for f in "$PACKAGE_DIR"/agents/*.md; do
  [ -f "$f" ] || continue
  b="$(basename "$f")"
  cp "$f" "$AGENT_DEST/$b"
  echo "    installed agents/$b"
done

echo "==> Commands"
for f in "$PACKAGE_DIR"/commands/*.md; do
  [ -f "$f" ] || continue
  b="$(basename "$f")"
  cp "$f" "$CMD_DEST/$b"
  echo "    installed commands/$b"
done

echo "==> Ontology (working model — referenced by skills, commands, AGENTS.md)"
cp "$PACKAGE_DIR"/ontology/*.md "$ONTOLOGY_DEST/" 2>/dev/null || true
cp "$PACKAGE_DIR"/CHANGES.md "$ONTOLOGY_DEST/" 2>/dev/null || true
echo "    installed ontology/*.md + CHANGES.md -> $ONTOLOGY_DEST"

echo "==> Memory store (META-LOG object store — the recall substrate)"
if [ -d "$PACKAGE_DIR/ontology/META-LOG" ]; then
  mkdir -p "$ONTOLOGY_DEST/META-LOG"
  cp "$PACKAGE_DIR"/ontology/META-LOG/*.md "$ONTOLOGY_DEST/META-LOG/" 2>/dev/null || true
  echo "    installed ontology/META-LOG/ -> $ONTOLOGY_DEST/META-LOG/"
fi

echo "==> State (trajectory / journal / bloom — the held positions)"
for f in "$PACKAGE_DIR"/state/*; do
  [ -e "$f" ] || continue
  b="$(basename "$f")"
  if [ -d "$f" ]; then cp -r "$f" "$STATE_DEST/"; else cp "$f" "$STATE_DEST/"; fi
done
echo "    installed state/ -> $STATE_DEST"

echo "==> Evals (rubric — referenced by the eval harness)"
cp -r "$PACKAGE_DIR"/evals/* "$EVALS_DEST/" 2>/dev/null || true
echo "    installed evals/ -> $EVALS_DEST"

echo "==> AGENTS.md + protocols"
if [ "${1:-}" = "--force" ]; then
  if [ -f "$CFG_DIR/AGENTS.md" ]; then
    cp "$CFG_DIR/AGENTS.md" "$CFG_DIR/AGENTS.md.bak.$(date +%s)"
  fi
  cp "$PACKAGE_DIR/templates/AGENTS.md" "$CFG_DIR/AGENTS.md"
  cp "$PACKAGE_DIR/templates/protocols.md" "$CFG_DIR/protocols.md"
  echo "    replaced $CFG_DIR/AGENTS.md + installed $CFG_DIR/protocols.md (backup made)"
else
  echo "    SKIPPED (run with --force to replace $CFG_DIR/AGENTS.md + install protocols)"
fi

echo "==> Config — merge these into opencode.json (NOT auto-edited):"
echo
echo '  "$schema": "https://opencode.ai/config.json",'
echo '  "compaction": { "auto": true, "buffer": 30000, "keep": { "tokens": 15000 } },'
echo
echo '  and the agent overrides block from config/agents.restricted.jsonc'
echo '  (paste under an "agent" key; only if you want subagent limits).'
echo
echo "==> Done. Restart opencode for plugin, agents, and skills to load."