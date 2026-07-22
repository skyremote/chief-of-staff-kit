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
4. Regenerate the orchestrator roster from the files that will actually be installed.
5. For current Codex, render native custom-agent TOML files according to
   `install-crew/references/rendering-codex.md`.
6. Grep generated output for unresolved `{{...}}` tokens and malformed YAML/TOML.

Do not silently replace a native Codex roster with legacy prompt files.

## 5. Verify and report

- Parse every generated TOML/JSON file.
- Confirm every orchestrator roster entry has a corresponding agent file.
- Confirm no secrets, personal tokens or unrelated files entered the backup or diff.
- Show a concise before/after roster and the backup path.
- Tell the user to run `/reload-plugins` or start a new session if the active client has not
  picked up agent changes.

Never delete the backup automatically.
