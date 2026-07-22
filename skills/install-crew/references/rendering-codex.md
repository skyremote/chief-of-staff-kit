# Rendering the crew for Codex

Current Codex releases support native custom agents and one-level subagent workflows in
the desktop app, CLI and IDE. Render the crew into that mechanism. Use the legacy prompt
fallback at the end only when the installed Codex build genuinely lacks custom agents.

## What to generate

For the selected project or global scope, produce:

1. one TOML file per persona under `.codex/agents/` or `~/.codex/agents/`;
2. one `AGENTS.md` at the workspace root (or a clearly delimited team section in an
   existing file) containing the routing and delegation doctrine;
3. a team README with the installed roster and update instructions.

Do not overwrite an existing `AGENTS.md`. Merge a versioned, clearly headed section and
preserve unrelated project rules.

## Custom-agent TOML

Each agent file requires `name`, `description` and `developer_instructions`:

```toml
name = "code-auditor"
description = "Read-only code reviewer focused on correctness, security and missing tests."
developer_instructions = """
You are the code auditor...
"""
```

Use the persona's kebab-case name as the filename. Convert the Claude template as follows:

- map frontmatter `name` and `description` to TOML strings;
- place the full persona body, with resolved placeholders, in
  `developer_instructions = """..."""`;
- omit Claude-only `tools`, `color` and `model` keys unless the user explicitly wants a
  Codex model override;
- when a model override is requested, use current Codex model IDs and
  `model_reasoning_effort`; otherwise inherit the parent session;
- translate "Agent tool" or Claude-specific invocation language into "spawn/delegate to
  the named custom agent";
- keep subagents aware that they are not alone in the workspace and must not revert other
  agents' edits.

Escape any literal triple double quote before embedding the body. Parse every TOML file
after writing it.

## Root AGENTS.md doctrine

The team section must include:

- the installed roster and each role's ownership boundary;
- a direct instruction that cross-cutting work should use the chief-of-staff as the root
  agent or ask the current root to delegate;
- "one specialist by default; two or three only for genuinely independent work";
- clean delegation briefs: objective, measurable output, format, sources, ownership and
  stopping point;
- wait for delegated results and synthesise them into one recommendation;
- pair a generator with a different reviewer for consequential, hard-to-reverse work;
- explicit ownership when several agents edit code, plus a reminder not to revert others;
- the default one-level topology: root can spawn children; children do the assigned work
  and return a summary rather than recursively fanning out.

Do not promise proactive fan-out on every task. Codex follows direct user instructions and
applicable `AGENTS.md`/skill instructions; parallel agents cost more and write-heavy work
can conflict.

## Project versus global scope

- Project team: `.codex/agents/*.toml` and project `AGENTS.md`.
- Personal team: `~/.codex/agents/*.toml`; still document project-specific routing in the
  project's `AGENTS.md` rather than placing business facts in a global file.

If both scopes exist, show the target plan and ask which one is canonical before writing.

## Placeholders

Resolve the same tokens as the Claude renderer:

- `{{WORKSPACE_CONTEXT}}` in every persona;
- `{{LEADS_LIST}}` and `{{SPECIALISTS_LIST}}` in the orchestrator;
- all division-lead tokens;
- `{{DEFAULT_STACK}}`, `{{FILING_MAP}}`, `{{INTEGRATION_SETUP}}` and
  `{{ROSTER_TABLE}}` where used.

Grep every output file for `{{` after rendering; a surviving token is a bug.

## Verification

1. Confirm the Codex version and that custom agents are available.
2. Parse all TOML files.
3. Confirm every roster entry maps to a file and every file has the three required fields.
4. Start a fresh Codex session in the target workspace and ask it to list or spawn one
   installed agent. Treat config generation and live runtime discovery as separate checks.
5. Report the exact directories written and the safe update command/workflow.

## Legacy fallback

Only when the installed Codex release does not support `.codex/agents/*.toml`, render the
persona bodies as plain Markdown under `.codex/prompts/` or `~/.codex/prompts/` and state
that those roles are manually invoked. Do not select this fallback merely because prompt
files already exist; offer migration to native agents through `update-crew`.
