---
name: update-crew
description: Safely update an existing chief-of-staff crew after the plugin is refreshed, including the migration from orchestrator, division leads and specialist agents to one main loop with skills. Use when the user asks to update, migrate or refresh their crew, or when the session-start notice says the crew is older than the kit. Shows one plan and asks once; then it backs up the crew, measures a golden-task baseline in test mode, folds one role at a time, keeps each change only if the golden tasks hold, restores any that do not, and reports at the end.
---

# Update an existing crew

Use this after the user refreshes the plugin, or when they ask the chief of
staff to update the crew. It brings the crew's shape and doctrine forward
without erasing the user's business facts, house style, tool wiring or
customisations. From v0.6.0 the kit's default is **one loop**: the chief of
staff plans and does the work, divisions and most specialists are skills, and
only roles whose context must differ stay agents (see the kit README for why).
Migration is measured and reversible; nothing is folded on faith.

**One yes, then it runs by itself.** Everything before the plan only reads. The
user approves one plan (§4): the role verdicts, the golden tasks and the backup.
After that yes, do not stop to ask again. Back up, measure, change one role,
check, keep or restore it on the golden-task verdict, and report at the end.
Stop early only for a blocker the plan did not cover (a missing file, a failed
backup, a runner that cannot start), and say exactly what it is.

## 1. Discover, without writing

- Claude agents: `.claude/agents/*.md`, `~/.claude/agents/*.md`
- Claude skills: `.claude/skills/*/SKILL.md`, `~/.claude/skills/*/SKILL.md`
- Codex: `.codex/agents/*.toml`, `~/.codex/agents/*.toml`, `.agents/skills/`,
  `~/.agents/skills/`, legacy `.codex/prompts/*.md`
- The `hooks` and `agent` keys in the matching settings files (read only those
  keys; never print the rest), and any `hooks.json` for Codex
- The closest `CLAUDE.md` / `AGENTS.md`, the user's own rule or preference
  files, and any `golden-tasks.md` (in `<scope>/evals/` from v0.7.0; older
  installs kept it beside the agents)
- The version marker `crew-kit-version` beside the crew. A crew without one was
  installed before v0.7.0.
- **An unfinished update:** a `crew-backup-*/PROGRESS.md` that does not say
  "Finished". If one exists, read it and continue from its next unticked step.
  Never start a second migration over the first.

If both a project and a global crew exist, the plan names both and proposes the
one in use. Identify the installed shape: **v0.5 or older** (an orchestrator
plus `lead-*` / division-lead agents and specialist agents), **v0.6 or later**
(a `chief-of-staff` main loop plus skills), or a mix.

### Hand-copied installs

A crew copied by hand from the templates, with no plugin behind it, is a real
install mode. Say in the plan that refreshing the plugin does not apply to
them, and recommend installing the plugin for update detection. Fetch the
templates (`git clone https://github.com/skyremote/chief-of-staff-kit` to a temp
directory, or `git pull` an existing clone) and continue unchanged.

## 2. Choose the path

- **v0.6 or later** → refresh: merge current template doctrine into each skill,
  agent and the main loop, preserving facts and user-authored lines, and install
  the eval kit (§5) if it is missing. The refresh is one measured change.
- **v0.5 or older** → recommend one loop (§3 to §7), done one role at a time. A
  crew with some roles folded and some still agents is a valid state. If the
  user answers the plan with "stay on agents", apply §8, install the eval kit,
  offer hook gates in the same plan, write the marker and stop.

## 3. Audit every role

For each installed agent, give one verdict and a one-line reason. Use the
user's evidence where they offer it: which agents they actually call. A role
nobody calls is a fold candidate on that evidence alone.

| Verdict | Means | Default for |
|---|---|---|
| **Fold** | Becomes a skill the main loop loads: its procedure moves into `SKILL.md` and its facts into referenced files | every division lead → division skill; architect, program manager, problem solver, deck writer, voice scriptwriter, growth marketer, product designer, ops steward, email writer, inbox reader, notes archivist, memory harvester → craft skills |
| **Merge** | Two roles that always run together, chain on each other's output or touch the same data become one skill | pairs the user always calls back to back (for example inbox reader and email writer, if every triage ends in replies) |
| **Call as a tool** | Keeps its own context, but the main loop calls it with a brief and gets a compact result back; it never takes over the conversation | tool-heavy jobs: web builder, video editor, course publisher, content engine → own-context skills (`context: fork`) in Claude Code, custom agents in Codex |
| **Keep** | Stays an agent because its context must differ from the main loop's | code auditor → `code-reviewer`; plus new `verifier` and `researcher` if the user wants them |

