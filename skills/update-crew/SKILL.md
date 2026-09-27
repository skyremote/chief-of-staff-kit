---
name: update-crew
description: Safely update an existing chief-of-staff crew after the plugin is refreshed. Inventories Claude Code and Codex agents, preserves customised divisions and workspace rules, previews the change set, backs up touched files and applies the current templates only after approval.
disable-model-invocation: true
---

# Update an existing crew

Use this workflow after the user refreshes the marketplace/plugin. The goal is to bring
the crew's **operating doctrine and available roles** forward without erasing the user's
business facts, house style, tool wiring or local customisations.

## 1. Discover the installed targets

Inspect, without writing:

- project Claude agents: `.claude/agents/*.md`
- global Claude agents: `~/.claude/agents/*.md`
- project Codex agents: `.codex/agents/*.toml`
- global Codex agents: `~/.codex/agents/*.toml`
- legacy Codex prompts: `.codex/prompts/*.md` and `~/.codex/prompts/*.md`
- the closest `CLAUDE.md` and `AGENTS.md`

Determine which copy is canonical. Do not create a second parallel roster when one already
exists. If both project and global teams exist, report both and ask which scope to update.

### Hand-copied installs (no kit behind the crew)

A crew can exist with NO plugin or marketplace install behind it — the user copied the
templates into `~/.claude/agents/` (or a project) by hand and personalised them. This is a
real install mode, not an error. The discovery above still finds the agent files; what's
missing is a local copy of the kit to update FROM. In that case:

1. Tell the user plainly: there is no installed kit, so "refresh the plugin" doesn't apply
   to them.
2. Offer the two routes: install the plugin/marketplace properly (recommended — they get
   update detection from now on), or fetch the templates directly
   (`git clone https://github.com/skyremote/chief-of-staff-kit` to a temp dir, or
   `git pull` an existing clone).
3. Then run the rest of this workflow unchanged against those current templates. Their
   customisations are preserved exactly as for a plugin install — the semantic inventory
   in step 2 does not care how the files got there.

## 2. Build a semantic inventory

For every installed persona, capture:

- name and role type: orchestrator, division lead, specialist or comms;
- custom division facts, boundaries and hand-offs;
- workspace/house-style block;
- integration/tool wiring;
- user-authored sections not present in the stock template;
- installed format and target path.

Compare against the current templates under the sibling `install-crew/` skill. The new
optional specialist catalogue includes `content-engine`, `web-builder`, `video-editor`
and `skool-writer-and-publish`.
Never assume the user wants all new roles; recommend the ones that fit their existing team.

## 3. Show the update plan and wait

Before writing, show:

- exact files that will be updated;
- exact new files proposed;
- custom content that will be preserved;
- any obsolete file proposed for retirement (do not delete automatically);
- target backup directory.

Wait for an explicit yes. This is the write gate.

## 4. Back up and update

Create a timestamped sibling backup directory such as
`.claude/agents-backup-YYYYMMDD-HHMMSS/` or `.codex/agents-backup-.../` and copy only the
files that will be touched. Then:

1. Merge the current role doctrine into each matching persona.
2. Preserve the installed division facts and `WORKSPACE_CONTEXT` verbatim unless the user
   asked to change them.
3. Preserve integration instructions and any clearly user-authored section.
4. Bring Claude Code frontmatter forward (v0.5.0):
   - Remove the `tools:` line: an allowlist hides every MCP connector and every newer
     built-in tool from that agent. If the list names anything beyond the kit's stock
     set (Read, Grep, Glob, Bash, Edit, Write, WebSearch, WebFetch, Skill, Agent,
     TodoWrite), such as MCP tools the user added, show it in the plan and ask first.
   - Give read-only roles (`code-auditor`, `memory-harvester`, and any custom agent whose
     persona says it never modifies files) `disallowedTools: Edit, Write, NotebookEdit`
     in its place.
   - Remove stock model pins so Claude Code honours a per-invocation choice,
     `CLAUDE_CODE_SUBAGENT_MODEL`, or the main session's model in that order.
     The v0.4.2 stock used `opus` for the orchestrator, architect, auditor and
     problem-solver, and `sonnet` for everything else. A pin that differs from
     its role's stock value may be intentional: keep it and mention it in the
     plan. If intent is unclear, show the exact file before changing it.
5. Replace the orchestrator's v0.4.x doctrine rather than merging it (v0.5.0). The
   sections "How you delegate", "Alone vs council", "Delegation depth", "Cross-agent
   visibility", "The delivery contract" and "Working style", and the model-tier and
   inline-first paragraphs, are superseded by the template's "When to delegate" and
   "How you answer"; merging old and new leaves the orchestrator with contradictory
   instructions. Carry any user-authored lines from those sections across and list
   them in the plan. If the settings `agent` key makes the orchestrator the front
   door, leave it in place and tell the user it is now optional (remove the key to
   turn it off).
6. Regenerate the orchestrator roster from the files that will actually be installed.
7. For current Codex, render native custom-agent TOML files according to
   `install-crew/references/rendering-codex.md`.
8. Grep generated output for unresolved `{{...}}` tokens and malformed YAML/TOML.

Do not silently replace a native Codex roster with legacy prompt files.

## 5. Verify and report

- Parse every generated TOML/JSON file.
- Confirm every orchestrator roster entry has a corresponding agent file.
- Confirm no secrets, personal tokens or unrelated files entered the backup or diff.
- Show a concise before/after roster and the backup path.
- Tell the user to run `/reload-plugins` or start a new session if the active client has not
  picked up agent changes.
- For each requested surface, check discovery in a new session: Claude Code
  terminal, local Claude desktop Code tab, and/or Codex app, CLI and IDE.
  File presence does not prove the client loaded the role. Report any surface
  whose runtime check was blocked separately. Cowork and cloud sessions use
  account-synced extensions rather than the local agent folder.

Never delete the backup automatically.
