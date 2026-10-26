# Rendering the crew for Claude Code

How the installer turns the templates into a working one-loop crew after the
interview: one main-loop agent, a folder of skills, three helper agents, hook
gates in settings, a golden-task file and a team README.

---

## 1. Choose the install scope

| Scope | Agents | Skills | Hook scripts | Settings |
|---|---|---|---|---|
| **Project** | `<ws>/.claude/agents/` | `<ws>/.claude/skills/` | `<ws>/.claude/hooks/` | `<ws>/.claude/settings.json` |
| **Global** | `~/.claude/agents/` | `~/.claude/skills/` | `~/.claude/hooks/` | `~/.claude/settings.json` |

Pick one scope for the whole crew. Project scope suits a crew tied to one
workspace and can be committed with it; global scope suits a personal crew used
from any directory. If a project and a global item share a name, Claude Code
prefers the personal (global) skill and the project agent; avoid relying on
either and keep names unique.

Personal skills load in local terminal and desktop Code sessions, not in Cowork
or cloud sessions. Check those surfaces separately.

## 2. The non-git caveat

Project-scoped agents and skills are discovered reliably inside a **git
repository**. In a plain or synced folder they may not load. Then either prefer
global scope, suggest `git init "<workspace>"`, or author in the workspace and
mirror to global (and note in the README that the mirror must be re-synced after
edits). Say which you did.

---

## 3. The main loop (`templates/main-loop.md` → `agents/chief-of-staff.md`)

It stays an agent file so it can be the main session (`claude --agent
chief-of-staff`, or the front-door `agent` key). Fill:

| Token | Filled with |
|---|---|
| `{{DIVISION_SKILLS}}` | One line per installed division skill: `- <slug>: <domain>` |
| `{{FORK_SKILLS}}` | The installed own-context skill names, comma-separated. If none, delete that paragraph |
| `{{GOLDEN_TASKS_PATH}}` | Path to the written `golden-tasks.md` |
| `{{WORKSPACE_CONTEXT}}` | The rendered house-style block (see §7) |

Do not list the craft skills in the body: their one-line descriptions are
already in the session's skill listing. Leave out `tools` and `model`, as in
v0.5.0, so connected tools stay available and the session's model applies.

## 4. Skills

A skill is a folder with a `SKILL.md` (YAML frontmatter, then instructions) and
optional referenced files. Claude sees each skill's `description` at all times
and loads the body only when the skill is used; referenced files load only when
the body points the model at them. That is the progressive disclosure the crew
relies on.

**Division skills.** Copy `templates/skills/division/` to
`skills/<division-slug>/` for each division and fill:

| Token | File | Filled with |
|---|---|---|
| `{{DIVISION_SLUG}}` | SKILL.md | kebab-case name, unique across skills |
| `{{DIVISION_NAME}}` | all | display name |
| `{{DOMAIN}}`, `{{WHAT_IT_IS}}` | SKILL.md | the domain and a one-line description |
| `{{OWNS}}`, `{{DOES_NOT_OWN}}` | SKILL.md | the edges, so the main loop loads the right skill |
| `{{FILING}}` | SKILL.md | where this division's artefacts go |
| `{{KEY_FACTS}}`, `{{SOURCES_OF_TRUTH}}` | facts.md | one fact per line with its source |
| `{{PEOPLE}}` | people.md | roles, owners, who decides |
| `{{VOICE}}` | voice.md | tone, register, words to use and avoid |
| `{{OPEN_WORK}}` | open-work.md | live commitments, owners, next steps |

Anything unknown becomes `- To fill: <what is needed>`, never a guess.

**Craft skills (inline).** Copy each chosen folder. Fill `{{DEFAULT_STACK}}`
(architecture), `{{FILING_MAP}}` (back-office) and `{{INTEGRATION_SETUP}}`
(email, inbox, notes, memory-harvest). The integration note names the
capability, the one-time wiring and the instruction to say plainly when it is
not wired. Do not hardcode one vendor as the only option.

**Own-context skills (`context: fork`).** `web-build`, `video-edit`,
`course-publish` and `content-engine` carry `context: fork` in their frontmatter.
Read what that does before describing it to the user:

- Claude Code starts a **new subagent** and gives it the skill body as its prompt.
  The docs are explicit that, despite the name, this is *not* a fork of the
  current conversation: the subagent does not see the conversation history. The
  arguments the main loop passes are substituted at `$ARGUMENTS`, which is why
  each of these skills opens with the brief and stops if it is incomplete.
- Its tool calls stay out of the main window; only its result comes back. That
  is the point for tool-heavy jobs.
- It runs in the background by default (Claude Code 2.1.218 or later). Add
  `background: false` if the user wants the turn to wait for the result.
- `agent:` selects the subagent type; the default is `general-purpose`.
- Fill `{{WORKSPACE_CONTEXT}}` in these four: they do not inherit it.

