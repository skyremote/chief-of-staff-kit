---
name: update-crew
description: Safely update an existing chief-of-staff crew after the plugin is refreshed, including the v0.6.0 migration from orchestrator, division leads and specialist agents to one main loop with skills. Audits each role (fold, merge, call as a tool, keep), folds one role at a time against golden tasks, backs up every touched file so the old crew stays restorable, and only writes after approval.
disable-model-invocation: true
---

# Update an existing crew

Use this after the user refreshes the plugin. It brings the crew's shape and
doctrine forward without erasing the user's business facts, house style, tool
wiring or customisations. From v0.6.0 the kit's default is **one loop**: the
chief of staff plans and does the work, divisions and most specialists are
skills, and only roles whose context must differ stay agents (see the kit
README for why). Migration is measured and reversible; nothing is folded on
faith.

## 1. Discover, without writing

- Claude agents: `.claude/agents/*.md`, `~/.claude/agents/*.md`
- Claude skills: `.claude/skills/*/SKILL.md`, `~/.claude/skills/*/SKILL.md`
- Codex: `.codex/agents/*.toml`, `~/.codex/agents/*.toml`, `.agents/skills/`,
  `~/.agents/skills/`, legacy `.codex/prompts/*.md`
- The `hooks` and `agent` keys in the matching settings files (read only those
  keys; never print the rest), and any `hooks.json` for Codex
- The closest `CLAUDE.md` / `AGENTS.md`, and any `golden-tasks.md`

Decide which copy is canonical. If both project and global crews exist, report
both and ask which to update. Identify the installed shape: **v0.5 or older**
(an orchestrator plus `lead-*` / division-lead agents and specialist agents),
**v0.6** (a `chief-of-staff` main loop plus skills), or a mix.

### Hand-copied installs

A crew copied by hand from the templates, with no plugin behind it, is a real
install mode. Tell the user that refreshing the plugin does not apply to them;
offer to install the plugin (recommended, for update detection) or to fetch the
templates (`git clone https://github.com/skyremote/chief-of-staff-kit` to a temp
directory, or `git pull` an existing clone). Then continue unchanged.

## 2. Choose the path

- **Already v0.6** → refresh: merge current template doctrine into each skill,
  agent and the main loop, preserving facts and user-authored lines. Go to §6.
- **v0.5 or older, user wants to stay on agents** → apply the v0.5.0 rules in §7
  and offer hook gates and golden tasks (§5). Stop there.
- **v0.5 or older, user wants one loop** → §3 to §6. Recommend this path, and
  say it is done one role at a time and can stop at any point: a crew with some
  roles folded and some still agents is a valid state.

## 3. Audit every role

For each installed agent, give one verdict and a one-line reason. Use the
user's evidence where it exists: which agents they actually call, and, if they
agree, a count of subagent runs per agent type from recent session transcripts.
A role nobody calls is a fold candidate on that evidence alone.

| Verdict | Means | Default for |
|---|---|---|
| **Fold** | Becomes a skill the main loop loads: its procedure moves into `SKILL.md` and its facts into referenced files | every division lead → division skill; architect, program manager, problem solver, deck writer, voice scriptwriter, growth marketer, product designer, ops steward, email writer, inbox reader, notes archivist, memory harvester → craft skills |
| **Merge** | Two roles that always run together, chain on each other's output or touch the same data become one skill | pairs the user always calls back to back (for example inbox reader and email writer, if every triage ends in replies) |
| **Call as a tool** | Keeps its own context, but the main loop calls it with a brief and gets a compact result back; it never takes over the conversation | tool-heavy jobs: web builder, video editor, course publisher, content engine → own-context skills (`context: fork`) in Claude Code, custom agents in Codex |
| **Keep** | Stays an agent because its context must differ from the main loop's | code auditor → `code-reviewer`; plus new `verifier` and `researcher` if the user wants them |

The orchestrator is not audited: it becomes the main loop.

Show the audit table and wait for the user to change any verdict.

## 4. Back up, then set the baseline

1. **Back up the whole crew before the first change.** Create
   `.claude/crew-backup-YYYYMMDD-HHMMSS/` (or the `~/.claude/` or `.codex/`
   equivalent) and copy into it every agent file, every crew skill folder,
   the team README, and a copy of the settings file. Write a `RESTORE.md` there
   with the exact copy commands that put the old crew back. Never delete a
   backup automatically.
