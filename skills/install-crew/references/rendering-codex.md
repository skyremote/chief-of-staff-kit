# Rendering the crew for Codex

This reference tells the installer how to render the crew templates for **Codex**.
Read it before generating any Codex output.

## The mechanism gap (read this first)

Codex has **no auto-orchestrating subagent system**. There is no equivalent of Claude
Code's automatic delegation, and **subagents cannot be spawned**. A single Codex agent
runs the session; it cannot fan work out to a team that executes in parallel under it.

So parity with the Claude Code crew is **content parity, not mechanism parity**. We
reproduce the *thinking* — the roles, the heuristics, the output contracts, the routing
and alone-vs-council doctrine — and make it invokable by hand. We do **not** promise
automatic delegation, because Codex cannot do it. Be honest about this everywhere it
matters; do not imply a capability the runtime lacks.

What this means in practice:
- Each persona becomes a prompt the user **invokes manually**.
- The routing doctrine becomes **documentation the user (or the single agent) reads and
  applies by hand**, not an engine that dispatches.
- "Council" sessions are run by the single agent **playing each role in turn**, or by the
  user pasting personas in sequence — not by concurrent agents.

## What to generate

For Codex, produce two things:

1. **One prompt file per persona** under `~/.codex/prompts/<role>.md`.
2. **One root `AGENTS.md`** that documents the whole team, the roster, and the full
   routing / alone-vs-council doctrine.

### 1. Persona prompt files — `~/.codex/prompts/<role>.md`

Write each persona (orchestrator, every division lead, every specialist, every comms
agent) as its own file under `~/.codex/prompts/`. Use the persona's kebab-case slug as
the filename, e.g. `~/.codex/prompts/architect.md`, `~/.codex/prompts/ops-steward.md`.

These files become **invokable, slash-style prompts** inside Codex: the user calls a
persona by name to load that operating doctrine into the current session. Author them so
they read as a direct instruction to the agent ("You are the … You do … You hand off
to …").

Conversion rules for each file:
- **Strip the Claude Code YAML frontmatter.** Codex prompt files are plain prompt bodies,
  not subagent definitions. Drop the `name / description / tools / model / color` block.
  If a short title line helps the user identify the prompt, use a plain Markdown heading
  at the top instead.
- **Keep the full body** — role, heuristics, working style, output contract, and the
  hand-off map. This is the substance that carries over; preserve its bite.
- **Rewrite hand-offs as manual instructions.** Where the Claude Code persona says it
  "hands off to" or "delegates to" another agent, phrase it as: *recommend the user
  invoke the `<other-role>` prompt next*, or *switch to the `<other-role>` persona*. Make
  clear the agent is naming the next role, not silently dispatching to it.
- Keep `{{WORKSPACE_CONTEXT}}` and any other placeholders inline (see "Placeholders"
  below) — they are filled identically to the Claude Code path.

### 2. Root `AGENTS.md`

Write a single `AGENTS.md` at the workspace root. Codex reads `AGENTS.md` automatically as
standing context, so this is where the team lives as a whole. It must contain:

- **A team overview** — what the crew is and how it is meant to be used in Codex.
- **The roster** — every persona with its one-line scope, plus the exact prompt-file path
  (`~/.codex/prompts/<role>.md`) so the user knows what to invoke.
- **The full routing doctrine** — the same orchestrator routing logic from the Claude Code
  build (which role owns what, who to reach for given a request type), written so the
  single agent can self-route or the user can pick the right persona.
- **The alone-vs-council doctrine** — when one role is enough, and when a decision wants
  several roles weighing in. In Codex, spell out that a "council" is run by the single
  agent **playing each role in turn** (or the user invoking each persona in sequence and
  synthesising), since concurrent subagents do not exist.
- **Two ways to use a persona**, stated plainly:
  1. Invoke the prompt file by its slash-style name to load that role, or
  2. Paste the persona body directly into the conversation.

**Mandatory honesty note in `AGENTS.md`.** Include an explicit statement that
**auto-delegation is a Claude Code feature** and that **in Codex the personas are invoked
manually** — the agent does not spawn or dispatch a team on its own. Do not soften this;
a user must not expect automatic orchestration that the runtime cannot deliver.

## Placeholders

Fill placeholders **exactly as in the Claude Code path** — same tokens, same source
values. Nothing about Codex changes how placeholders resolve.

- `{{WORKSPACE_CONTEXT}}` — inject into **every** persona prompt file and into `AGENTS.md`:
  the user's house style (language variant, emoji policy, deliverable versioning),
  workspace/filing notes, and standing rules. Never hardcode a house style; it comes only
  from this token.
- `{{LEADS_LIST}}`, `{{SPECIALISTS_LIST}}` — render into the `AGENTS.md` roster.
- Division-lead tokens (`{{LEAD_NAME}}`, `{{LEAD_SLUG}}`, `{{DOMAIN}}`, `{{WHAT_IT_IS}}`,
  `{{OWNS}}`, `{{DOES_NOT_OWN}}`, `{{KEY_FACTS}}`, `{{HANDOFFS}}`, `{{LEAD_COLOR}}`) — fill
  per lead. `{{LEAD_COLOR}}` has no rendering effect in Codex (there is no agent colour
  swatch); carry it only if a persona body references it, otherwise drop it.
- `{{DEFAULT_STACK}}` (architect), `{{FILING_MAP}}` (ops-steward),
  `{{INTEGRATION_SETUP}}` (comms agents), `{{ROSTER_TABLE}}` (the `AGENTS.md` roster) —
  same substitutions as the Claude Code build.

## Integration-dependent personas

Comms and other integration-dependent personas carry an `{{INTEGRATION_SETUP}}` note.
Render it unchanged: the persona describes its capability generically and is instructed to
**say plainly when its integration is not wired** rather than fabricate a result. Codex
does not change this contract — if the underlying integration is absent, the persona
states so.

## Output summary

| Target | Where it goes | Frontmatter? |
|---|---|---|
| Each persona prompt | `~/.codex/prompts/<role>.md` | No — plain prompt body |
| Team / roster / doctrine | `AGENTS.md` (workspace root) | No — plain Markdown |

Keep the Codex output lean and declarative, matching the voice of the source personas.
The win is reproducing the crew's *thinking* in a runtime that cannot orchestrate — so be
faithful to the doctrine and honest about the mechanism.