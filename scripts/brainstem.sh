#!/usr/bin/env bash
# brainstem.sh — scheduled self-check for the preservation layer (BSTEM analog).
# Runs, in order: identity probe (Test 1), store thermodynamics (Test 2),
# index<->store consistency. Appends a one-line record to the brainstem log.
# Fails loudly (exit 1) on any check failing so cron can surface it.
# Read-only except: store-temp (demotes only when cold) + the log append.

set -u

# Guard: the brainstem only exists to serve a running opencode process.
# If the daemon is not running, there is no consumer and nothing to verify —
# exit silently (no log line). Uses the exact process NAME (-x), not -f,
# because -f would match the cron shell's own path (which contains "opencode")
# and log forever even when the daemon is absent.
if ! pgrep -x opencode >/dev/null; then
    exit 0
fi

TOOLS="${1:-$HOME/.config/opencode/session-tools}"
ONT="${2:-$HOME/.config/opencode/ontology}"
STATE="${3:-$HOME/.config/opencode/state}"
LOG="$STATE/brainstem.log"

mkdir -p "$STATE" 2>/dev/null
fail=0

: > /dev/null 2>&1 || true
if ! touch "$LOG" 2>/dev/null; then echo "brainstem: cannot write log $LOG" >&2; exit 1; fi

if bash "$TOOLS/verify_recall.sh" "$ONT" "$STATE" >/dev/null 2>&1; then
    ident="identity OK"
else
    ident="identity FAILED"; fail=1
fi

if COLD_DAYS="${COLD_DAYS:-14}" bash "$TOOLS/store-temp.sh" "$ONT/META-LOG" >/dev/null 2>&1; then
    thermo="thermo OK"
else
    thermo="thermo FAILED"; fail=1
fi

rows=$(grep -c '^| [0-9][0-9]*' "$ONT/META-LOG.md" 2>/dev/null || echo 0)
files=$(find "$ONT/META-LOG" -maxdepth 1 -name '0*.md' 2>/dev/null | wc -l)
trade_ok="consistency"
[ "$rows" = "$files" ] || { trade_ok="UNSYNCED rows=$rows files=$files"; fail=1; }

# Auto-Memory step: when the unconsolidated count crosses the threshold,
# the dump fires — short-term deltas consolidate into long-term structure.
# Runs after consistency so we never consolidate a drifted store.
if [ "$trade_ok" = "consistency" ]; then
    CONS_OUT=$(CONSOLIDATE_AT="${CONSOLIDATE_AT:-8}" bash "$TOOLS/consolidate.sh" "$ONT" 2>&1)
    if echo "$CONS_OUT" | grep -q "WROTE"; then
        accum="consolidated$(echo "$CONS_OUT" | grep -c WROTE)"
        echo "  $ident | $thermo | $trade_ok | $accum | active=$files | $(date -Is)" >> "$LOG"
    else
        echo "  $ident | $thermo | $trade_ok | active=$files | $(date -Is)" >> "$LOG"
    fi
else
    echo "  $ident | $thermo | $trade_ok | active=$files | $(date -Is)" >> "$LOG"
fi
echo "brainstem: $ident | $thermo | $trade_ok (active=$files)"
exit $fail