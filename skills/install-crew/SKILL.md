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
   product-designer · ops-steward                              ← shared specialists
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
- `templates/specialists/*.md` — the 9 generic specialists.
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
- **Codex** → render invokable prompts + a root `AGENTS.md`
  (`references/rendering-codex.md`). Note honestly: Codex has no auto-orchestrating
  subagent system, so in Codex the personas are invoked manually and `AGENTS.md`
  documents the routing doctrine — the *content* ports, the auto-delegation does not.
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
2. **Specialists** → which of the 9 to include (default: all). Drop any that don't
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

## Step 5 — Report and tell them to restart

Report what you wrote and where. Then:

- **Claude Code:** agents load at session start, not mid-session — tell the user to
  start a new session, then invoke `@chief-of-staff` for anything cross-cutting or
  call any agent by `name`.
- **Codex:** point them at the new prompt files and `AGENTS.md`.
- If you mirrored project files to global (non-git workspace), remind them to re-sync
  after edits.

---

## Guardrails

- **Never fabricate the user's facts.** If you don't know a division's details, ask,
  or write a clear placeholder and tell them to fill it. A confidently-wrong fact is
  worse than a gap.
- **Keep the published descriptions clean.** Real names, companies, domains, and
  paths belong in the persona body via `{{WORKSPACE_CONTEXT}}`, never in the
  frontmatter `description` (that string is broadly visible).
- **Scale the crew to the user.** One division and three specialists is a perfectly
  good crew. Don't push all 18 agents on someone who needs five.
- **Hold the boundaries.** The value of this team is clean ownership and routing —
  keep each lead's "does not own" honest so the orchestrator can route without
  collisions.
