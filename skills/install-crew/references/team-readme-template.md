# The crew — org chart & operating rules

Your installed agent team: one **orchestrator**, one or more **division leads**, and
a bench of shared **specialists**. Each agent's personality, scope, and hand-offs
live in its own agent file (`*.md` for Claude Code, `*.toml` for Codex). This README is the map: who's who, when
they work alone vs together, and how to run them.

## Where these live

These agent files live in your agents directory. Claude Code and Codex load agent
configuration at session start — edits take effect on the **next** session. If
you move or add an agent file, keep it in this same directory so it is discovered.

## The org chart

```
                          YOU
                           │
                      orchestrator        ← talk to this; it routes & synthesises
                           │
         ┌─────────────────┼─────────────────┐
       lead              lead              lead          ← your division leads
         └─────────────────┼─────────────────┘
                           │  (any lead pulls in any specialist)
                  ───── shared specialists ─────         ← cross-cutting roles
```

The root session does most ordinary work itself. It brings in a lead or
specialist when you ask for one or when a separate agent adds clear value.
Leads own a domain; specialists own a craft. A lead can ask a specialist to
handle a distinct part of its brief when its client permits nested agents;
otherwise the root coordinates that hand-off.

## The roster

{{ROSTER_TABLE}}

Some agents are **setup-dependent** — they rely on an integration (email, notes,
meeting transcripts, memory stores) that you must wire up before they can do their
job. Those agents degrade gracefully: when an integration is not connected, they say
plainly what is missing rather than fabricating a result. See each agent's own file
for the setup it needs.

## When they work alone vs together

**Default: the current session works directly.** Use one specialist for a task
that needs that role's context or access. Run independent work together only
when doing so improves the result or saves time.

**Sequential (a chain):** when one agent's output feeds the next. A lead supplies the
facts → a specialist turns them into the deliverable → a reviewer checks it. Or an
architect sets the design → code gets written against it → a reviewer audits it. Run
these in order, passing each result forward to the next agent. The point of a chain
is dependency, not consensus.

**Together (a council):** only for genuinely high-stakes or ambiguous calls where
independent viewpoints reduce error — a pricing decision, an architecture choice, a
go/no-go. Convene **2–3 agents with different vantage points** (e.g. an architect, a
strategist, and the owning lead), let each assess independently, then have the
orchestrator reconcile their views into one recommendation. **Do not** run councils on
simple or objective questions — it wastes effort and can make the answer worse by
manufacturing disagreement where there is none.

**Generator + reviewer.** One agent produces an important deliverable (code,
deck, plan), and a different agent checks it when an independent review adds
value. Keep the files and review scope explicit. Routine checks stay with the
agent doing the work.

## How to run them

- **Claude Code CLI:** run `claude --agent chief-of-staff` for an orchestrated
  session. An optional `agent` setting makes that the default for bare `claude`.
  Pin unattended `claude -p` jobs to the agent they require.
- **Claude desktop Code tab:** start a new local session in the workspace where
  the crew was installed. It reads the same local agent files and settings as
  the CLI. Ask for a named lead or specialist; verify one real delegation in
  the Tasks pane. Chat, Cowork and cloud sessions have separate extension
  loading and need their own installation check.
- **Codex app, CLI or IDE:** the root reads the team section of `AGENTS.md`.
  Ask it to use a named specialist when you want that role. Custom agents are
  configured in `.codex/agents/` or `~/.codex/agents/`; `codex --agent` is not
  the entry point on current builds. Check one actual spawned agent in the
  client you use.

## Adding and editing agents

Add a new agent in the native format for this directory, keep each agent's scope
non-overlapping with the others, and add a row to the roster above so the team stays
legible. When a new domain appears that no existing lead owns, give it its own lead
rather than overloading an unrelated one.
