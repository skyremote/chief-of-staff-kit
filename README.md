# chief-of-staff-kit

**A customisable team of AI agents for Claude Code and Codex.** Install a
**chief-of-staff** orchestrator that triages your work and routes it to **division
leads** and **specialists** — all scaffolded to fit *your* org through a short
interview. No two installs look the same.

![A chief-of-staff orchestrator routing to division leads, each fanning out to specialist agents](assets/hero.jpg)

---

## What you get

One team shape, instantiated to fit anyone:

```
                    chief-of-staff            ← triages, routes, synthesises
        ┌───────────────┼───────────────┐
     lead A           lead B           lead C  ← one lead per "division"
        └───────────────┼───────────────┘
                 (any lead pulls in any specialist)
   architect · code-auditor · program-manager · problem-solver
   presentation-writer · voice-scriptwriter · growth-marketer
   product-designer · ops-steward                              ← 9 specialists
   inbox-reader · email-writer · notes-archivist · memory-harvester  ← 4 opt-in comms
```

A **"division"** is whatever unit you run: a business, a department, a team, a
product line, a client portfolio, or a person you manage. You might have four
companies; someone else has two departments and five reports. The installer learns
*your* structure and generates one lead per division, then wires the chief-of-staff
to route across exactly that team.

The value isn't the names — it's the **operating doctrine** baked into each agent:
clean-brief delegation, explicit ownership boundaries, "work alone vs convene a
council", generator-plus-reviewer pairing, and decisive synthesis instead of a menu
of options.

## Install (Claude Code)

```text
/plugin marketplace add skyremote/chief-of-staff-kit
/plugin install chief-of-staff-kit@skyremote
```

Then just tell Claude:

> **install the crew**

The `install-crew` skill runs an interview (or reads your existing `CLAUDE.md`),
confirms a plan, and writes your agents into your project (`.claude/agents/`) or
globally (`~/.claude/agents/`). Start a new session and invoke `@chief-of-staff`.

### Manual install (no marketplace)

```bash
git clone https://github.com/skyremote/chief-of-staff-kit
cp -r chief-of-staff-kit/skills/install-crew ~/.claude/skills/
```

Then ask Claude to **install the crew**.

## Codex

The same personas render for [Codex](https://github.com/openai/codex) too: each
agent becomes an invokable prompt under `~/.codex/prompts/`, plus a root `AGENTS.md`
that documents the team and the routing doctrine. Be aware of one honest limitation —
Codex has no auto-orchestrating subagent system, so in Codex you invoke the personas
manually; the content ports, the automatic delegation does not.

## How it works

1. **Reads before it asks** — if you have a `CLAUDE.md` / `AGENTS.md`, the installer
   proposes a draft org from it rather than interrogating you cold.
2. **Interviews** — confirms your divisions, which specialists to include, any
   integration agents to opt into, your house style, and where to install.
3. **Renders** — fills the templates, injects your house style into every agent,
   regenerates the orchestrator's roster, and writes a team `README`.

Everything is plain Markdown. There's no build step — the "rendering" is the
installer model following [`skills/install-crew/SKILL.md`](skills/install-crew/SKILL.md).

## What's in here

```
.claude-plugin/        plugin + marketplace manifests
skills/install-crew/
  SKILL.md             the installer (interview → render → write)
  templates/           the canonical agent personas (generic, placeholder-driven)
  references/          how to render for Claude Code and Codex
assets/                README art
```

## License

[MIT](LICENSE). Use it, fork it, make it yours.
