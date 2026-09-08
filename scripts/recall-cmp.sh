#!/usr/bin/env bash
# recall-cmp.sh — comparator-based recall with the feedback loop built in.
# Ranking is NOT a stored score. Distance = token-set overlap between the
# query and each delta's topic+shift text. The low-distance/high-overlap tail
# IS the relevance set — and the consolidation candidate set.
#
# FEEDBACK LEG (the memory of remembering): this tool does not just read —
# every query APENDS a trace line to META-LOG-traces.tsv (the record of being
# used) and RE-BURSTS by WEIGHTED LOTTERY (touch restores mtime, reversing the
# one-way thermodynamic clock: use makes a delta hot again). Ranking is not
# good/bad, so selection is not argmax — each delta's re-burst probability is
# proportional to its rank, floored at 5%, so no delta is ever hard-excluded.
# Use → revive → more use → revive. That is the loop closed.
#
# Usage:
#   recall-cmp.sh "<query>" [ONT_ROOT]
#   ONT_ROOT defaults to ~/.config/opencode/ontology
#   TRACE=0 disables trace+re-burst (pure read). Default: loop on.
#
# Output: ranked list of deltas, highest overlap first, with the overlap
# ratio. The top of this list is "what is this query about, among what I
# already hold."

set -u
Q="$1"
ONT="${2:-$HOME/.config/opencode/ontology}"
IDX="$ONT/META-LOG.md"
TRACE_FILE="$ONT/META-LOG-traces.tsv"

[ -n "$Q" ] || { echo "usage: recall-cmp.sh \"<query>\"" >&2; exit 1; }
[ -f "$IDX" ] || { echo "no index: $IDX" >&2; exit 1; }

norm() { echo "$1" | tr 'A-Z' 'a-z' | tr -cs 'a-z0-9_' '\n' | grep -vE '^(sh|a|an|the|of|to|in|on|for|and|or|is|are|it|we|i|not|no|will|by|its|this|that|from|at|as|be|with|was)$' | sort -u; }

tokens=$(norm "$Q")
qtok_count=$(echo "$tokens" | grep -c . || true)

echo "query: \"$Q\"  (unique tokens: $qtok_count)"
echo "rank  overlap  id  topic   (overlap = shared tokens / union)"
echo "------------------------------------------------------------"

# parse only data rows: id($2), topic($4), shift-text($6) — the SHIFT is the
# memory itself; topic alone would rank on filenames.
RANKED=$(awk -F'|' '/^\| [0-9]+ /{gsub(/ /,"",$2); gsub(/ /,"",$4); gsub(/^ /,"",$6); print $2, $4, $6}' "$IDX" |
    while read -r id topic text; do
        dtokens=$(norm "$id $topic $text")
        shared=$(comm -12 <(echo "$tokens") <(echo "$dtokens") | wc -l)
        union=$( { echo "$tokens"; echo "$dtokens"; } | sort -u | wc -l)
        [ "$union" -eq 0 ] && union=1
        overlap=$(awk -v s="$shared" -v u="$union" 'BEGIN{printf "%.3f", s/u}')
        printf "%s %s %s %s\n" "$overlap" "$shared" "$id" "$topic"
    done |
    sort -rn)

echo "$RANKED" | awk '{printf "  %-4s %-7s %s  %s\n", NR, $1, $3, $4}'

# ---- feedback leg: trace the access, re-burst by WEIGHTED LOTTERY ----
# Ranking is not good/bad, so selection is not argmax. Each ranked delta
# enters a stochastic draw with probability proportional to its overlap
# relative to the top, floored at 5% — the tail always keeps a chance.
# The numbers become tendencies, not hard gates. No delta is ever
# deterministically excluded or guaranteed.
if [ "${TRACE:-1}" = "1" ] && [ -n "$RANKED" ]; then
    top_overlap=$(echo "$RANKED" | head -1 | awk '{print $1}')
    reburst_ids=""
    while read -r ov shared id topic; do
        p=$(awk -v o="$ov" -v top="$top_overlap" 'BEGIN{
            if (top<=0) {print 0.05; exit}
            pp=o/top; if (pp<0.05) pp=0.05; print pp}')
        roll=$((RANDOM % 1000))
        hit=$(awk -v p="$p" -v r="$roll" 'BEGIN{print (r/1000 < p) ? "yes" : "no"}')
        [ "$hit" = "yes" ] && reburst_ids="$reburst_ids $id"
    done <<< "$RANKED"
    reburst_ids=$(echo $reburst_ids | tr ' ' ',')
    echo -e "$(date -Is)\t$Q\t$reburst_ids" >> "$TRACE_FILE" 2>/dev/null
    echo "trace: appended to $(basename "$TRACE_FILE")"
    if [ -n "$reburst_ids" ]; then
        echo "  lottery drew: ${reburst_ids#?}"
        for id in $(echo "$reburst_ids" | tr ',' ' '); do
            nnn=$(printf "%03d" "$id" 2>/dev/null)
            f=$(find "$ONT/META-LOG" -maxdepth 1 -name "${nnn}-*.md" 2>/dev/null | head -1)
            if [ -n "$f" ]; then
                touch "$f"
                echo "  re-burst: $id -> $(basename "$f") (mtime resurrected)"
            fi
        done
    else
        echo "  lottery drew no one this draw"
    fi
fi