2. **Golden tasks.** If there is no `golden-tasks.md`, write one from
   `install-crew/templates/evals/golden-tasks.md` and help the user fill ten
   real tasks with "done" lines, covering every division and every role they
   use weekly. Include one task per chain they rely on (for example lead then
   deck writer then reviewer), so a dropped hand-off shows up.
3. **Baseline.** Run the ten tasks **twice** on the current crew, each in a
   fresh session, and record pass or fail and time per task.

## 5. Fold one role at a time

Start with the main loop, then one division lead, then the specialists in the
order the user prefers. For each role:

1. **Show the plan for this one role:** the new or changed files, what custom
   content moves where, and the agent file that will be retired (moved into the
   backup's `retired/` folder, not deleted). Wait for a yes.
2. **Write it.**
   - *Orchestrator → main loop:* render `install-crew/templates/main-loop.md`
     as `chief-of-staff`. Carry across the user's `WORKSPACE_CONTEXT` verbatim
     and any user-authored lines; drop the roster, routing and delegation
     sections, which the one question replaces. Leave any front-door `agent`
     key in place.
   - *Division lead → division skill:* `KEY_FACTS` and sources to `facts.md`,
     people to `people.md`, voice notes to `voice.md`, live work to
     `open-work.md`, owns / does not own and filing to `SKILL.md`. Hand-off
     lines become "load skill X" lines.
   - *Specialist → craft skill:* start from the matching template in
     `install-crew/templates/skills/`, then carry across the user's custom
     facts, stack, filing map and integration wiring.
   - *Call as a tool:* the matching own-context skill (Claude Code) or custom
     agent (Codex), with the user's customisations.
   - *Keep:* bring frontmatter forward (§7) and, for the auditor, rename to
     `code-reviewer` with `effort: high` if the user agrees.
3. **Measure.** Start a new session and run the golden tasks twice. Compare task
   by task with the baseline, not only the total: a fold can save time and still
   flip one task from pass to fail.
4. **Decide.** Keep the fold only if it scores at least as well. Otherwise
   restore that role's agent from the backup, remove the skill you just created,
   and record the role as **keep** with the reason.

Update the main loop's `{{DIVISION_SKILLS}}` line and the team README after each
kept change. Offer hook gates once, at any point: interview for irreversible
actions and write them as `install-crew/references/rendering-claude-code.md` §6
describes (preview, back up, merge, test).

For larger or production agent systems, point the user to Anthropic's
[single-agent-loop-kit](https://github.com/anthropics/single-agent-loop-kit),
which runs the same audit, baseline, merge, fold and call-as-tool steps with
scripts for coupling maps and eval comparison.

## 6. Verify and report

- Parse every frontmatter block, TOML and JSON file you wrote.
- Grep generated output for unresolved `{{` tokens.
- Confirm every skill named in the main loop exists, and every retired agent is
  in the backup.
- Test each gate with a matching and a non-matching input.
- Show the before and after roster, the golden-task results per change, the
  backup path and the restore command.
- Tell the user to start a new session (or `/reload-skills` and
  `/reload-plugins`) and check discovery on each surface they use. File
  presence does not prove the client loaded it.

## 7. Agents that stay agents (v0.5.0 rules, still current)

- Remove stock `tools:` allowlists; they hide connected and newer built-in tools.
  If a list names anything beyond the kit's old stock set (Read, Grep, Glob,
  Bash, Edit, Write, WebSearch, WebFetch, Skill, Agent, TodoWrite), show it and
  ask first.
- Read-only roles get `disallowedTools: Edit, Write, NotebookEdit`.
- Remove stock model pins (v0.4.2 used `opus` for the orchestrator, architect,
  auditor and problem solver, `sonnet` for the rest). Keep a pin that differs
  from its role's stock value and mention it.
- Replace v0.4.x orchestrator doctrine rather than merging it: old sections
  such as "How you delegate", "Alone vs council", "Delegation depth" and "The
  delivery contract" contradict the current template.
- For Codex, render native custom-agent TOML per
  `install-crew/references/rendering-codex.md`; never silently replace a native
  roster with legacy prompt files.
