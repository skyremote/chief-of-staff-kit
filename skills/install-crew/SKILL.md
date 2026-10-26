---
name: install-crew
description: Install a customised chief of staff for Claude Code and/or Codex in the one-loop shape — one main loop that plans and does the work, one skill per division, craft skills, three helper agents, hook gates for irreversible actions and a golden-task eval. Interviews the user (or reads their CLAUDE.md / AGENTS.md) and renders it into their project or global config. Use when the user wants to "install the crew", "set up my chief of staff", "scaffold agents or skills for my business", or runs this kit for the first time.
---

# Install the crew

This skill turns generic templates into **one main loop with skills, a few
helpers and hard gates**, fitted to the person installing it.

```
                         chief-of-staff              ← main loop: plans, does the work, keeps the context
                               │
   loads skills when needed ───┼─── calls a helper only when a separate context changes the result
                               │
  division skills   Business One · Business Two · …            (facts, people, voice, filing, open work)
  craft skills      architecture · program-plan · problem-solving · decks · voice-scripts
                    growth · product-design · back-office · email · inbox · notes · memory-harvest
  own-context skills web-build · video-edit · course-publish · content-engine   (context: fork)
  helper agents     code-reviewer · verifier · researcher
  hooks             gates on the user's irreversible actions (onFailure: block)
  evals             golden-tasks.md: ten tasks, run twice before and after any change
```

A **division** is whatever unit the user runs: a business, a department, a team,
a product line, a client book, or a person they manage. Each becomes a skill, not
an agent: the main loop sees its one-line summary and opens it when the work
touches that division.

**Your job when this skill runs:** a short interview, one plan to approve, then
write the files. Never invent the user's business facts; ask, or leave a clean
placeholder and say so.

---

## Files in this skill

- `templates/main-loop.md`: the chief of staff (an agent file, run as the main session).
- `templates/skills/division/`: `SKILL.md` plus `facts.md`, `people.md`,
  `voice.md`, `open-work.md`. Instantiated once per division.
- `templates/skills/<craft>/SKILL.md`: twelve craft and comms skills that run
  inline, and four that run in their own context (`context: fork`).
- `templates/agents/`: `code-reviewer`, `verifier`, `researcher`.
- `templates/hooks/`: three example gate scripts.
- `templates/evals/golden-tasks.md`: the eval starter.
- `templates/legacy/`: the v0.5 orchestrator, division-lead, specialist and comms
  agents, for users who ask for the old shape.
- `references/rendering-claude-code.md`, `references/rendering-codex.md`,
  `references/team-readme-template.md`.

Read the rendering reference for each target before writing. Read each template
before filling it.

---

## Step 0 — Target tool(s)

Ask which the user runs (offer both):

- **Claude Code** → `references/rendering-claude-code.md`. Check the version with
  `claude --version`: hook gates with `onFailure` need 2.1.295 or later, the
  per-call `effort` parameter 2.1.292, and forks on by default in `-p`, the SDK,
  desktop and VS Code 2.1.302. Recommend updating if older; the crew still
  installs, but say which parts will not work.
- **Codex** → `references/rendering-codex.md` (skills, custom-agent TOML, root
  `AGENTS.md`, hooks without `ask` or `onFailure`).
- **Both** → render each from the same answers.

## Step 1 — Read before you ask

Read `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md` and the workspace's `CLAUDE.md`
/ `AGENTS.md` if they exist. Draft from them: the divisions, house style
(spelling variant, emoji policy, versioning), default stack, filing conventions,
and anything that sounds irreversible (sending, publishing, paying, deploying,
pushing). Also list any skills and agents already installed, so you can avoid
name collisions and spot an existing crew (if one exists, offer `update-crew`
instead of a fresh install).

> "It looks like you run **A**, **B** and **C**. Should each be its own division
> skill? Anything missing?" beats twenty cold questions.

## Step 2 — Interview

Confirm what you inferred; ask only for gaps. Prefer multiple choice.

