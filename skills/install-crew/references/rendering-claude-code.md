# Rendering the crew into Claude Code subagents

This reference explains how the installer turns the templates in this skill into
working Claude Code subagents. It is the step that happens *after* the interview:
you have the answers, now you write files to disk and tell the user how to load
them.

A Claude Code subagent is a single Markdown file with YAML frontmatter. The crew
is just a folder of these files plus one team README. Rendering is mechanical:
pick a scope, copy each template, fill placeholders, write the file, regenerate
the orchestrator's roster lists, write the README, and tell the user to restart.

---

## 1. Choose the install scope

Subagents live in one of two places. Pick one per install (don't split the crew
across both — it fragments the roster and confuses discovery).

| Scope | Path | Visible to |
|---|---|---|
| **Project** | `<workspace>/.claude/agents/` | Claude Code sessions started inside that workspace |
| **Global (user)** | `~/.claude/agents/` | Every Claude Code session on the machine |

Rules of thumb:

- **One workspace, agents specific to it** → project scope. The crew travels with
  the folder, can be committed alongside it, and won't pollute unrelated projects.
- **Agents the user wants everywhere** (a personal operating team they invoke from
  any directory) → global scope.
- **Unsure** → ask in the interview. Default to project scope when the crew
  references workspace-specific context; default to global when it is a general
  personal team.

If both a project and a global agent share the same `name`, the project one wins
inside that workspace. Avoid relying on this — keep names unique.

---

## 2. The non-git caveat (read before choosing project scope)

Claude Code's auto-discovery of **project** agents is reliable inside a directory
that is a **git repository**. In a folder that is *not* a git repo (for example a
synced cloud-drive folder, or a plain working directory), project-scoped agents in
`.claude/agents/` may **not** be picked up automatically.

When the target workspace is not a git repo, do one of the following:

1. **Prefer global scope.** Write the crew to `~/.claude/agents/` instead. This is
   the most robust option and works regardless of the workspace's git status.
2. **Recommend `git init`.** If the user wants the crew to live with the workspace,
   suggest initialising a repo first:

   ```bash
   git init "<workspace>"
   ```

   Then project scope discovers normally.
3. **Mirror to global.** Author the files in the workspace (so they're versioned
   with the project) but also copy them into `~/.claude/agents/` so Claude Code
   finds them. If you do this, note in the README that the global copies must be
   re-synced after edits, or they drift.

State which path you took and why, so the user isn't surprised when an agent does
or doesn't appear.

---

## 3. Frontmatter rules for each subagent

Every agent file begins with YAML frontmatter, then the persona body. The
templates already carry the body; you fill the frontmatter fields.

```markdown
---
name: division-lead-acme
description: Owns everything for the Acme division — strategy, deliverables, and routing within that domain. Invoke when work concerns Acme, its customers, or its roadmap.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
color: blue
---

<persona body starts here>
```

Field rules:

- **`name`** — kebab-case slug, unique across the crew. Lowercase letters, digits,
  hyphens only. This is how the agent is addressed (`@name`, or how the
  orchestrator hands off). Derive it from the role and, for division leads, the
  domain slug: `division-lead-<slug>`, `architect`, `code-auditor`,
  `ops-steward`, etc.
- **`description`** — third person, action-oriented, **trigger-friendly**. This is
  the single most important field: Claude reads it to decide *when* to invoke the
  agent. Lead with what it owns, then "Invoke when …" / "Use for …" cues. Keep it
  one to three sentences. **No real-world names, companies, domains, or paths** —
  if the interview gave you specifics, fold them into the persona body via
  `{{WORKSPACE_CONTEXT}}`, not into the published description.
- **`tools`** — comma-separated list of the tools the agent may use. Grant the
  minimum the role needs:
  - Read-only analysts (auditor, reviewer): `Read, Grep, Glob`.
  - Builders (architect, writers, ops): add `Write, Edit, Bash`.
  - The orchestrator typically needs `Read, Grep, Glob, Task` so it can delegate.
  - Comms agents that depend on an integration also list that integration's tools
    (for example MCP tool names) — but the persona must still degrade gracefully
    when they're absent (see §4, integration note).
  - Omitting `tools` entirely inherits the full default toolset. Prefer being
    explicit.
- **`model`** — `haiku`, `sonnet`, or `opus`, matched to the role's difficulty:
  cheap/fast (`haiku`) for mechanical scouts, `sonnet` for most leads and
  specialists, `opus` for the orchestrator and hard reasoning roles (architect,
  problem solver). When in doubt use `sonnet`.
- **`color`** — a display colour for the agent in the UI. Division-lead templates
  carry a `{{LEAD_COLOR}}` token; fill it from the interview (one of the standard
  Claude Code colours: `red`, `blue`, `green`, `yellow`, `purple`, `orange`,
  `pink`, `cyan`). Give specialists distinct colours so the team is scannable.

---

## 4. Filling placeholders from the interview

The templates are riddled with `{{TOKENS}}`. Replace every one before writing the
file — a leftover `{{TOKEN}}` in a shipped agent is a bug. Source the values from
the interview answers.

### Inject `{{WORKSPACE_CONTEXT}}` into EVERY agent

This is the non-negotiable one. Every template has a `{{WORKSPACE_CONTEXT}}` block.
Replace it in **all** agents with the same rendered context captured in the
interview — the user's house style and standing rules, for example:

- Language / spelling variant to write in (do **not** assume one; use what the user
  stated).
- Emoji policy (allowed or not).
- Deliverable versioning convention, if any.
- Where things get filed / workspace layout notes.
- Any standing "always do X" rules.

