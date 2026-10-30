#!/bin/sh
# crew-version-check.sh: at session start, one line when the installed crew is
# older than this kit. Runs from the plugin's hooks/hooks.json. Silent when no
# crew is installed, when the crew is current, and inside golden-task test runs.
#
# The installer and update-crew write the kit version into
# <scope>/crew-kit-version (.claude/ for a project crew, ~/.claude/ for a global
# one). A crew without that file was installed before v0.7.0.

[ "${CREW_TEST_MODE:-}" = "1" ] && exit 0
ROOT=${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
KIT=$(sed -n 's/^[[:space:]]*"version"[[:space:]]*:[[:space:]]*"\([0-9][0-9.]*\)".*/\1/p' \
  "$ROOT/.claude-plugin/plugin.json" 2>/dev/null | head -n 1)
[ -n "$KIT" ] || exit 0

PROJECT=${CLAUDE_PROJECT_DIR:-$PWD}
FOUND=""
MARK=""
for dir in "$PROJECT/.claude" "$HOME/.claude"; do
  if [ -f "$dir/crew-kit-version" ]; then
    FOUND=$dir
    MARK=$(tr -d ' \r\n' < "$dir/crew-kit-version" | sed 's/^[vV]//')
    break
  fi
  if [ -f "$dir/agents/chief-of-staff.md" ]; then
    FOUND=$dir
    break
  fi
done
[ -n "$FOUND" ] || exit 0

older() { # older A B: succeeds when version A is older than version B
  awk -v a="$1" -v b="$2" 'BEGIN {
    n = split(a, x, "."); m = split(b, y, "."); k = (n > m) ? n : m
    for (i = 1; i <= k; i++) { p = x[i] + 0; q = y[i] + 0
      if (p < q) exit 0
      if (p > q) exit 1 }
    exit 1 }'
}

case "$MARK" in
  "") FROM="a version before 0.7.0" ;;
  *[!0-9.]*) FROM="an unknown version" ;;
  *) older "$MARK" "$KIT" || exit 0; FROM="v$MARK" ;;
esac

printf '{"systemMessage":"chief-of-staff-kit: your crew was installed from %s and the kit is now v%s. Ask your chief of staff to update the crew; it backs everything up first.","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"The installed crew (%s) is older than chief-of-staff-kit v%s. If the user asks to update, migrate or refresh the crew, use the update-crew skill."}}\n' \
  "$FROM" "$KIT" "$FROM" "$KIT"
exit 0
