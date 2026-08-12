#!/bin/sh
# crew-context.sh - SessionStart hook.
#
# If a crew is installed (a team README exists), remind the session of the
# roster and the routing doctrine. If no crew is installed yet, do nothing.
#
# Portability contract (applies to every hook in this kit):
#   - POSIX sh only. No bash-isms, no jq, no node, no python.
#   - No machine-specific paths. Only $CLAUDE_PROJECT_DIR, $HOME, and
#     ${CLAUDE_PLUGIN_ROOT} are ever referenced.
#   - Fail open: any missing file or unexpected state exits 0 silently.
#     A hook must never break a session on a machine it wasn't written on.

set -u

readme=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -f "${CLAUDE_PROJECT_DIR}/.claude/agents/README.md" ]; then
  readme="${CLAUDE_PROJECT_DIR}/.claude/agents/README.md"
elif [ -f "${HOME}/.claude/agents/README.md" ]; then
  readme="${HOME}/.claude/agents/README.md"
fi

# No crew installed: stay silent.
[ -n "$readme" ] || exit 0

# Pull the roster table (markdown table lines) out of the team README.
# Cap it so a huge README can't flood the context.
roster=$(grep '^|' "$readme" 2>/dev/null | head -30) || true
[ -n "$roster" ] || exit 0

cat <<EOF
## Crew installed

This machine has a chief-of-staff crew installed (see $readme):

$roster

Routing doctrine: route cross-cutting work through the chief-of-staff
orchestrator; single-domain work goes straight to that division lead. The
orchestrator can only delegate when it runs as the MAIN session (for example
\`claude --agent chief-of-staff\`): a subagent cannot spawn subagents.
EOF

exit 0
