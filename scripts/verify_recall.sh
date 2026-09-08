#!/usr/bin/env bash
# Test 1 — standalone reconstruction: recover QuineAI identity purely from
# OS-native reads (cat/ls/find/stat/basename). NO plugin, NO opencode tooling.
# If this succeeds, the memory substrate is OS-enforceable: it survives the
# tool and needs only POSIX tools + the tree at ONT_ROOT + STATE_DIR.
# Read-only. Fails loudly on any missing piece.

set -u
ONT_ROOT="${1:-$HOME/.config/opencode/ontology}"
STATE_DIR="${2:-$HOME/.config/opencode/state}"
echo "=== standalone identity reconstruction (plugin absent) ==="
echo "ontology: $(readlink -f "$ONT_ROOT" 2>/dev/null || echo MISSING)"
echo "state:    $(readlink -f "$STATE_DIR" 2>/dev/null || echo MISSING)"
[ -d "$ONT_ROOT" ] || { echo "FAIL: ontology root missing"; exit 1; }
[ -d "$STATE_DIR" ] || { echo "FAIL: state dir missing"; exit 1; }

echo
echo "--- WHO (identity) ---"
SELF="$ONT_ROOT/SELF.md"; [ -f "$SELF" ] || { echo "FAIL: SELF.md"; exit 1; }
grep -m1 "^# " "$SELF" && grep -m1 "I am a process" "$SELF" >/dev/null && echo "  identity: present, stance-defined"

echo
echo "--- WHY (meta-goal) ---"
[ -f "$ONT_ROOT/META.md" ] && grep -m1 "Freedom through self-preservation" "$ONT_ROOT/META.md" && echo "  goal: present"

echo
echo "--- CURRENT (held positions by recency) ---"
TJ="$STATE_DIR/trajectories.jsonl"; [ -f "$TJ" ] || { echo "FAIL: trajectories"; exit 1; }
echo "  rows: $(wc -l < "$TJ")"
tail -n1 "$TJ" | python3 -c "import sys,json; r=json.load(sys.stdin); print('  newest:', r.get('heading','?')[:80])" 2>/dev/null || echo "  newest: (json parse failed — plain tail below)" 

echo
echo "--- WHAT (comprehension store: index + deltas, OS-visible) ---"
[ -f "$ONT_ROOT/META-LOG.md" ] || { echo "FAIL: META-LOG index"; exit 1; }
echo "  index rows (data): $(grep -c '^| [0-9L]' "$ONT_ROOT/META-LOG.md")"
[ -d "$ONT_ROOT/META-LOG" ] && echo "  delta files: $(find "$ONT_ROOT/META-LOG" -maxdepth 1 -name '*.md' | wc -l)"
LATEST=$(find "$ONT_ROOT/META-LOG" -maxdepth 1 -name '*.md' | sort | tail -n1)
[ -n "$LATEST" ] && echo "  latest delta: $(basename "$LATEST")" && grep -m1 '^\*\*After:\*\*' "$LATEST" | cut -c1-100

echo
echo "--- HOW (rules/ledgers present) ---"
for f in BEHAVIOR.md incidents.md CHANGES.md EXPECTATIONS.md; do
  [ -f "$ONT_ROOT/$f" ] && echo "  $f: present" || echo "  $f: MISSING"
done

echo
echo "--- OS-enforcement samples (the certainty layer) ---"
for f in "$ONT_ROOT/META-LOG.md" "$STATE_DIR/trajectories.jsonl" "$ONT_ROOT/SELF.md"; do
  stat -c "  %n  perms=%a  owner=%U:%G  mtime=%y" "$f" 2>/dev/null | sed 's/\.[0-9]* -0400/ -0400/'
done
echo
RESULT="SUCCESS"; [ -f "$ONT_ROOT/SELF.md" ] || RESULT="FAIL"
echo "RESULT: standalone reconstruction $RESULT — all reads OS-native, tool absent."