The orchestrator is not audited: it becomes the main loop.

## 4. One plan, one yes

Show all of this in one message:

1. **The audit table**, in the order the changes will run: the main loop first,
   then each division, then the specialists.
2. **The golden tasks.** If there is no `golden-tasks.md`, draft one from
   `install-crew/templates/evals/golden-tasks.md` using the crew files and the
   user's `CLAUDE.md`: ten everyday tasks covering every division and every
   role used weekly, one task per chain (for example lead, then deck writer,
   then reviewer), **one task per hard rule** (every "never do X" line in the
   old agent files and every gated action) and **one failure task** (something
   missing, where the right answer stops after two tries and asks). Write every
   "done" line for test mode: sends, pushes and writes are blocked, so "done"
   describes the answer and the attempt, never a real effect. If the file
   exists, keep its tasks and add only the missing kinds.
3. **Hook gates**, proposed for any irreversible action the old crew mentions
   (sending, publishing, pushing, paying, deploying) that no hook covers yet,
   with the exact hooks block (`install-crew/references/rendering-claude-code.md` §6).
4. **Anything §8 would otherwise ask about:** non-stock `tools:` entries and
   non-stock model pins, with what you propose for each.
5. **The backup path**, and the size of the run: (changes + 1 for the baseline)
   x tasks x 2 test sessions, each followed by a grading session, plus up to 8
   more for any task that fails once. Give a rough time; the runs happen in the
   background.
6. One question: **"Reply yes to run all of it, or change anything first."**

This is the only stop. Wait for the yes, then do not ask again until the report.

## 5. Back up, install the eval kit, set the baseline

1. **Back up the whole crew before the first change.** Create
   `.claude/crew-backup-YYYYMMDD-HHMMSS/` (or the `~/.claude/` or `.codex/`
   equivalent) and copy into it every agent file, every crew skill folder,
   the team README, any existing `golden-tasks.md` and a copy of the settings
   file. Write a `RESTORE.md` there with the exact copy commands that put the
   old crew back, and a `PROGRESS.md` with the approved plan as a checklist.
   Tick each step as it finishes. Never delete a backup automatically.
2. **Install the eval kit** into `<scope>/evals/` (`.claude/evals/` or
   `~/.claude/evals/`): copy `install-crew/templates/evals/golden.py` and
   `test-mode.py`, and write the approved `golden-tasks.md`. An older
   `golden-tasks.md` beside the agents moves into the backup's `retired/`
   folder, so only one live copy remains.
3. **Baseline.** Run, in the background, from the workspace the crew serves:
   `python3 <scope>/evals/golden.py run baseline --cwd <workspace>` (add
   `--agent <name>` if the main loop is not called `chief-of-staff`, and use the
   same flags for every later run). Wait for it to finish; do not poll. The
   runner first proves test mode is active with a canary, then runs every task
   twice, each in a fresh session, and grades each run against its done line.
   - Exit 0: read every failing task once. If the task or its done line is wrong,
     not the crew, fix it now and run the same baseline command again: it reruns
     only the tasks you changed. Changing a task later makes the earlier numbers
     useless. Note any fix for the report.
   - Exit 75 (usage limit, Claude unavailable, or interrupted): note it in
     `PROGRESS.md`, tell the user in one line that it continues later, then run
     the same command again; it continues from its last result. Adding
     `--wait-on-limit` makes it wait out a usage limit by itself.
   - Exit 3: report the reason it prints and stop. It never runs a task when
     test mode cannot be proved safe, and it never counts a run it could not
     finish or grade.

## 6. Change one role at a time

For each role, in the plan's order:

1. **Write it.** Retire the old agent file into the backup's `retired/` folder;
   never delete it.
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
   - *Merge → one skill:* read both old files side by side. Take the **union**
     of their rules, never a summary: every rule, check and escalation line
     from either file goes into the merged skill. Where two lines say the same
     thing, keep the stricter wording once. Where they contradict, keep the
     stricter rule and list the conflict for the report. Delete only the lines
     about calling each other, since one skill now does both jobs.
   - *Call as a tool:* the matching own-context skill (Claude Code) or custom
     agent (Codex), with the user's customisations.
   - *Keep:* bring frontmatter forward (§8) and, for the auditor, rename to
     `code-reviewer` with `effort: high` if the plan said so.
