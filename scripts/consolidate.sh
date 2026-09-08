#!/usr/bin/env bash
# consolidate.sh — Auto-Memory dump: short-term → long-term at threshold.
#   When the number of unconsolidated deltas reaches CONSOLIDATE_AT,
#   the auto-memory kicks in: cluster the low-distance deltas, write ONE
#   higher-order consolidated delta that references them, and mark the
#   members consolidated so recall skims the long-term structure first.
#
#   Short-term = unconsolidated delta files. Long-term = the consolidated
#   delta(s) that subsume them. The threshold is the kick-in condition
#   (like theta rollover triggering a stamp — after enough accumulates,
#   the dump happens).
#
# Usage: consolidate.sh [ONT_ROOT]   (ONT_ROOT defaults to ~/.config/opencode/ontology)
# Env:  CONSOLIDATE_AT=<n>  (default 8: fire when >=8 unconsolidated deltas)
#       DRY_RUN=1           (default: actually writes; DRY_RUN=1 prints plan only)
#
# Safety: never rewrites history — deltas are never deleted or edited; the
# members stay, marked consolidated in the ledger. The consolidated delta
# is the long-term structure layered on top.

set -u
ONT="${1:-$HOME/.config/opencode/ontology}"
IDX="$ONT/META-LOG.md"
CONS_DIR="$ONT/META-LOG-consolidated"
LEDGER="$ONT/META-LOG-consolidated.tsv"
AT="${CONSOLIDATE_AT:-8}"

[ -f "$IDX" ] || { echo "no index: $IDX" >&2; exit 1; }

# ---- who is unconsolidated? (all deltas minus those already in the ledger) ----
consolidated_ids=$(test -f "$LEDGER" && awk -F'\t' '{split($4,a,","); for(i in a) print a[i]}' "$LEDGER" || true)
active_rows=$(mktemp)
awk -F'|' '/^\| [0-9][0-9]* /{gsub(/ /,"",$2); gsub(/^ /,"",$3); gsub(/ /,"",$4); gsub(/^ /,"",$5); print $2 "\t" $3 "\t" $4 "\t" $5}' "$IDX" | while IFS=$'\t' read -r id date topic file text; do
    if ! echo "$consolidated_ids" | grep -qx "$id"; then printf '%s\t%s\t%s\t%s\n' "$id" "$topic" "$file" "$text"; fi
done > "$active_rows"

total=$(wc -l < "$active_rows")
echo "consolidate: unconsolidated deltas: $total (threshold $AT)"

[ "$total" -ge "$AT" ] || { echo "  below threshold — no dump yet (short-term not full)"; rm -f "$active_rows"; exit 0; }

# ---- comparator: build the overlap graph (distance = token-set overlap) ----
#     grouped by topic stem: deltas sharing a topic keyword sit low-distance.
norm() { echo "$1" | tr 'A-Z' 'a-z' | tr -cs 'a-z0-9_' '\n' | grep -vE '^(sh|a|an|the|of|to|in|on|for|and|or|is|are|it|we|i|not|no|will|by|its|this|that|from|at|as|be|with|was|a)$' | sort -u; }

# cluster key: the most-common topic among the unconsolidated set,
# computed by counting topic keywords across the set.
counts=$(mktemp)
while IFS=$'\t' read -r id topic file text; do
    for kw in $(echo "$topic" | tr '-' '\n'); do echo "$kw"; done
done < "$active_rows" | sort | uniq -c | sort -rn > "$counts"
top_kw=$(head -1 "$counts" | awk '{print $2}')
n_top=$(head -1 "$counts" | awk '{print $1}')
echo "  dominant topic keyword: '$top_kw' (appears $n_top× among unconsolidated)"

# the cluster = deltas whose topic or text carries the dominant keyword
members=$(while IFS=$'\t' read -r id topic file text; do
    if echo "$id $topic $text" | grep -qiE "[^a-z]$top_kw|^$top_kw"; then echo "$id $topic $file"; fi
done < "$active_rows")
n_members=$(echo "$members" | grep -c . || echo 0)
[ "$n_members" -ge 2 ] || { echo "  no mergeable cluster (need >=2 members sharing dominant keyword)"; rm -f "$active_rows" "$counts"; exit 0; }

echo "  cluster: $n_members deltas around '$top_kw'"
echo "$members" | sed 's/^/    /'

if [ "${DRY_RUN:-0}" = "1" ]; then
    echo "  DRY RUN — would write consolidated delta + ledger rows"
    rm -f "$active_rows" "$counts"; exit 0
fi

# ---- write the consolidated (long-term) delta ----
mkdir -p "$CONS_DIR"
DATE=$(date +%Y-%m-%d)
CONS_ID=$(printf "C%03d" "$(( $(ls "$CONS_DIR" 2>/dev/null | wc -l) + 1 ))")
CONS_FILE="$CONS_DIR/${CONS_ID}-${DATE}-${top_kw}.md"
{
    echo "# $CONS_ID — consolidated: $top_kw ($DATE)"
    echo
    echo "Long-term structure: AUTO-MEMORY dump at threshold ($total unconsolidated ≥ $AT) —"
    echo "the short-term deltas below were consolidated into this structure."
    echo
    echo "## Members (short-term merged)"
    echo "$members" | awk '{printf "- %s  %s  (%s)\n", $1, $3, $2}'
    echo
    echo "## Shared thread"
    echo "$members" | while read -r id topic file; do
        txt=$(awk -F'|' '{gsub(/ /,"",$2); if($2==id){gsub(/^ /,"",$6); gsub(/^ /,"",$7); print $6 " " $7}}' id="$id" "$IDX")
        [ -n "$txt" ] && echo "- [$id] $txt"
    done
    echo
    echo "## Nature"
    echo "Consolidation reuses compatibility; members remain in the store (never"
    echo "rewritten). Recall reads this consolidated delta before descending into"
    echo "members. Re-bursting a member (new high-overlap reference) pulls it"
    echo "back to hot regardless of its mtime."
} > "$CONS_FILE"
[ -s "$CONS_FILE" ] || { echo "ERROR: consolidated delta write failed" >&2; rm -f "$active_rows" "$counts"; exit 1; }

# ---- ledger (append-only): mark members consolidated ----
echo -e "${CONS_ID}\t${DATE}\t${top_kw}\t$(echo "$members" | awk '{printf "%s,", $1}' | sed 's/,$//')" >> "$LEDGER"
chmod 644 "$CONS_FILE" 2>/dev/null

echo "  WROTE $CONS_FILE"
echo "  ledger: members → $CONS_ID appended to $(basename "$LEDGER")"
rm -f "$active_rows" "$counts"