Render it once as a short block and paste the identical text into each agent so the
whole crew behaves consistently. Example of a filled block (values are
illustrative — use whatever the interview actually captured):

```markdown
## Working context

- Write in the user's stated spelling variant. Follow the user's stated emoji policy.
- Version deliverables by copying to `_v2` before editing; never overwrite `_v1`.
- File deliverables in the folders the interview captured (e.g. decks under a
  presentations folder, invoices under a finance folder).
- Flag genuine ambiguity rather than guessing.
```

If the user gave no house style, render a minimal neutral block (e.g. "No specific
house style configured — follow the user's lead and ask if unsure") rather than
inventing rules.

### Division-lead tokens

For each division lead the interview names, copy the division-lead template and
fill:

| Token | Filled with |
|---|---|
| `{{LEAD_NAME}}` | Display name of the lead role |
| `{{LEAD_SLUG}}` | kebab-case slug for `name:` |
| `{{DOMAIN}}` | The domain it owns (generic label) |
| `{{WHAT_IT_IS}}` | One-line description of the domain |
| `{{OWNS}}` | What this lead is responsible for |
| `{{DOES_NOT_OWN}}` | Explicit out-of-scope, to keep routing clean |
| `{{KEY_FACTS}}` | Standing facts the lead must always know |
| `{{HANDOFFS}}` | Which specialists/leads it hands off to and when |
| `{{LEAD_COLOR}}` | Frontmatter `color:` |

### Specialist / architect / ops tokens

- **Architect** template has `{{DEFAULT_STACK}}` — fill with the user's chosen
  default tech stack so the architect proposes in their house stack rather than a
  generic one.
- **Ops steward** template has `{{FILING_MAP}}` — fill with where the user files
  things (the folder map captured in the interview).
- **Comms agents** have `{{INTEGRATION_SETUP}}` — fill with a generic note naming
  the *capability* (email send/read, notes sync, calendar, etc.) and the one-time
  wiring the user must do, plus the instruction to **say plainly when the
  integration isn't wired rather than fabricate** a result. Do not hardcode a
  specific vendor as the only option.

After substitution, scan each rendered file for any remaining `{{` — if one
survives, the install is incomplete.

---

## 5. Regenerate the orchestrator's roster lists

The orchestrator (chief-of-staff) template contains two tokens that describe the
*team it can route to*: `{{LEADS_LIST}}` and `{{SPECIALISTS_LIST}}`. These must be
generated **from the roster you actually installed**, not from the full catalogue —
the orchestrator should only know about agents that exist on disk.

After you've decided which agents to write, build the two lists from their
frontmatter:

- **`{{LEADS_LIST}}`** — one line per installed division lead: its `name` and a
  one-line scope drawn from `{{OWNS}}` / the description.
- **`{{SPECIALISTS_LIST}}`** — one line per installed specialist: its `name` and a
  one-line scope.

Rendered example:

```markdown
## Your leads
- division-lead-acme — owns the Acme domain: strategy, deliverables, routing within it.
- division-lead-zenith — owns the Zenith domain: roadmap, customers, delivery.

## Your specialists
- architect — system design and tech decisions in the house stack.
- code-auditor — read-only review for correctness and risk before shipping.
- ops-steward — filing, versioning, and keeping the workspace tidy.
- email-writer — brand-aware outbound drafting (says so plainly if email isn't wired).
```

If the user later adds or removes an agent, **re-render these two lists** so the
orchestrator's map stays accurate. A stale roster makes the orchestrator route to
agents that aren't there.

---

## 6. Write the team README

The team-readme template (`{{ROSTER_TABLE}}`) becomes a human-facing index of the
crew. Write it next to the agents:

- Project scope → `<workspace>/.claude/agents/README.md`
- Global scope → `~/.claude/agents/README.md`

Generate `{{ROSTER_TABLE}}` from the installed files — one row per agent:

```markdown
| Agent | Role | Model | Invoke when |
|---|---|---|---|
| chief-of-staff | Orchestrator | opus | Anything cross-cutting; routes to the right lead/specialist. |
| division-lead-acme | Lead | sonnet | Work concerns the Acme domain. |
| architect | Specialist | sonnet | System design or a tech decision is needed. |
| code-auditor | Specialist | sonnet | Reviewing a change before it ships. |
```

The README should also note: the install scope chosen, the non-git caveat if it
applied (and what you did about it), and how to re-sync if you mirrored to global.

---

## 7. Tell the user to restart

Claude Code loads the agent roster at session start. Files you've just written are
**picked up on the next session, not the current one.** Always end the install with
an explicit instruction:

> The crew is installed in `<path>`. Start a **new** Claude Code session (or
> restart the current one) so the agents load. Then invoke the orchestrator with
> `@chief-of-staff` for anything cross-cutting, or call any agent by its `name`.

If you mirrored project files to global because the workspace isn't a git repo, also
remind the user to re-run the sync after editing any agent, or the loaded global
copies will be stale.

---

## Quick checklist

- [ ] Scope chosen (project vs global); non-git caveat handled.
- [ ] Every template copied; every `{{TOKEN}}` filled (grep for leftover `{{`).
- [ ] `{{WORKSPACE_CONTEXT}}` injected identically into **every** agent.
- [ ] Frontmatter valid on each: kebab-case `name`, trigger-friendly `description`,
      minimal `tools`, right `model`, a `color`.
- [ ] No real-world names, brands, domains, emails, or personal paths in any
      shipped file.
- [ ] Orchestrator `{{LEADS_LIST}}` / `{{SPECIALISTS_LIST}}` regenerated from the
      actual roster.
- [ ] Team README written with `{{ROSTER_TABLE}}`.
- [ ] User told to restart the session.
