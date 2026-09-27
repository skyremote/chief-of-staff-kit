---
name: install-crew
description: Install and customise a team of AI agents (a chief-of-staff orchestrator that routes to division leads and specialists) into the user's own project or global config. Interviews the user about their business, departments, teams, products, or the people they manage — or reads their existing CLAUDE.md / AGENTS.md — then renders a tailored crew for Claude Code and/or Codex. Use when the user wants to "install the crew", "set up the agent team", "build my chief of staff", "scaffold agents for my business", or runs this kit for the first time.
---

# Install the crew

This skill turns a set of generic agent templates into a **customised team of agents
for the person installing it** — wired to their org, their house style, their tools.

The team is one shape, instantiated to fit anyone:

```
                    chief-of-staff            ← orchestrator: triages, routes, synthesises
        ┌───────────────┼───────────────┐
     lead A           lead B           lead C  ← one "lead" per division (see below)
        └───────────────┼───────────────┘
                 (any lead pulls in any specialist)
   architect · code-auditor · program-manager · problem-solver
   presentation-writer · voice-scriptwriter · growth-marketer
   product-designer · ops-steward · content-engine
   web-builder · video-editor · skool-writer-and-publish      ← shared specialists
   inbox-reader · email-writer · notes-archivist · memory-harvester  ← opt-in comms
```

A **"division"** is deliberately abstract. For the installing user it might be a
business, a department, a team, a product line, a client portfolio, or a person they
manage. The installer's job is to learn what *their* divisions are and generate one
lead per division.

**Your job when this skill runs:** conduct a short interview (informed by anything
already in their config), confirm a plan, then write the agent files. Never invent
the user's business facts — ask, or leave a clean placeholder and say so.

---

## Files in this skill

- `templates/orchestrator.md` — the chief-of-staff template.
- `templates/division-lead.md` — ONE lead template, instantiated once per division.
- `templates/specialists/*.md` — the 13 generic specialists.
- `templates/comms/*.md` — the 4 integration-dependent agents (opt-in).
- `references/rendering-claude-code.md` — how to write Claude Code subagents.
- `references/rendering-codex.md` — how to write Codex prompts + AGENTS.md.
- `references/team-readme-template.md` — the team README the installer writes for the user.

Read the relevant rendering reference before you write files. Read each template
before you fill it.

---

## Step 0 — Confirm the target tool(s)

Ask which the user runs (offer both):

- **Claude Code** → render native subagents (`references/rendering-claude-code.md`).
  The same local agent files are available in terminal sessions and local Code
  sessions in the Claude desktop app. Check the Code tab, the selected workspace
  and install scope. Chat and Cowork use account-synced extensions; local
  `~/.claude/agents/` files alone do not prove those surfaces can see the crew.
- **Codex** → render native custom-agent TOML files + a root `AGENTS.md`
  (`references/rendering-codex.md`). Current Codex releases can spawn project or global
  custom agents. Detect the installed Codex version before rendering and use the legacy
  prompt-file fallback in that reference only for an older release without custom agents.
- **Both** → render each from the same answers.

## Step 1 — Read before you ask

Look for context the user has already written, and use it to *propose* a draft org
rather than interrogating them from scratch:

1. Global config: `~/.claude/CLAUDE.md` (and `~/.codex/AGENTS.md` if present).
2. Project config in the current working directory: `CLAUDE.md` and/or `AGENTS.md`.

From whatever exists, extract candidate **divisions** (named businesses, departments,
teams, products), the user's **house style** (language/spelling variant, emoji
policy, versioning rules), a **default tech stack** if mentioned, and any **filing
conventions**. Draft a proposed roster from this. If nothing is found, start clean.

> "I read your config and it looks like you run **A**, **B**, and **C** — should each
> be its own lead? Anything missing?" beats twenty cold questions.

## Step 2 — Interview (confirm and fill the gaps)

Work through these, conversationally, confirming what you inferred in Step 1. Prefer
multiple-choice where you can. Keep it tight.

1. **Divisions** → the list of leads. For each: a display name, the domain it owns,
   a one-line "what it is", what it **owns**, what it explicitly **does not own**,
   the standing facts it must always know, and who it hands off to. A division can be
   a company, a department, a product, a client book, or a report you manage. (If the
   user has only one domain, one lead is fine — the orchestrator still adds value.)
