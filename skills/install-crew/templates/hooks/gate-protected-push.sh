#!/bin/sh
# gate-protected-push.sh: hold pushes to protected branches, tag pushes and
# force pushes. Other git pushes and all other commands pass untouched.
#
# Usage:  gate-protected-push.sh [ask|deny] ["<branch globs>"]
#   default branches: "main master release release/*"
#   Example: gate-protected-push.sh deny "main production release/*"
#
# The script filters the command itself, so it is safe behind a plain
# `Bash` matcher (Codex) as well as behind `"if": "Bash(git push *)"`.

set -f   # branch globs are patterns, not filenames
MODE=${1:-ask}
BRANCHES=${2:-"main master release release/*"}
INPUT=$(cat)

get() { # get <key> [<key>...]  -> string value from the hook JSON
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

CMD=$(get tool_input command) || { echo "gate-protected-push: needs jq or python3" >&2; exit 1; }
CWD=$(get cwd) || CWD=.
[ -n "$CMD" ] || exit 0

# Only look at the part of each subcommand from "git ... push" onwards.
PUSHES=$(printf '%s\n' "$CMD" | tr ';&|' '\n\n\n' | grep -E '(^|[[:space:]])git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+push([[:space:]]|$)')
[ -n "$PUSHES" ] || exit 0

is_protected() {
  for g in $BRANCHES; do
    # shellcheck disable=SC2254
    case "$1" in $g) return 0 ;; esac
  done
  return 1
}

HIT=""
OLDIFS=$IFS
IFS='
'
for line in $PUSHES; do
  IFS=$OLDIFS
  args=$(printf '%s' "$line" | sed -E 's/.*[[:space:]]push([[:space:]]|$)//')
  repo_dir=$(printf '%s' "$line" | sed -nE 's/.*git[[:space:]]+-C[[:space:]]+([^[:space:]]+).*/\1/p')
  [ -n "$repo_dir" ] || repo_dir=$CWD
  positional=0; refspec_seen=0
  for a in $args; do
    case "$a" in
      --force|-f|--force-with-lease*|--mirror|--all|--tags|--delete|-d) HIT="$HIT $a" ;;
      -*) ;;
      *)
        positional=$((positional + 1))
        if [ "$positional" -ge 2 ]; then
          refspec_seen=1
          dst=${a#+}; dst=${dst##*:}; dst=${dst#refs/heads/}
          [ -z "$dst" ] && dst=${a%%:*}
          is_protected "$dst" && HIT="$HIT $dst"
        fi ;;
    esac
  done
  if [ "$refspec_seen" -eq 0 ]; then
    cur=$(git -C "$repo_dir" rev-parse --abbrev-ref HEAD 2>/dev/null)
    [ -n "$cur" ] && is_protected "$cur" && HIT="$HIT $cur"
  fi
  IFS='
'
done
IFS=$OLDIFS

[ -n "$HIT" ] || exit 0
REASON=$(printf 'Gate: protected push (%s). Confirm with the user before this runs.' "$(echo $HIT)" | tr -d '"\\')
if [ "$MODE" = "ask" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"%s"}}\n' "$REASON"
  exit 0
fi
echo "$REASON Stop and ask the user; push to a feature branch and open a pull request instead." >&2
exit 2