1. **Divisions** → one division skill each. For each: name, domain, one line on
   what it is, what it owns and does not own, standing facts and sources of
   truth, people and roles, voice, filing, and open work. Anything the user does
   not know yet becomes a clearly marked "to fill" line, not an invention.
2. **Crafts** → which of the twelve inline skills to include (default: all that
   fit). Drop what doesn't fit how they work.
3. **Own-context skills** → `web-build`, `video-edit`, `course-publish`,
   `content-engine`. Install only those they will use.
4. **Comms integrations** → for `email`, `inbox`, `notes`, `memory-harvest`:
   what is wired (an MCP server, a CLI, nothing yet). Default off.
5. **Helpers** → `code-reviewer` (if they write or ship code), `verifier` (if
   they ship sites or apps), `researcher` (almost everyone). Ask about
   `omitClaudeMd` for the reviewer: on by default so it sees only the spec and
   the diff; off if their `CLAUDE.md` holds coding standards it must apply.
6. **Irreversible actions** → ask: "What should never happen without you saying
   yes?" Prompt with examples: sending email or messages, publishing, pushing to
   a release or main branch, deploying, writing to a live database, payments,
   deleting data, secrets in a commit. For each, capture the tool that does it
   (a Bash command pattern or an MCP tool name) and whether to **ask** or
   **deny**. See "Choosing ask or deny" in the rendering reference; default to
   `deny` if they run with bypass permissions or unattended `claude -p` jobs.
7. **House style** → becomes `{{WORKSPACE_CONTEXT}}`. Do not assume a spelling
   variant or emoji rule; if they say nothing, render a neutral block.
8. **Default stack** (if they build software) and **filing map** (if they use
   `back-office`).
9. **Install scope** → project (`<workspace>/.claude/`) or global (`~/.claude/`).
   See the non-git caveat in the rendering reference.
10. **Front door** (optional, default no) → should `chief-of-staff` become the
    default local Claude Code session? First scan for scheduled headless runs,
    because the `agent` key applies to `claude -p` too, and show what you find:
    ```bash
    crontab -l 2>/dev/null | grep -n "claude"
    grep -rln "claude -p\|claude --print" ~/Library/LaunchAgents /Library/LaunchAgents 2>/dev/null
    grep -rln "claude -p\|claude --print" <workspace> --include="*.sh" 2>/dev/null
    ```
    (On Linux, also check systemd user timers and `/etc/cron*`.) Each hit that
    should not run as the chief of staff must pin `--agent <name>` first.
11. **Shape** → only if the user asks for the old v0.5 shape (an orchestrator
    routing to division-lead and specialist agents), offer the legacy templates.
    Say plainly that v0.6.0 replaces that shape and why (see the kit README).
    Hook gates and golden tasks apply to either shape.

## Step 3 — Show the plan, then confirm

Before writing anything, show:

- every file you will create: the main loop, each division skill folder, each
  craft skill, each helper agent, each gate script, `golden-tasks.md`, the team
  README and QUICKSTART;
- the target directories;
- **the exact `hooks` block you will merge into settings**, and the settings
  file it goes into, with the backup path. Show only the block you add, never
  the rest of the settings file, which may hold secrets;
- any name collision with an existing skill or agent, and the rename you propose;
- the front-door change, if chosen.

Wait for a yes. This is the only gate; once confirmed, write everything.

## Step 4 — Render and write

Follow the rendering reference. In order:

1. **Main loop** from `templates/main-loop.md`: fill `{{DIVISION_SKILLS}}` (one
   line per installed division skill), `{{FORK_SKILLS}}` (the installed
   own-context skill names, or remove that paragraph if none),
   `{{GOLDEN_TASKS_PATH}}` and `{{WORKSPACE_CONTEXT}}`.
2. **Division skills**: copy `templates/skills/division/` once per division to
   `skills/<division-slug>/` and fill every token in all five files.
