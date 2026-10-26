# Design notes

The kit ships **one canonical set of generic templates** plus an **installer
skill** that renders them, customised, into the user's environment. Templates are
the single source of truth; the installer is the only moving part.

## Why templates, not bundled agents and skills

Claude Code plugins *can* ship live agents and skills, but those are identical
for everyone. The point here is per-user customisation (your divisions, your
house style, your irreversible actions). So everything ships as **templates
inside the installer skill**, and the installer fills them per install.

## One loop (v0.6.0)

Up to v0.5.0 the kit rendered an org chart: an orchestrator agent, one lead agent
per division and a bench of specialist agents. v0.6.0 renders one main loop that
does the work, with the knowledge it needs as skills. The reasoning:

- **Hand-offs drop decisions.** Every agent boundary is a summary written by one
  model for another. Anthropic's article *Building agents: When to fold
  subagents into your main agent loop* (22 October 2026) lists the failure modes
  this causes in larger systems: lost context, sprawl, conflicting stitched
  prompts, piecemeal evals and latency.
- **Most roles are knowledge or procedure, not a different context.** A
  division's facts and voice are needed *inside* the loop that writes the email.
  That is what a skill is for: a one-line description always visible, the body
  and its referenced files loaded only when used.
- **Some roles really do need a different context**, and those stay agents. The
  test is the one question: does what the main loop knows help, hurt, or not
  matter? It hurts a reviewer (shared blind spots), so `code-reviewer` and
  `verifier` get fresh windows. It does not matter to research, so `researcher`
  runs clean and keeps its reading out of the main context.
- **Tool-heavy jobs** (site builds, video edits, course publishing, content
  runs) are skills with `context: fork`. Despite the name, Claude Code runs such
  a skill in a **new subagent** whose prompt is the skill body; it does not see
  the conversation. Its tool output stays out of the main window and only its
  result returns. So each of these skills opens with the brief (`$ARGUMENTS`)
  and stops if the brief is incomplete. This is the "call as a tool" pattern,
  distinct from a **fork helper** (`subagent_type: "fork"`, `/subtask`), which
  inherits the whole conversation and shares its prompt cache.
- **Hard rules are hooks.** A rule the model must never break belongs in a
  PreToolUse hook, which runs every time, with `"onFailure": "block"` so a gate
  that crashes or times out blocks the action rather than waving it through.
- **Measure, then keep.** Golden tasks (ten, with "done" lines, two runs before
  and after) decide whether any change to the crew stays. That includes this
  shape: the legacy agents ship alongside for anyone whose numbers say otherwise.

## The division abstraction

A "division" is intentionally abstract: a business, department, team, product,
client book or a report. One parameterised skill template (`SKILL.md` plus
`facts.md`, `people.md`, `voice.md`, `open-work.md`) is instantiated per
division. The `SKILL.md` stays short because, after compaction, Claude Code
re-attaches each invoked skill only up to its first 5,000 tokens within a shared
25,000-token budget; detail lives in the referenced files.

## Where the house style lives

`{{WORKSPACE_CONTEXT}}` is rendered once and placed in the main loop, the four
own-context skills and the three helpers: the pieces that run with their own
prompt. Inline skills do not repeat it, because they run inside the main loop
and every repeated line costs re-attachment budget.

## Placeholder catalogue

| Token | Scope | Filled with |
|---|---|---|
| `{{WORKSPACE_CONTEXT}}` | main loop, own-context skills, helpers | house style + standing rules |
| `{{DIVISION_SKILLS}}`, `{{FORK_SKILLS}}`, `{{GOLDEN_TASKS_PATH}}` | main loop | the installed roster and eval path |
| `{{DIVISION_SLUG}}` … `{{OPEN_WORK}}` | division skill | per-division details |
| `{{DEFAULT_STACK}}` | architecture | the user's default stack |
| `{{FILING_MAP}}` | back-office | where things get filed |
| `{{INTEGRATION_SETUP}}` | email, inbox, notes, memory-harvest | which integration to wire |
| `{{ROSTER_TABLE}}` | team README | the generated roster |
| `{{LEADS_LIST}}`, `{{SPECIALISTS_LIST}}`, `{{LEAD_*}}` | legacy templates only | as in v0.5.0 |

## Two render targets, one source

`references/rendering-claude-code.md` emits an agent file for the main loop,
skill folders, helper agents and a hooks block. `rendering-codex.md` emits a team
section in `AGENTS.md`, skills under `.agents/skills/`, custom-agent TOML for the
helpers and heavy jobs, and `hooks.json`. Codex hooks have no `ask` and no
failure policy, so Codex gates deny and fail open; the reference says so.

## Upgrade contract

The installer owns first-time rendering. `update-crew` owns existing
installations: it inventories before writing, preserves user-specific facts and
workspace context, audits each role (fold, merge, call as a tool, keep), backs up
the whole crew with a restore note, and folds one role at a time against the
golden tasks. Plugin version bumps are required because Claude Code uses the
manifest version as the update cache key.

## Provenance

Generalised from a working multi-venture agent team and its move to one loop.
Every template was authored from structure and heuristics only and scrubbed so the
published kit carries **no** real names, businesses, clients, domains, paths or
usage data, only the reusable operating doctrine.
