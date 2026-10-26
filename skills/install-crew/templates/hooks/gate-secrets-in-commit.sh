#!/bin/sh
# gate-secrets-in-commit.sh: block a git commit whose staged changes look like
# they contain a secret (private keys, common API-key shapes, .env files).
# Other commands pass untouched. It never prints the secret itself.
#
# Usage:  gate-secrets-in-commit.sh [deny|ask]   (default deny)
#
# Pattern matching is a backstop, not a scanner: it catches the common shapes.
# Add your own patterns to EXTRA below.

set -f   # no filename expansion of patterns or paths
MODE=${1:-deny}
EXTRA=''   # e.g. 'mycompany_live_[A-Za-z0-9]{24}'
INPUT=$(cat)

get() {
  if command -v jq >/dev/null 2>&1; then
    path=""; for k in "$@"; do path="$path.$k"; done
    printf '%s' "$INPUT" | jq -r "$path // empty"
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$INPUT" | python3 -c 'import json,sys
d=json.load(sys.stdin)
for k in sys.argv[1:]:
    d=d.get(k,"") if isinstance(d,dict) else ""
print(d if isinstance(d,str) else "")' "$@"
  else
    return 1
  fi
}

CMD=$(get tool_input command) || { echo "gate-secrets-in-commit: needs jq or python3" >&2; exit 1; }
CWD=$(get cwd) || CWD=.
[ -n "$CMD" ] || exit 0

COMMIT=$(printf '%s\n' "$CMD" | tr ';&|' '\n\n\n' | grep -E '(^|[[:space:]])git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+commit([[:space:]]|$)' | head -1)
[ -n "$COMMIT" ] || exit 0

DIR=$(printf '%s' "$COMMIT" | sed -nE 's/.*git[[:space:]]+-C[[:space:]]+([^[:space:]]+).*/\1/p')
[ -n "$DIR" ] || DIR=$CWD
git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1 || exit 0

# Staged changes, plus tracked changes when the commit uses -a / --all.
DIFF=$(git -C "$DIR" diff --cached -U0 --no-color)
FILES=$(git -C "$DIR" diff --cached --name-only)
if printf '%s' "$COMMIT" | grep -Eq '[[:space:]](-a|--all|-[a-zA-Z]*a[a-zA-Z]*)([[:space:]]|$)'; then
  DIFF="$DIFF
$(git -C "$DIR" diff -U0 --no-color)"
  FILES="$FILES
$(git -C "$DIR" diff --name-only)"
fi

# One "label:::extended-regex" per line. Matched against added lines only.
PATTERNS='private key:::-----BEGIN [A-Z ]*PRIVATE KEY-----
AWS access key:::AKIA[0-9A-Z]{16}
GitHub token:::gh[pousr]_[A-Za-z0-9]{36,}
GitHub fine-grained token:::github_pat_[A-Za-z0-9_]{40,}
Slack token:::xox[abposr]-[A-Za-z0-9-]{10,}
sk- style API key:::sk-[A-Za-z0-9_-]{32,}
Google API key:::AIza[0-9A-Za-z_-]{35}
hard-coded credential:::([Aa][Pp][Ii][_-]?[Kk][Ee][Yy]|[Ss][Ee][Cc][Rr][Ee][Tt]|[Tt][Oo][Kk][Ee][Nn]|[Pp][Aa][Ss][Ss][Ww]([Oo][Rr])?[Dd])["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'[:space:]]{16,}'
[ -n "$EXTRA" ] && PATTERNS="$PATTERNS
custom pattern:::$EXTRA"

FOUND=""
ADDED=$(printf '%s\n' "$DIFF" | grep -E '^\+' | grep -vE '^\+\+\+')
OLDIFS=$IFS
IFS='
'
for p in $PATTERNS; do
  label=${p%%:::*}; regex=${p#*:::}
  printf '%s\n' "$ADDED" | grep -Eq -e "$regex" && FOUND="$FOUND; $label"
done
for f in $FILES; do
  case "$f" in
    .env|*/.env|.env.*|*/.env.*|*.pem|*.p12|*id_rsa*|*id_ed25519*)
      case "$f" in *.example|*.sample|*.template) ;; *) FOUND="$FOUND; file $f" ;; esac ;;
  esac
done
IFS=$OLDIFS

[ -n "$FOUND" ] || exit 0
REASON=$(printf 'Gate: possible secret in this commit%s' "$FOUND" | tr -d '"\\' | head -c 400)
if [ "$MODE" = "ask" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"%s"}}\n' "$REASON"
  exit 0
fi
echo "$REASON. Unstage it, move the value to an ignored env file or secret store, and tell the user. Do not bypass this gate." >&2
exit 2