This is different from a **fork helper** (`subagent_type: "fork"`, or
`/subtask <task>` by hand), which *does* inherit the whole conversation, shares
the main session's prompt cache and cannot start further forks. Forks are on by
default in the terminal from Claude Code 2.1.232 and in `-p`, the Agent SDK, the
desktop app and VS Code from 2.1.302. The main loop uses forks for side tasks
that need what it already knows; it uses the own-context skills for heavy jobs
with a clean brief. `CLAUDE_CODE_FORK_SUBAGENT=0` turns fork mode off;
`"Agent(fork)"` in `permissions.deny` stops only forks.

**Frontmatter rules for every skill.** `name` matches the folder, lowercase and
hyphens. `description` leads with the use case; description plus `when_to_use`
is truncated at 1,536 characters in the listing. Do not add `allowed-tools`
as a sandbox: it pre-approves tools for the invoking turn and does not restrict
which tools are available. Keep each `SKILL.md` short: after compaction Claude
Code re-attaches each invoked skill only up to its first 5,000 tokens, within a
shared 25,000-token budget, newest first. From 2.1.304 the skill list itself is
sent again after compaction, and `/reload-skills` sends only new or changed
skills.

## 5. Helper agents

Agents are single Markdown files with YAML frontmatter. Keep the three that need
a different context from the main loop:

| Agent | Why it is separate | Frontmatter that matters |
|---|---|---|
| `code-reviewer` | Must not inherit the builder's assumptions; sees only the spec and the diff | `effort: high`, `disallowedTools: Edit, Write, NotebookEdit`, `omitClaudeMd: true` (2.1.271+) unless the user's CLAUDE.md holds standards it must apply |
| `verifier` | Knows only the user flow; checks what a user experiences | `disallowedTools: Edit, Write, NotebookEdit` |
| `researcher` | Needs nothing from the main loop; keeps raw reading out of it | no `effort`: the main loop passes one per call |

Field rules:

- **`effort`** sets how hard the helper thinks (`low`, `medium`, `high`, `xhigh`,
  `max`, depending on the model). The main loop can also pass `effort` on each
  Agent call (2.1.292+), which overrides the frontmatter. Precedence: the
  `CLAUDE_CODE_EFFORT_LEVEL` environment variable, then the per-call parameter,
  then frontmatter, then the session level. It does not apply to forks, which
  run exactly as the main session does.
- **`autoCompactWindow`** (2.1.296+) lets one helper compact earlier, for
  example `autoCompactWindow: 200000` on a researcher that reads long logs.
  Write a plain integer; `200k` is read as 200 and ignored.
- **`tools` / `model`**: leave out, as in v0.5.0. `disallowedTools` is a
  behaviour boundary, not a sandbox: Bash and connected tools can still write.
- **`color`**: one of `red`, `blue`, `green`, `yellow`, `purple`, `orange`,
  `pink`, `cyan`.
- Keep private facts out of every `description`.

## 6. Hook gates

Hard rules live in hooks, not in prose. Claude Code runs a hook every time its
event fires, whether or not the model remembers the rule.

**Write order:** back up the settings file to
`settings.json.bak-YYYYMMDD-HHMMSS`; copy the chosen scripts to the hooks
directory and `chmod +x` them; parse the settings JSON; append the approved
entries under `hooks.PreToolUse` without touching anything else; write; parse
again. Never print the full settings file.

**Example block** (project scope; for global scope use `$HOME/.claude/hooks/...`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(git push *)",
            "command": "\"${CLAUDE_PROJECT_DIR}\"/.claude/hooks/gate-protected-push.sh ask \"main release/*\"",
            "timeout": 10,
            "onFailure": "block",
            "statusMessage": "Checking the push gate"
          },
          {
            "type": "command",
            "if": "Bash(git commit *)",
            "command": "\"${CLAUDE_PROJECT_DIR}\"/.claude/hooks/gate-secrets-in-commit.sh deny",
            "timeout": 20,
            "onFailure": "block",
            "statusMessage": "Checking the commit for secrets"
          }
        ]
      },
      {
        "matcher": "mcp__<mail-server>__send.*",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PROJECT_DIR}\"/.claude/hooks/gate-confirm.sh \"sending email\" ask",
            "timeout": 10,
            "onFailure": "block"
          }
        ]
      }
    ]
  }
}
```

**How the pieces work** (from the Claude Code hooks reference):

- `matcher` filters the tool name. Letters, digits, `_`, `-`, `|` and `,` are an
  exact name or list; anything else is an unanchored regular expression, so
  `mcp__<server>__send.*` matches that server's send tools. Use the real server
  and tool names found in Step 1.
- `if` is one permission rule such as `Bash(git push *)`. It checks each
  subcommand of a compound command, but it is best-effort and `git -C dir push`
  does not match `Bash(git push *)`. The scripts filter the command themselves,
  so dropping `if` widens coverage at the cost of running the script on every
  Bash call.
- **`"onFailure": "block"`** (Claude Code 2.1.295 or later) makes a gate that
  cannot start, times out, exits with an unexpected code or prints invalid JSON
  **block** the action. Without it, a broken or slow gate lets the action through.
  The scripts need `jq` or `python3`; without either they exit 1, which blocks.
  That is why the `if` filters matter: they keep a broken gate from blocking
  unrelated commands.
- Exit 2 blocks and feeds stderr to Claude. Exit 0 with
  `"permissionDecision": "ask"` prompts the user.

**Choosing ask or deny.** `ask` shows the user a permission prompt with the
gate's reason, and the docs state that a hook's `ask` still forces a prompt in
auto mode. In a `claude -p` run nobody can answer, so calls that would prompt are
denied. Behaviour under bypass-permissions mode is not documented: if the user
runs that way, use `deny` (the gate blocks and the main loop asks the user in
chat; the user then runs the action themselves or approves it explicitly).
Secrets default to `deny`.

**Test every gate before you finish** by piping a sample input into the script
as Claude Code would, in a scratch repository, never against the user's real
remote:

```bash
printf '%s' '{"tool_name":"Bash","cwd":"/tmp/gate-test","tool_input":{"command":"git push origin main"}}' \
  | .claude/hooks/gate-protected-push.sh deny; echo "exit $?"   # expect 2
