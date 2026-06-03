# The crew — org chart & operating rules

Your installed agent team: one **orchestrator**, one or more **division leads**, and
a bench of shared **specialists**. Each agent's personality, scope, and hand-offs
live in its own `*.md` file in this folder. This README is the map: who's who, when
they work alone vs together, and how to run them.

## Where these live

These agent files live in your agents directory. Claude Code loads them at the start
of a session — edits take effect on the **next** session, not the current one. If
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

The shape is the same regardless of how many leads or specialists you installed:
**you talk to the orchestrator, the orchestrator routes to a lead, and any lead can
pull in any specialist.** Leads own a domain; specialists own a craft.

## The roster

{{ROSTER_TABLE}}

Some agents are **setup-dependent** — they rely on an integration (email, notes,
meeting transcripts, memory stores) that you must wire up before they can do their
job. Those agents degrade gracefully: when an integration is not connected, they say
plainly what is missing rather than fabricating a result. See each agent's own file
for the setup it needs.

## When they work alone vs together

**Default: one agent, alone.** Most work is a single clear domain — let one
specialist own it. It is faster, cheaper, and keeps context clean. Reach for more
agents only when the work genuinely needs more than one vantage point.

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

**Generator + reviewer — the highest-value pairing.** One agent produces the work
(code, deck, plan), a **different** agent checks it. Never let a single agent be the
only judge of its own output on anything that matters. This one pattern catches more
real errors than any council, and it is cheap. Make it the default for important
deliverables.

## How to run them

- **Chat (automatic delegation):** just describe the task in a normal session —
  Claude delegates to the right agent based on each agent's `description`. This is the
  usual path; you rarely need to name an agent explicitly.
- **Name or @-mention an agent:** to force a specific agent, ask for it by name
  ("ask the *<lead>* to…") or `@`-mention it. Use this when auto-delegation picks the
  wrong agent or when you want a particular vantage point.
- **Orchestrated session:** run the **orchestrator** as your main session when you
  want it to spawn and coordinate several agents on a cross-cutting task. **A subagent
  cannot spawn subagents** — only the main session can. So any work that needs one
  agent to call others must be driven by the orchestrator (or a lead) running *as the
  main session*, not delegated to it as a subagent.
- **Deep single-domain session:** run a **lead** as your main session for a focused
  work block in that one domain — it keeps full context on that area and can still
  pull in specialists as it goes.

## Adding and editing agents

Add a new agent as a `*.md` file in this directory, keep each agent's scope
non-overlapping with the others, and add a row to the roster above so the team stays
legible. When a new domain appears that no existing lead owns, give it its own lead
rather than overloading an unrelated one.