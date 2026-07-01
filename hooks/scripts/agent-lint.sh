#!/bin/sh
# agent-lint.sh - PostToolUse hook (Write|Edit|MultiEdit).
#
# When an agent file under .claude/agents/ is written or edited, verify the
# kit's own install checklist automatically:
#   1. no leftover {{TOKEN}} placeholders (a surviving token is a bug), and
#   2. frontmatter carries the required `name:` and `description:` fields.
#
# On a violation it exits 2 with the reason on stderr, which feeds the problem
# back to the model to fix. For any file that is not a crew agent file, and in
# any unexpected state, it exits 0 silently.
#
# Portability contract: POSIX sh only; no jq/node/python; no machine-specific
# paths; fail open.

set -u

input=$(cat 2>/dev/null) || exit 0

# Extract the written file's path from the hook JSON without jq. The
# tool_input of Write/Edit/MultiEdit always carries "file_path": "...".
file_path=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)

[ -n "$file_path" ] || exit 0

# Only lint markdown agent files inside a .claude/agents/ directory.
case "$file_path" in
  *"/.claude/agents/"*.md) ;;
  *) exit 0 ;;
esac
case "$file_path" in
  *README.md) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

errors=""

if grep -q '{{' "$file_path" 2>/dev/null; then
  tokens=$(grep -o '{{[A-Z_]*}}' "$file_path" | sort -u | tr '\n' ' ')
  errors="${errors}- Leftover template placeholder(s): ${tokens}. Every {{TOKEN}} must be filled before an agent ships.
"
fi

# Frontmatter must open at line 1 and carry name: and description:.
first_line=$(head -1 "$file_path")
if [ "$first_line" != "---" ]; then
  errors="${errors}- Missing YAML frontmatter (file must start with ---).
"
else
  frontmatter=$(awk 'NR==1{next} /^---$/{exit} {print}' "$file_path")
  printf '%s\n' "$frontmatter" | grep -q '^name:[[:space:]]*[a-z0-9][a-z0-9-]*[[:space:]]*$' || \
    errors="${errors}- Frontmatter needs a kebab-case \`name:\` (lowercase letters, digits, hyphens).
"
  printf '%s\n' "$frontmatter" | grep -q '^description:[[:space:]]*..*' || \
    errors="${errors}- Frontmatter needs a \`description:\` (Claude uses it to decide when to invoke the agent).
"
fi

if [ -n "$errors" ]; then
  printf 'Agent file %s failed the crew lint:\n%s' "$file_path" "$errors" >&2
  exit 2
fi

exit 0
