#!/usr/bin/env bash
# guard-repo.sh — the sanctuary rule before every push.
# Scans staged changes (and optionally the whole tree) for anything that must
# never reach the public repo: credentials, tokens, private server identifiers
# and paths. Exits non-zero when it finds a hit, so it can run as a pre-push
# hook and REFUSE the push.
#
# Two layers:
#   1. GENERIC patterns (committed here — safe to be public):
#        * GitHub fine-grained PATs          github_pat_
#        * Alpaca style API keys             ^(AK|PK)[A-Z0-9]{16,}$
#        * long high-entropy lookalikes      [A-Za-z0-9_-]{32,} next to "key/secret/token"
#        * absolute private home paths       ^/home/<user>/
#        * ssh key references                ~/.ssh/ or .ssh/private
#   2. LOCAL deny-list (scripts/.git-guard-deny, GITIGNORED — never committed):
#        one regex per line, e.g. the server IP, the SSH port, passphrases.
#
# Wire as a hook:  ln -s ../../scripts/guard-repo.sh .git/hooks/pre-push
# or run manually:  bash scripts/guard-repo.sh          (whole tree)
#                   bash scripts/guard-repo.sh --cached  (staged only)

set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1

GENERIC_PATTERNS=(
  'github_pat_[A-Za-z0-9_]+'
  '(^|[^A-Za-z])(AK|PK)[A-Z0-9]{16,}([^A-Za-z]|$)'
  '(api[_-]?key|secret|token|password|passphrase)[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9_./+=-]{16,}'
  '(^|[[:space:]])/home/[a-z][a-z0-9_-]*/'
  '\.ssh(/|)(id_|quineai)'
  ':6336([^0-9]|$)'
)

LOCAL_DENY="$PWD/scripts/.git-guard-deny"
DENY_PATTERNS=()
if [ -f "$LOCAL_DENY" ]; then
  while IFS= read -r line; do
    [ -n "${line:-}" ] && [[ "$line" != \#* ]] && DENY_PATTERNS+=("$line")
  done < "$LOCAL_DENY"
fi

SCAN_TARGET() {
  if [ "${1:-}" = "--cached" ]; then
    git diff --cached -- . || true
  else
    git ls-files -z | xargs -0 -I{} sh -c '[ -f "{}" ] && cat "{}" || true'
  fi
}

hits=0
for pat in "${GENERIC_PATTERNS[@]}" "${DENY_PATTERNS[@]}"; do
  while IFS= read -r m; do
    hits=$((hits+1))
    printf '  DENIED %-28s %s\n' "$pat" "$(printf '%s' "$m" | cut -c1-90)"
  done < <(SCAN_TARGET "${1:-}" | grep -aoE "$pat" || true)
done

if [ "$hits" -gt 0 ]; then
  echo "guard-repo: $hits sensitive match(es) found — push REFUSED. Sanctuary rule."
  exit 1
fi
echo "guard-repo: clean (no sensitive content detected)"
exit 0