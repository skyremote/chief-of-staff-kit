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

## Install in Claude Code

You need [Claude Code](https://claude.com/claude-code). Add the plugin in the
client you use:

**Terminal:**

1. Add the marketplace:
   ```text
   /plugin marketplace add skyremote/chief-of-staff-kit
   ```
2. Install the plugin:
   ```text
   /plugin install chief-of-staff-kit@skyremote
   ```
   (Or run `/plugin`, choose **Browse marketplaces**, and install **chief-of-staff-kit**
   from the menu.)
**Claude desktop app:** open **Code** for a local workspace. In **Customize →
Plugins → Add plugin → Add marketplace → Add from a repository**, enter
`https://github.com/skyremote/chief-of-staff-kit`. Install
**chief-of-staff-kit** from that marketplace and start a new local Code session.

Then tell Claude **`install the crew`**. The installer interviews you (or reads your
existing `CLAUDE.md`), shows you a plan to approve, then writes your agents into your
project (`.claude/agents/`) or globally (`~/.claude/agents/`). Start another new
session to load them. In the terminal, `claude --agent chief-of-staff` starts an
orchestrated session. In the desktop Code tab, ask for the chief of staff or a
named specialist and check that a real delegation appears in **Tasks**. The
installer can also make the chief of staff the default local session if you choose.

The local Code tab shares Claude Code's local configuration. Chat, Cowork and
cloud sessions load extensions differently; check those surfaces separately.

## Update an existing crew

If you installed an earlier version, you do not need to reinstall your team or lose its
customisation:

```text
/plugin marketplace update skyremote
/plugin update chief-of-staff-kit@skyremote
/reload-plugins
/chief-of-staff-kit:update-crew
```

In the desktop app, update the plugin in **Customize → Plugins**, start a new
local Code session, then run `update-crew` there. Updating the plugin does not
rewrite an existing crew: the updater previews changes, backs up touched files
and preserves your divisions and workspace rules.

See `CHANGELOG.md` for what each version changed — the operating doctrine your crew runs on
moves between releases, so an old render can be enforcing rules that are no longer true.

**Hand-copied crew (no plugin installed)?** If you copied the templates into
`~/.claude/agents/` by hand and personalised them, the marketplace commands above don't
apply to you — but the updater still does. Clone or pull this repo, make the
`update-crew` skill available (or just point Claude at `skills/update-crew/SKILL.md` in
your clone), and run it: it updates the agents you actually have, wherever they came
from, and preserves your customisation the same way.

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

Clone this repository, open your target workspace in Codex, and ask Codex to read
`skills/install-crew/SKILL.md` from the clone and install the crew for Codex.
The same personas render as native custom-agent TOML files under
`.codex/agents/` or `~/.codex/agents/`, plus a chief-of-staff section in the
root `AGENTS.md`. The root session uses that section to coordinate the crew;
ask it for a named agent when you want a hand-off. Current Codex releases can
spawn these agents in the desktop app, CLI and IDE. The installer uses legacy
prompt files only when an older Codex release lacks custom agents.

## How it works

1. **Reads before it asks** — if you have a `CLAUDE.md` / `AGENTS.md`, the installer
   proposes a draft org from it rather than interrogating you cold.
2. **Interviews** — confirms your divisions, which specialists to include, any
   integration agents to opt into, your house style, and where to install.
3. **Renders** — fills the templates, injects your house style into every agent,
   regenerates the orchestrator's roster, and writes a team `README`.
4. **Updates safely** — on later runs, inventories the installed roster and preserves
   customised facts while bringing the operating doctrine and available roles forward.

The source templates and skills are Markdown. Codex custom agents are generated
as TOML. There is no build step — the installer follows
[`skills/install-crew/SKILL.md`](skills/install-crew/SKILL.md).

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
