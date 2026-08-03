# chief-of-staff-kit

**A customisable team of AI agents for Claude Code and Codex.** Install a
**chief-of-staff** orchestrator that triages your work and routes it to **division
leads** and **specialists** — all scaffolded to fit *your* org through a short
interview. No two installs look the same.

![A chief-of-staff orchestrator routing to division leads, each fanning out to specialist agents](assets/hero.jpg)

---

## Explore the live system

[Open the live, read-only BluPlai whiteboard](https://app.bluplai.com/public/whiteboards/wb_haSCnp3ySzExZDzSiJeIhpqh41P89AAGQj83QvplK1o)
to explore the native, editable release workflow from the private AIOS to the public
kit. It needs no BluPlai account, and changes to the board appear there live.

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
   product-designer · ops-steward · content-engine
   web-builder · video-editor · skool-writer-and-publish     ← 13 specialists
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

You need [Claude Code](https://claude.com/claude-code). Then it's about two minutes:

1. **Add the marketplace:**
   ```text
   /plugin marketplace add skyremote/chief-of-staff-kit
   ```
2. **Install the plugin:**
   ```text
   /plugin install chief-of-staff-kit@skyremote
   ```
   (Or run `/plugin`, choose **Browse marketplaces**, and install **chief-of-staff-kit**
   from the menu.)
3. **Restart** Claude Code (start a new session) so the plugin loads.
4. **Tell Claude:** `install the crew`. The installer interviews you (or reads your
   existing `CLAUDE.md`), shows you a plan to approve, then writes your agents into your
   project (`.claude/agents/`) or globally (`~/.claude/agents/`).
5. **Restart once more**, then invoke `@chief-of-staff` for anything cross-cutting.

## Update an existing crew

If you installed an earlier version, you do not need to reinstall your team or lose its
customisation:

```text
/plugin marketplace update skyremote
/plugin update chief-of-staff-kit@skyremote
/reload-plugins
/chief-of-staff-kit:update-crew
```

The updater inventories the agents already present, previews the exact changes, preserves
your divisions and workspace rules, and only writes after you approve the plan. Version
0.2 adds the content-engine, web-builder, video-editor and skool-writer-and-publish
templates, native Codex custom agents, and an advisor adoption runbook.

To configure Anthropic's advisor primitive after updating, run:

```text
/chief-of-staff-kit:advisor
```

### Manual install (no marketplace)

```bash
git clone https://github.com/skyremote/chief-of-staff-kit
cp -r chief-of-staff-kit/skills/install-crew ~/.claude/skills/
```

Then ask Claude to **install the crew**.

## Codex

The same personas render as native Codex custom agents under `.codex/agents/` or
`~/.codex/agents/`, plus a root `AGENTS.md` that requests delegation for genuinely
independent work. Current Codex releases can spawn these agents in the desktop app, CLI
and IDE; the default depth remains one level, which keeps the chief-of-staff pattern
predictable. The installer can still emit legacy prompt files when it detects an older
Codex release.

## How it works

1. **Reads before it asks** — if you have a `CLAUDE.md` / `AGENTS.md`, the installer
   proposes a draft org from it rather than interrogating you cold.
2. **Interviews** — confirms your divisions, which specialists to include, any
   integration agents to opt into, your house style, and where to install.
3. **Renders** — fills the templates, injects your house style into every agent,
   regenerates the orchestrator's roster, and writes a team `README`.
4. **Updates safely** — on later runs, inventories the installed roster and preserves
   customised facts while bringing the operating doctrine and available roles forward.

Everything is plain Markdown. There's no build step — the "rendering" is the
installer model following [`skills/install-crew/SKILL.md`](skills/install-crew/SKILL.md).

## What's in here

```
.claude-plugin/        plugin + marketplace manifests
skills/install-crew/
  SKILL.md             the installer (interview → render → write)
  templates/           the canonical agent personas (generic, placeholder-driven)
  references/          how to render for Claude Code and Codex
skills/update-crew/    in-place updater for existing installations
skills/advisor/        advisor adoption and verification runbook
assets/                README art
```

## License

[MIT](LICENSE). Use it, fork it, make it yours.