2. **Specialists** → which of the 13 to include (default: all). Drop any that don't
   fit how they work.
3. **Comms agents** (opt-in, default off) → `inbox-reader`, `email-writer`,
   `notes-archivist`, `memory-harvester`. Only install the ones the user wants, and
   for each, capture what integration they'll wire (or note it's unwired).
4. **House style** → spelling/language variant, emoji policy, deliverable versioning,
   any standing "always do X" rules. This becomes `{{WORKSPACE_CONTEXT}}`. **Do not
   assume** a variant or an emoji rule — use what they tell you; if they say nothing,
   render a neutral block.
5. **Default tech stack** (if they build software) → fills the architect's
   `{{DEFAULT_STACK}}`.
6. **Filing map** (if they want ops-steward) → where things get filed; fills
   `{{FILING_MAP}}`.
7. **Install scope** → **project** (`<workspace>/.claude/agents/`) or **global**
   (`~/.claude/agents/`). See the non-git caveat in the rendering reference and pick
   accordingly.
8. **Front door** (optional, default no) → should the orchestrator become the
   DEFAULT local Claude Code session, so a bare `claude` or a new local Code-tab
   session starts with it? Offer it as a real choice: in the kit's tests
   a plain session did everyday work as well as the orchestrator, and
   `claude --agent chief-of-staff` starts the orchestrator whenever they want it. It
   suits people who hand work to the crew most days. If yes, you'll set the `agent`
   key in Step 4.5.

   **Before asking this question, scan for scheduled headless runs** — the `agent`
   key applies to `claude -p` too, so an unattended job would silently start
   booting as the orchestrator. Check and SHOW the user what you find:
   ```bash
   crontab -l 2>/dev/null | grep -n "claude"
   grep -rln "claude -p\|claude --print" ~/Library/LaunchAgents /Library/LaunchAgents 2>/dev/null
   grep -rln "claude -p\|claude --print" <workspace> --include="*.sh" 2>/dev/null
   ```
   (On Linux, check systemd user timers and `/etc/cron*` as well.) Any hit that
   should NOT run as the orchestrator must pin its own agent with
   `--agent <name>` — offer to add the flag for them before enabling the front
   door. Most people with a cron do not remember they have a cron; the scan is
   the point, not the caveat.

## Step 3 — Show the plan, then confirm

Before writing anything, show the user:

- The exact list of agents you'll create (orchestrator + each named lead + chosen
  specialists + any comms agents).
- The target tool(s) and the exact directory(ies) you'll write to.
- A one-line note on scope and (if relevant) the non-git caveat decision.

Wait for a yes. This is the only gate — once confirmed, write everything.

## Step 4 — Render and write

Follow the rendering reference for each target tool. The mechanics:

1. For **each division**, copy `templates/division-lead.md` and fill its tokens
   (`{{LEAD_NAME}}`, `{{LEAD_SLUG}}`, `{{DOMAIN}}`, `{{WHAT_IT_IS}}`, `{{OWNS}}`,
   `{{DOES_NOT_OWN}}`, `{{KEY_FACTS}}`, `{{HANDOFFS}}`, `{{LEAD_COLOR}}`). Give each a
   unique kebab-case `name` (e.g. `lead-<slug>`).
2. Copy each chosen **specialist**; fill `{{DEFAULT_STACK}}` (architect) and
   `{{FILING_MAP}}` (ops-steward) where present.
3. Copy each opted-in **comms** agent; fill `{{INTEGRATION_SETUP}}`.
4. Inject the **same** rendered `{{WORKSPACE_CONTEXT}}` block into **every** agent so
   the whole crew behaves consistently.
5. Copy `templates/orchestrator.md` and regenerate `{{LEADS_LIST}}` and
   `{{SPECIALISTS_LIST}}` **from the roster you actually installed** — not the full
   catalogue.
6. Write the team README from `references/team-readme-template.md`, filling
   `{{ROSTER_TABLE}}` from the installed files.
7. **Grep every written file for a leftover `{{`** — a surviving token is a bug; fix
   it before finishing.

## Step 4.5 — Make it the front door (if opted in)

If the user said yes to the front-door question, wire the orchestrator in as the
default main-loop agent (Claude Code only):