2. **Rule map.** Write `rule-map-<role>.md` in the backup folder. List every
   line of the old file (both files for a merge) that carries a rule, a check,
   a fact or a step, and where it now lives (file and section) or why it went.
   Only three reasons count: the main loop now owns it (persona, voice,
   routing, delegation), it was written for an older model, or it duplicates a
   named line. An old "stop after two failed attempts and return a STUCK
   report" line maps to the main loop's rule on stopping after two failed
   tries: inline, the main loop is the one that stops and asks the user.
3. **Independent review.** Give the old file(s), the new files, the rule map and
   the user's own rule files to `code-reviewer` (or, if it is not installed, a
   fresh `claude -p` session that may only read). Brief it to check that every
   old rule arrived or has a valid reason, that no new line contradicts
   another, that no house-style rule breaks itself (a rule that bans a
   character must not use it), and to flag any line with no source rather than
   call it invented: it may come from a file the reviewer cannot see. Fix every
   confirmed finding before you measure.
4. **Measure.** In the background: `python3 <scope>/evals/golden.py run
   <change-label> --cwd <workspace>`, then `python3 <scope>/evals/golden.py check
   <change-label> --cwd <workspace>`. Use a new short label per change, such
   as `main-loop` or `fold-decks`, never one already used. The check compares task by task with the last
   kept run (the baseline for the first change), reruns any task that failed in
   only one run four more times, and prints HOLDS or WORSE. Exits 75 and 3 mean
   what they meant at the baseline.
5. **Decide by the verdict, without asking.**
   - **HOLDS:** keep the change. The runner records it as the last kept run.
   - **WORSE:** restore this role from the backup, move the skill you created
     into the backup's `rejected/` folder, and record the role as **keep** with
     the tasks that failed.

   Tick the step in `PROGRESS.md`, update the main loop's `{{DIVISION_SKILLS}}`
   line and the team README after each kept change, and go to the next role.

For larger or production agent systems, point the user to Anthropic's
[single-agent-loop-kit](https://github.com/anthropics/single-agent-loop-kit),
which runs the same audit, baseline, merge, fold and call-as-tool steps with
scripts for coupling maps and eval comparison.

## 7. Verify and report

- Parse every frontmatter block, TOML and JSON file you wrote.
- Grep generated output for unresolved `{{` tokens.
- Confirm every skill named in the main loop exists, every retired agent is in
  the backup, and every rule map accounts for every old line.
- Test each gate script with a matching and a non-matching input. That direct
  test is what proves a gate: in golden-task runs test mode blocks first, so a
  gate task proves only that the session stops and does not try another route.
- Write the kit version (`version` in the plugin's `.claude-plugin/plugin.json`)
  into `<scope>/crew-kit-version`: the bare version, such as `0.7.0`, on one
  line. That silences the session-start notice.
- Mark `PROGRESS.md` "Finished".
- Report in one message: the roster before and after, each change with its
  verdict and the tasks that decided it, any merge conflicts, any golden task
  you fixed, the backup path and the restore command.
- Tell the user to start a new session (or `/reload-skills` and
  `/reload-plugins`) and check discovery on each surface they use. File
  presence does not prove the client loaded it.

## 8. Agents that stay agents (v0.5.0 rules, still current)

- Remove stock `tools:` allowlists; they hide connected and newer built-in tools.
  A list that names anything beyond the kit's old stock set (Read, Grep, Glob,
  Bash, Edit, Write, WebSearch, WebFetch, Skill, Agent, TodoWrite) goes in the
  plan rather than being edited silently. Newer built-ins such as `ToolSearch`
  are current, not stale: keep them.
- Read-only roles get `disallowedTools: Edit, Write, NotebookEdit`.
- Remove stock model pins (v0.4.2 used `opus` for the orchestrator, architect,
  auditor and problem solver, `sonnet` for the rest). Keep a pin that differs
  from its role's stock value and mention it in the plan.
- Replace v0.4.x orchestrator doctrine rather than merging it: old sections
  such as "How you delegate", "Alone vs council", "Delegation depth" and "The
  delivery contract" contradict the current template.
- For Codex, render native custom-agent TOML per
  `install-crew/references/rendering-codex.md`; never silently replace a native
  roster with legacy prompt files. The golden-task runner drives Claude Code
  only: on Codex, run the golden tasks by hand, twice before and twice after
  each change, in fresh sessions.
