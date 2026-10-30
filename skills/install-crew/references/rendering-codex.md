# Rendering the crew for Codex

Codex gets the same one-loop shape: the root session is the main loop, divisions
and crafts are skills, the three helpers are custom agents, and irreversible
actions are gated by hooks. Codex differs from Claude Code in three places that
matter here: skills have no `context: fork`, hooks have no `ask` and no
`onFailure`, and the root session takes its doctrine from `AGENTS.md`.

## What to generate

| Piece | Project scope | Global scope |
|---|---|---|
| Main-loop doctrine | team section in `<ws>/AGENTS.md` | team section in the workspace's `AGENTS.md` (business facts stay out of global files) |
| Division and craft skills | `<ws>/.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` |
| Helpers and heavy jobs | `<ws>/.codex/agents/*.toml` | `~/.codex/agents/*.toml` |
| Hook gates | `<ws>/.codex/hooks.json` + `<ws>/.codex/hooks/*.sh` | `~/.codex/hooks.json` + `~/.codex/hooks/*.sh` |
| Golden tasks, README, QUICKSTART | next to the agents | next to the agents |

The golden-task runner (`golden.py`) drives Claude Code only. On Codex, write
`golden-tasks.md` and run the tasks by hand, twice before and twice after a
change, each in a fresh session. Test mode cannot be made safe on Codex yet:
its hooks let an action through when they fail, and its sandbox covers only
shell commands, not connected tools.

Never overwrite an existing `AGENTS.md`, `hooks.json` or `config.toml`. Merge a
clearly headed, versioned section or entry and preserve everything else. Back up
each file first.

## Root `AGENTS.md`: the main loop

Render the body of `templates/main-loop.md` (without its frontmatter) as the
team section, with the same tokens filled. Translate Claude-specific language:

- "load the skill" stays: Codex picks a skill when the task matches its
  `description`, or the user mentions it with `$<skill>` or `/skills`.
- "own-context skills" become **custom agents** (see below), so the sentence
  reads "heavy jobs run as the named custom agents, each with a full brief".
- Per-call `effort` and forks are Claude Code features. Replace that line with:
  "Ask a custom agent only when a separate context changes the result."
- Keep the one question (helps, hurts, does not matter), the hooks paragraph,
  the golden-tasks paragraph and "How you answer" as written.

## Skills

Codex reads `SKILL.md` with `name` and `description` in the frontmatter. Copy
each division and inline craft skill folder unchanged after filling tokens, and
drop any Claude-only keys. Optional Codex settings such as
`policy.allow_implicit_invocation` go in a separate `agents/openai.yaml` inside
the skill folder, not in the frontmatter.

## Custom agents (TOML)

Each file needs `name`, `description` and `developer_instructions`:

```toml
name = "code-reviewer"
description = "Independent code reviewer in a fresh window. Sees only the spec and the diff."
sandbox_mode = "read-only"
developer_instructions = """
You are an independent code reviewer...
"""
```

Render as custom agents:

- **The three helpers.** `code-reviewer` and `verifier` get
  `sandbox_mode = "read-only"`; check they can still read what they need. If the
  user wants a stronger reviewer, set `model_reasoning_effort = "high"` on
  `code-reviewer`, the Codex counterpart of `effort: high`.
- **The four heavy jobs** (`web-build`, `video-edit`, `course-publish`,
  `content-engine`). Codex has no `context: fork`, so a separate agent is the
  way to keep their tool output out of the main loop. This is the "call as a
  tool" pattern: the root keeps the conversation, sends a full brief, and gets a
  compact result back. Replace `$ARGUMENTS` in the body with "the brief you were
  given". If the user prefers them inline, render them as plain skills instead
  and drop the `context` key.

Omit `tools`, `color`, `model` and Claude's `effort` and `omitClaudeMd` keys.
Escape any literal triple double quote in a body. Parse every TOML file after
writing it.

## Hook gates

Codex supports `PreToolUse` hooks in `hooks.json` (or inline `[hooks]` in
`config.toml`), with the same JSON input shape (`tool_name`,
`tool_input.command`, `cwd`) for shell commands, `apply_patch` and MCP tools.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^Bash$",
        "hooks": [
          { "type": "command", "command": ".codex/hooks/gate-protected-push.sh deny \"main release/*\"", "timeout": 10, "statusMessage": "Checking the push gate" },
          { "type": "command", "command": ".codex/hooks/gate-secrets-in-commit.sh deny", "timeout": 20 }
        ]
      },
      {
        "matcher": "^mcp__<mail-server>__send.*",
        "hooks": [
          { "type": "command", "command": ".codex/hooks/gate-confirm.sh \"sending email\" deny", "timeout": 10 }
        ]
      }
    ]
  }
}
```

Differences to state plainly to the user:

- **Always `deny`.** Codex does not support `ask` yet. A gate blocks with exit 2
  and the root asks the user in chat.
- **No `if` field.** The matcher is a regular expression on the tool name only,
  so the gate scripts filter the command themselves and exit 0 for anything
  that is not theirs.
- **Gates fail open.** Codex has no `onFailure`; a gate that errors or times out
  is reported and the tool call continues. The docs call tool hooks "a useful
  guardrail, not a complete enforcement boundary". For anything that must never
  happen, also remove the credential or permission that makes it possible.
- **Trust review.** Non-managed hooks must be reviewed with `/hooks` before they
  run, and project hooks load only when the project `.codex/` layer is trusted.
  Tell the user to do this in the first drive.

Test each gate with a matching and a non-matching sample input, as in the Claude
Code reference.

## Verification

1. Confirm the Codex version supports custom agents, skills and hooks.
2. Parse every TOML and JSON file; check every skill has `name` and `description`.
3. Grep all output for `{{`.
4. In a fresh session in each client the user will use: ask one division task
   (the skill should load), ask the root to use `researcher`, and trigger one
   gate in a scratch repository after `/hooks` review.
5. Report the directories written and the backups taken.

## Legacy shape and older builds

For the legacy v0.5 shape, render the agents in `templates/legacy/` as custom
agents and the legacy orchestrator body as the `AGENTS.md` team section. Only
when the installed Codex lacks custom agents, render personas as Markdown under
`.codex/prompts/` and say those roles are invoked by hand.