1. **Set the `agent` key** in the chosen scope's settings — `~/.claude/settings.json`
   for global installs, `<workspace>/.claude/settings.json` for project installs:
   ```json
   { "agent": "chief-of-staff" }
   ```
   Merge into the existing file — never overwrite other settings. This swaps the
   main loop to the orchestrator for bare `claude` and new local Code-tab
   sessions in the desktop app. `--agent <name>` overrides it in the CLI.
   Verify the desktop session separately; a settings file alone is not proof
   that the selected app surface loaded it.
2. **VS Code extension caveat** — the extension has no agent setting of its own. If
   the embedded session doesn't pick up the key, the integrated terminal is the
   route. Offer this shell function (NOT a bare alias — that breaks `claude update`
   and `claude --version`):
   ```bash
   claude() {
     if [[ $# -eq 0 ]] || [[ "$1" == -* ]]; then
       command claude --agent chief-of-staff "$@"
     else
       command claude "$@"
     fi
   }
   ```
3. **Headless caveat** — the `agent` key DOES apply to headless `claude -p` runs
   (verified empirically 2026-08-18). Warn the user: any unattended script that
   should NOT run as the orchestrator (crons, render jobs, pipelines) must pin its
   own agent explicitly with `--agent <name>`, or it will silently boot the
   orchestrator and its routing instructions for every scheduled run.
   Revisit the scheduled-run scan from the Step 2 front-door question: every hit
   found there must be pinned (or the user must explicitly accept the change)
   BEFORE you set the key. Nothing errors when this goes wrong — the job just
   quietly becomes a different job — so the scan is the only warning they get.

## Step 5 — Report and tell them to restart

Report what you wrote and where. Then:

- **Claude Code:** start a new terminal or local desktop Code session in the
  selected workspace. Ask for the chief of staff by name for cross-cutting work.
  If the front door is enabled, verify a bare CLI and a new Code-tab session.
- **Codex:** point them at the generated `AGENTS.md` and custom-agent TOML
  files. The root session follows `AGENTS.md`; ask it to use a named specialist.
  Do not claim a `codex --agent` launch path without checking that build's CLI.
- If you mirrored project files to global (non-git workspace), remind them to re-sync
  after edits.

## Step 6 — First drive (do not skip)

An installed crew a user doesn't know how to drive is a failed install. After they
restart, walk them through three checks in their new session, in order:

1. **Discovery check:** in a fresh Claude session, ask for a named lead or
   specialist and confirm it actually runs. In the CLI, use
   `claude --agent chief-of-staff` to check the orchestrator identity. If they
   opted into the front door (Step 4.5), a bare `claude` and a new local
   desktop Code session should also start with that identity. For Codex,
   check that its root session follows the team section of `AGENTS.md` and
   can spawn one named custom agent.
2. **Inline answer:** in an orchestrated session, ask one trivial question from
   their real work. It should be answered directly, with no delegation.
3. **First delegation:** in that session, ask one small real task that clearly
   belongs to a single lead ("ask the <lead> to…"). Point out that naming the
   lead sends the work there and the result comes back as one answer.

Then leave them a `QUICKSTART.md` next to the team README covering: when to talk to
the orchestrator vs a lead directly; that the orchestrator does most work itself and
delegates when they name an agent or the work splits into parallel streams; that very
large jobs spanning many agents run best as a workflow; and where the roster README
lives. Close by telling them the update path: pull the kit's latest and re-run
`update-crew`. If they installed by hand-copying the templates rather than via the
marketplace/plugin, the update path is different — clone or pull the kit's repo and
run `update-crew` from there against their installed agents (see "Hand-copied
installs" in the update-crew skill).

---

## Guardrails

- **Never fabricate the user's facts.** If you don't know a division's details, ask,
  or write a clear placeholder and tell them to fill it. A confidently-wrong fact is
  worse than a gap.
- **Keep descriptions clean.** A local lead description may name its division
  for routing. Keep customer details, private facts, paths and credentials out
  of frontmatter `description`; it is visible when the agent is discovered.
- **Scale the crew to the user.** One division and three specialists is a perfectly
  good crew. Don't push all 18 agents on someone who needs five.
- **Hold the boundaries.** The value of this team is clean ownership and routing —
  keep each lead's "does not own" honest so the orchestrator can route without
  collisions.
