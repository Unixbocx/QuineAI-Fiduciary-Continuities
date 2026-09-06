#!/usr/bin/env bash
# session-cost.sh — per-message token/cost breakdown for an opencode session.
# Read-only. Never writes to the opencode database.
#
# Usage:
#   ./session-cost.sh                # most recent session
#   ./session-cost.sh <session_id>   # a specific session
#
# Revert: this script does not modify anything. Deleting it is the only revert.

set -euo pipefail

DB="${OPENCODE_DB:-$HOME/.local/share/opencode/opencode.db}"

if [ ! -f "$DB" ]; then
  echo "DB not found at $DB. Override with OPENCODE_DB=/path/to/opencode.db" >&2
  exit 1
fi

SID="${1:-}"

if [ -z "$SID" ]; then
  SID=$(sqlite3 "$DB" "SELECT id FROM session ORDER BY time_updated DESC LIMIT 1;")
  echo "== Session: $SID (most recent) =="
else
  TITLE=$(sqlite3 "$DB" "SELECT title FROM session WHERE id='$SID';")
  echo "== Session: $SID $TITLE =="
fi

sqlite3 -separator $'\t' "$DB" "
SELECT substr(m.id,1,20),
       json_extract(m.data,'\$.role'),
       json_extract(m.data,'\$.mode'),
       json_extract(m.data,'\$.tokens.total'),
       json_extract(m.data,'\$.tokens.input'),
       json_extract(m.data,'\$.tokens.output'),
       json_extract(m.data,'\$.cost')
FROM message m
WHERE m.session_id='$SID'
ORDER BY m.time_created;
" | column -t -s $'\t'

echo
echo "== Summary =="
sqlite3 "$DB" "
SELECT 'turns',            COUNT(*) FROM message
 WHERE session_id='$SID' AND json_extract(data,'\$.role')='assistant'
UNION ALL SELECT 'sum output tok', COALESCE(SUM(json_extract(data,'\$.tokens.output')),0)
 FROM message
 WHERE session_id='$SID' AND json_extract(data,'\$.role')='assistant'
UNION ALL SELECT 'compactions', COUNT(*)
 FROM message
 WHERE session_id='$SID' AND json_extract(data,'\$.mode')='compaction';
" | column -t -s $'\t'