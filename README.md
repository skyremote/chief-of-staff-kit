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

### Manual install (no marketplace)

```bash
git clone https://github.com/skyremote/chief-of-staff-kit
cp -r chief-of-staff-kit/skills/install-crew ~/.claude/skills/
```

Then ask Claude to **install the crew**. On the manual path the installer can also
wire the kit's hooks into your `settings.json` (see [Hooks](#hooks)); Claude Code
will show a **hook-write approval prompt** when it does — approve it once
(choose `1. Yes`). That prompt is not a permissions bug: hooks run shell commands
automatically, so Claude Code always asks a human before writing hooks to
`settings.json`, even in bypass-permissions mode. It's a one-time gate per hook
change. (The marketplace install never triggers it — plugin hooks load from the
plugin itself and nothing is written to `settings.json`.)

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

## Hooks

The kit ships a small, **portable** hook config in [`hooks/`](hooks/). Portable
means it runs clean on a fresh machine, by construction:

- POSIX `sh` only — no bash-isms, no `jq`, no `node`, no `python`.
- No machine-specific paths — hooks are addressed via `${CLAUDE_PLUGIN_ROOT}`
  (plugin install) or `~/.claude/hooks/chief-of-staff/` (manual install); the
  scripts themselves only ever reference `$CLAUDE_PROJECT_DIR` and `$HOME`.
- Fail open — if the crew isn't installed yet, or anything looks unexpected,
  every hook exits `0` silently. A hook must never break a session on a machine
  it wasn't written on.

What they do:

| Hook | Event | Behaviour |
|---|---|---|
| `crew-context.sh` | `SessionStart` | If a crew is installed, injects the roster and the routing doctrine into the session. Silent when no crew exists. |
| `agent-lint.sh` | `PostToolUse` (Write/Edit) | When an agent file under `.claude/agents/` is written, checks for leftover `{{TOKENS}}` and missing `name:`/`description:` frontmatter, and feeds failures back to the model to fix. Silent for every other file. |

With the **marketplace install** the hooks load automatically with the plugin —
no `settings.json` write, no approval prompt. With the **manual install** the
installer offers to copy the scripts to `~/.claude/hooks/chief-of-staff/` and add
them to your `settings.json`; that write triggers Claude Code's one-time
hook-write approval (by design — see the manual-install note above).

## Handing this to a friend

The three things that trip people up, in order:

1. **Agents must live in `~/.claude/agents/` (or project `.claude/agents/`)** —
   Claude Code only discovers agents there.
2. **Run the orchestrator as the main session**: `claude --agent chief-of-staff`.
   A subagent can't spawn subagents, so if chief-of-staff runs *as* a subagent it
   can't route to the rest of the crew.
3. **If you use bypass-permissions mode, keep it on and approve the hook prompt
   once** (manual install only — the marketplace path never shows it). The
   hook-write gate sits above bypass mode on purpose; `disableAllHooks` is the
   only thing that silences it, at the cost of turning hooks off entirely.

## What's in here

```
.claude-plugin/        plugin + marketplace manifests
hooks/
  hooks.json           portable hook config (loaded with the plugin)
  scripts/             the hook scripts (POSIX sh, dependency-free, fail-open)
skills/install-crew/
  SKILL.md             the installer (interview → render → write)
  templates/           the canonical agent personas (generic, placeholder-driven)
  references/          how to render for Claude Code and Codex
assets/                README art
```

## License

[MIT](LICENSE). Use it, fork it, make it yours.