3. **Craft skills**: copy each chosen folder; fill `{{DEFAULT_STACK}}`,
   `{{FILING_MAP}}`, `{{INTEGRATION_SETUP}}` where present. Inline skills carry
   no workspace block: the main loop already has it.
4. **Own-context skills**: copy and fill `{{WORKSPACE_CONTEXT}}`; they cannot
   see the main loop's context.
5. **Helper agents**: copy, fill `{{WORKSPACE_CONTEXT}}`, apply the reviewer's
   `omitClaudeMd` choice.
6. **Hook gates**: back up the settings file, copy the chosen gate scripts,
   `chmod +x`, merge the approved hooks block, parse the JSON, then test each
   gate as the rendering reference describes.
7. **Golden tasks**: write `golden-tasks.md`. Offer to draft the ten tasks from
   the interview; the user must correct each "done" line.
8. **Team README and QUICKSTART** from `references/team-readme-template.md`.
9. **Grep every written file for a leftover `{{`** and parse every frontmatter
   block. A surviving token is a bug; fix it before finishing.

For the legacy shape, follow "Legacy shape" at the end of the rendering
reference instead of steps 1 to 5.

## Step 4.5 — Front door (if opted in)

Merge `{ "agent": "chief-of-staff" }` into the chosen scope's settings (never
overwrite). Bare `claude` and new local Code-tab sessions then start as the
chief of staff; `--agent <name>` overrides it. The VS Code extension has no
agent setting of its own; if it does not pick up the key, offer this shell
function (not a bare alias, which breaks `claude update`):
```bash
claude() {
  if [[ $# -eq 0 ]] || [[ "$1" == -* ]]; then
    command claude --agent chief-of-staff "$@"
  else
    command claude "$@"
  fi
}
```
Every scheduled `claude -p` hit from the Step 2 scan must be pinned (or the user
must accept the change) before you set the key.

## Step 5 — Report and restart

Report what you wrote and where, and the settings backup path. Tell them to start
a **new** Claude Code session (terminal or local desktop Code tab) or run
`/reload-skills` and `/reload-plugins`, so the agents, skills and hooks load. For
Codex, point to `AGENTS.md`, `.agents/skills/` and `/hooks` for the trust review.

## Step 6 — First drive (do not skip)

In the new session:

1. **Main loop:** `claude --agent chief-of-staff` (or a bare `claude` if the
   front door is on). Ask one real question; it should answer directly.
2. **Skill load:** ask a task for one division. It should load that division
   skill, not call an agent.
3. **Helper:** ask it to review a small diff or research one question. It should
   call `code-reviewer` or `researcher` and keep the conversation.
4. **Gate:** ask for one gated action in a safe form (for example, a push to a
   protected branch in a throwaway repository). The gate must stop it.
5. **Baseline:** run the golden tasks twice and record the result, so the next
   change has something to beat.

Leave a `QUICKSTART.md` next to the team README covering: the main loop does the
work; skills load on demand; the three helpers and when each is used; which
actions are gated and how to change a gate; how to run the golden tasks; and the
update path (`update-crew`).

---

## Guardrails

- **Never fabricate the user's facts.** A confidently wrong fact is worse than a gap.
- **Keep descriptions clean.** A division skill's description may name the
  division so it loads at the right moment; keep customer details, private facts,
  paths and credentials out of every `description`, because it is always in
  context.
- **Keep skills short.** After compaction Claude Code re-attaches each invoked
  skill only up to its first 5,000 tokens, within 25,000 tokens shared across
  skills. Put the important rules at the top of `SKILL.md` and detail in the
  referenced files.
- **Avoid name collisions.** If a skill or agent with the same name already
  exists in either scope, propose a prefix (for example `crew-email`) rather than
  shadowing it.
- **Settings are precious.** Back up before writing, change only the `hooks`
  (and, if chosen, `agent`) keys, never print the file, parse it after writing.
- **Scale the crew to the user.** One division skill, three crafts and a
  researcher is a perfectly good crew.
