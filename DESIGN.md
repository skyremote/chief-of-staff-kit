# Design notes

The kit ships **one canonical set of generic agent personas** plus an **installer
skill** that renders them, customised, into the user's environment. Personas are the
single source of truth; the installer is the only moving part.

## Why templates, not bundled agents

Claude Code plugins *can* ship live agents — but live plugin agents are static and
identical for everyone. The whole point here is per-user customisation (your
divisions, your house style, your stack). So the personas ship as **templates inside
the skill**, and the installer fills them per install. The plugin's only job is to
deliver the installer + templates.

## The division abstraction

Four business leads collapse into **one parameterised `division-lead` template**. A
"division" is intentionally abstract — a business, department, team, product, client
book, or a report — so the same template fits a solo founder with four companies and
a manager with two teams. The installer instantiates it once per division and
regenerates the orchestrator's roster to match.

## Placeholder catalogue

| Token | Scope | Filled with |
|---|---|---|
| `{{WORKSPACE_CONTEXT}}` | every agent | house style + standing rules |
| `{{LEADS_LIST}}` / `{{SPECIALISTS_LIST}}` | orchestrator | the installed roster |
| `{{LEAD_NAME}}` … `{{LEAD_COLOR}}` | division-lead | per-division details |
| `{{DEFAULT_STACK}}` | architect | the user's default stack |
| `{{FILING_MAP}}` | ops-steward | where things get filed |
| `{{INTEGRATION_SETUP}}` | comms agents | which integration to wire |
| `{{ROSTER_TABLE}}` | team README | the generated roster |

## Two render targets, one source

`references/rendering-claude-code.md` emits native subagents. `rendering-codex.md`
emits invokable prompts + an `AGENTS.md` playbook. Codex has no auto-orchestration,
so parity is *content*, not *mechanism* — stated honestly to users.

## Provenance

Generalised from a working four-venture agent team. Every persona was authored from
structure-and-heuristics only and passed through an adversarial privacy scrub so the
published kit carries **no** real names, businesses, clients, domains, paths, or
tooling — only the reusable operating doctrine.
