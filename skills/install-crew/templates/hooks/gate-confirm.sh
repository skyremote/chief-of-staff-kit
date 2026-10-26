#!/bin/sh
# gate-confirm.sh: hold one kind of irreversible action for the user.
#
# Use it for actions with no safe automatic check: sending email, writing to a
# live database, making a payment, publishing. The settings entry chooses WHICH
# tool calls reach this script (matcher plus, in Claude Code, `if`); this script
# only decides how to hold them.
#
# Usage:  gate-confirm.sh "<label>" [ask|deny]
#   ask  (default) ask the user to confirm in the permission prompt (Claude Code).
#   deny block the call and tell the agent to stop and ask the user.
#        Use deny for Codex, for unattended `claude -p` runs, and wherever
#        you have not checked that `ask` prompts in your permission mode.
#
# Exit codes: 0 with JSON = ask; 2 = blocked; anything else = the gate itself
# failed, which Claude Code treats as a block when the hook sets
# "onFailure": "block".

LABEL=${1:-"an irreversible action"}
MODE=${2:-ask}
INPUT=$(cat)

if command -v jq >/dev/null 2>&1; then
  TOOL=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty') || exit 1
elif command -v python3 >/dev/null 2>&1; then
  TOOL=$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_name",""))') || exit 1
else
  echo "gate-confirm: needs jq or python3 to read the hook input" >&2; exit 1
fi

REASON=$(printf 'Gate: %s (%s). Confirm with the user before this runs.' "$LABEL" "${TOOL:-unknown tool}" | tr -d '"\\')

if [ "$MODE" = "ask" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"%s"}}\n' "$REASON"
  exit 0
fi
echo "$REASON Stop, tell the user exactly what you were about to do, and wait. Do not look for another route." >&2
exit 2