printf '%s' '{"tool_name":"Bash","cwd":"/tmp/gate-test","tool_input":{"command":"ls"}}' \
  | .claude/hooks/gate-protected-push.sh deny; echo "exit $?"   # expect 0
```

Then, in the new session, confirm one live block during the first drive.

**Other irreversible actions** from the interview (writing to a live database,
payments, deploys, deletions) use `gate-confirm.sh "<label>" ask|deny` behind a
matcher for the tool that performs them, for example the database MCP server's
write tools or `"if": "Bash(psql *)"`.

## 7. `{{WORKSPACE_CONTEXT}}`

Render the user's house style once as a short block: spelling variant (do not
assume one), emoji policy, versioning, filing notes and standing rules. Paste
the identical block into the main loop, the four own-context skills and the
three helpers. Inline skills do not carry it; they run inside the main loop. If
the user gave no house style, render "No specific house style configured:
follow the user's lead and ask if unsure."

## 8. Golden tasks, README and QUICKSTART

Write `golden-tasks.md`, `README.md` (from `team-readme-template.md`, filling
`{{ROSTER_TABLE}}`) and `QUICKSTART.md` into the agents directory. The roster
table has one row per installed item:

```markdown
| Name | Kind | Runs | Use when |
|---|---|---|---|
| chief-of-staff | main loop | main session | Always: plans and does the work |
| business-one | division skill | inline | Work for Business One |
| decks | craft skill | inline | Slides are needed |
| web-build | own-context skill | own context, background | Building and shipping a site |
| code-reviewer | helper agent | fresh window, effort high | Before a consequential change ships |
| gate-protected-push | hook gate | every matching push | Push to main or release |
```

## 9. Restart

Agents, skills and settings load at session start. Tell the user to start a
new session (or run `/reload-skills` and `/reload-plugins`), then run
`claude --agent chief-of-staff`.

## Quick checklist

- [ ] Scope chosen; non-git caveat handled.
- [ ] Every token filled; grep for leftover `{{`.
- [ ] Every frontmatter block parses; skill `name` matches its folder.
- [ ] `{{WORKSPACE_CONTEXT}}` in the main loop, own-context skills and helpers only.
- [ ] Settings backed up; only `hooks` (and `agent` if chosen) changed; JSON parses.
- [ ] Each gate tested with a matching and a non-matching input.
- [ ] No real names, brands, domains, emails or personal paths in shipped text.
- [ ] README, QUICKSTART and `golden-tasks.md` written; user told to restart.

---

## Legacy shape (v0.5 agents, on request only)

If the user asks for the v0.5 shape, render from `templates/legacy/` as v0.5.0
did: `legacy/orchestrator.md` as `chief-of-staff`, `legacy/division-lead.md`
once per division (`{{LEAD_NAME}}`, `{{LEAD_SLUG}}`, `{{DOMAIN}}`,
`{{WHAT_IT_IS}}`, `{{OWNS}}`, `{{DOES_NOT_OWN}}`, `{{KEY_FACTS}}`, `{{HANDOFFS}}`,
`{{LEAD_COLOR}}`), the chosen `legacy/specialists/` and `legacy/comms/` agents
(`{{DEFAULT_STACK}}`, `{{FILING_MAP}}`, `{{INTEGRATION_SETUP}}`), and
`{{WORKSPACE_CONTEXT}}` in every agent. Regenerate the orchestrator's
`{{LEADS_LIST}}` and `{{SPECIALISTS_LIST}}` from the agents actually written. No
`tools` allowlists and no `model` pins. Hook gates (§6) and golden tasks (§8)
apply unchanged; recommend running the golden tasks against both shapes before
the user settles on the legacy one.
