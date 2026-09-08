#!/usr/bin/env bash
# store-temp.sh — memory thermodynamics for the META-LOG object store.
# Demote cold comprehension deltas to a zstd-compressed archive tier, driven by
# mtime (the OS's native access-age proxy). COLD_DAYS env controls the cutoff.
#
# Principle (preservation strategy): the index row's `file` column is a content
# name, not a location — so recall is "find the name across active + archive".
# Never rewrites an index row; never edits history; appends only.
#
# Safety contract (bound writes, data first):
#   1. compress each delta to a temp .zst, then `zstd -t` to prove it decodes
#   2. only then move it into place and remove the original
#   3. preserve the original mtime on the archive copy (OS retains age)
#   4. append a one-line record to the demotion ledger
#   5. idempotent — re-running does nothing (originals already gone)
#   6. refuse to operate outside the store dir

set -eu

STORE="${1:-$HOME/.config/opencode/ontology/META-LOG}"
COLD_DAYS="${COLD_DAYS:-14}"
LEDGER="$STORE/../META-LOG-demoted.tsv"

[ -d "$STORE" ] || { echo "ERR: store dir missing: $STORE" >&2; exit 1; }

# Refuse if STORE is not a META-LOG object store (safety guard)
grep -q "^# " "$STORE/../META-LOG.md" 2>/dev/null || { echo "ERR: $STORE does not look like the META-LOG store" >&2; exit 1; }

ARCHIVE="$STORE/archive"
mkdir -p "$ARCHIVE"
: > "$LEDGER.tmp"   # will rewrite ledger only at end; see below

COLD_TS=$(date -d "-${COLD_DAYS} days" +%s 2>/dev/null || date -d "now - ${COLD_DAYS} days" +%s)
echo "store-temp: scanning $STORE (cold cutoff = ${COLD_DAYS}d, mtime < $(date -d @$COLD_TS '+%Y-%m-%d'))"

DEMOTED=0
while IFS= read -r -d '' f; do
    name=$(basename "$f")            # e.g. 001-2026-09-08-memory.md
    zst="$ARCHIVE/${name}.zst"
    [ -f "$zst" ] && { echo "  skip (already archived): $name"; continue; }

    tmp="$zst.tmp"
    if zstd -q -f -o "$tmp" "$f"; then
        if [ -s "$tmp" ] && zstd -q -t "$tmp"; then
            mv "$tmp" "$zst"
            touch -r "$f" "$zst"     # preserve the OS's age record on the archive copy
            printf '%s\t%s\t%s\n' "$(date -Is)" "$name" "demoted to $zst (mtime $(stat -c %y "$f" | cut -c1-19))" >> "$LEDGER"
            echo "  DEMOTED: $name -> $(basename "$zst") ($(stat -c %s "$zst") bytes)"
            rm -f -- "$f"            # delete original ONLY after archive copy verified
            DEMOTED=$((DEMOTED+1))
        else
            echo "  WARN: compression test failed for $name — original kept intact" >&2
            rm -f "$tmp"
        fi
    else
        echo "  WARN: compression failed for $name — original kept intact" >&2
        rm -f "$tmp"
    fi
done < <(find "$STORE" -maxdepth 1 -type f -name '*.md' -mtime +"$COLD_DAYS" -print0)

rm -f "$LEDGER.tmp"
echo "store-temp: done — $DEMOTED demoted, active deltas: $(find "$STORE" -maxdepth 1 -type f -name '*.md' | wc -l), archived: $(find "$ARCHIVE" -type f -name '*.zst' 2>/dev/null | wc -l)"