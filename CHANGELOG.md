# Changelog

## v0.5.0 — 2026-09-27

This release updates the crew for current Claude Code and Codex clients. It
combines the staged mechanism and persona changes into one member update.

- **Connected tools stay available.** Removed stock `tools:` allowlists from all
  Claude agent templates. In the test workspace the v0.4.2 chief of staff saw
  8 tools against 25 in a plain session; an allowlist hid connected and newer
  built-in tools. Subagents still receive only the tools their runtime permits.
- **Model choice follows the session.** Removed stock `model:` pins. Claude Code
  now resolves a per-invocation choice, `CLAUDE_CODE_SUBAGENT_MODEL`, then the
  main session's model. Across four delegated tasks, the old Sonnet-pinned lead
  averaged 97 seconds against 55 seconds without the pin, saving $0.09 in
  total (8%) while pinned. Both arms passed the same 5/5 hidden tests. Members
  can still deliberately pin a model; the updater preserves custom pins.
- **The chief of staff works directly on short requests.** It delegates when a
  named role is requested, independent streams justify parallel work, the task
  would consume too much context, or another agent holds relevant access. It
  briefs once, gives each agent clear ownership, and synthesises their results.
  Division leads also work directly when their domain does not need a specialist.
  A lead may use a specialist for a distinct part of its brief where the client
  supports nested agents; otherwise the root coordinates that hand-off.
- **Less process talk.** Removed the routing line in every reply, the old
  delegation ceremony, cache and cold-start arguments, and stale nesting and
  delivery rules. In the sampled everyday tasks, v0.4.2 narrated its routing
  in 5 of 9 answers; the new version did so in 0 of 27. Everyday requests
  averaged 26 seconds with the new chief of staff and 26 seconds in a plain
  session. Deterministic and hidden checks were level; these tests do not
  establish a quality gain over a plain session. Explicitly requested
  delegation worked in 6 of 6 runs.
- **The front door is a choice at installation.** A new install asks whether
  the chief of staff should be the default local Claude Code session, with no
  as the initial selection. The updater leaves an existing `agent` setting
  untouched. Scheduled `claude -p` jobs still need their own agent choice when
  the default is enabled.
- **Read-only claims are precise.** Claude's auditor and memory harvester block
  `Edit`, `Write` and `NotebookEdit`; Bash and connected tools may still write,
  so this is a behavioural boundary. Codex read-only reviewers use its native
  read-only sandbox.
- **Native client guidance.** The installer and team README now cover Claude's
  local desktop Code tab, as well as the terminal. Codex uses custom-agent TOML
  in the app, CLI and IDE with the chief-of-staff doctrine in root `AGENTS.md`;
  it does not depend on a `codex --agent` CLI flag. Chat, Cowork and cloud
  sessions have separate extension loading and need their own checks.
- **Existing crews need the updater.** Refreshing the plugin alone does not
  rewrite copied agent files. `update-crew` previews changes, backs up files,
  preserves business facts and user-authored instructions, removes stock
  allowlists and model pins, and replaces contradictory v0.4.x doctrine.

The Jev preference and averaged-score numbers from the staging notes were
excluded: their questions did not pass the method check. The release evidence
above rests on timings, tool counts, deterministic tests and answer text.

## v0.4.2 — 2026-08-24

Distribution-fix release, prompted by a field report from an early adopter who
diffed a long-stale install against main. The content of v0.3.0–v0.4.1 had
shipped to main, but the plugin and marketplace manifests were never bumped past
0.2.2 and no tags or GitHub releases were cut — so marketplace update detection
told existing installs there was nothing new, and people quietly ran old
orchestrators believing they were current. This release fixes the pipe and the
report's other findings:

- **Manifests bumped**: `plugin.json` and `marketplace.json` now carry the real
  version, so marketplace installs are finally told to update. Retro-tags and
  GitHub releases added for v0.2.1 through v0.4.1.
- **Release checklist** added (`RELEASING.md`) so a content release can never
  again ship without the manifest bump, tag and release — the root cause here.
- **Front-door scheduled-run scan**: before offering the front door, the
  installer now actively scans for scheduled `claude -p` invocations (crontab,
  launchd plists, workspace scripts) and shows what it finds — turning the
  documented headless caveat into a check that catches the cron you forgot
  you had.
- **Hand-copied installs** are now a recognised install mode: `update-crew`
  documents the update path for crews copied from the templates by hand, with
  no plugin installed behind them.
- **"60% more expensive" clarified to "per run"** in the v0.4.0 haiku numbers —
  it always meant total run cost from the extra turns, not per-token rate.
- **Stale haiku guidance fixed** in the Claude Code rendering reference, which
  still recommended haiku for mechanical scouts in contradiction of the v0.4.0
  benchmark rejection.

## v0.4.1 — 2026-08-18

Front-door release. The installer now offers to make the orchestrator the
DEFAULT session: a new interview question plus Step 4.5 set the `agent` key in
settings so a bare `claude` (and the desktop app) boots straight into the
chief of staff — no flags, no remembering. Includes the VS Code integrated-
terminal shell function (the extension has no agent setting of its own) and
the headless caveat (`claude -p` scripts should pass `--agent` explicitly).
First-drive check updated: with the front door enabled, a bare `claude` must
pass the identity check.

## v0.4.0 — 2026-08-18

Model-tier release, benchmarked like v0.3.0. Division leads drop from opus to
sonnet — routing and synthesis work sonnet handles cleanly at a fraction of the
cost — while the orchestrator and the judgement agents (architect, code-auditor,
problem-solver) keep the strong model. Haiku was tested for mechanical
specialists and REJECTED on data: under identical conditions haiku workers ran
~2.7x slower than sonnet (mean 139s vs 52s), 60% more expensive per run (total
run cost from the extra turns — haiku's per-token rate is still cheaper), and
wildly inconsistent (87-216s) — a cheaper per-token model is not a cheaper run. Sonnet
workers under the v0.3.0 orchestrator benchmarked at a flat 52s per delegated
task (vs 122s on v0.2.x, 96s pre-v0.2), with blind-read production-grade output
quality on client-comms and incident-diagnosis tasks.

- **Leads: opus → sonnet** in the division-lead template.
- **Tier doctrine** in the orchestrator: strong plans, cheap executes, strong
  audits; never override a worker's pinned model upward for ordinary work;
  never change a model mid-session (cache cold-start).
- **Advisor gating** in worker briefs: consult the advisor only after two
  failed attempts, never on routine work.

## v0.3.0 — 2026-08-18

Speed release. Community reports that the crew "felt slower" since v0.2.x were
benchmarked and confirmed: the mandatory delivery ceremony put a ~2-minute latency
floor under every delegation (old fast path ~50s; v0.2.x never under ~105s on the
same task, at equal cost), and depth-first delegation stacks cold starts and
short-lived caches.

- **Inline-first gate**: the orchestrator now does work itself unless the task
  genuinely needs parallel streams, context isolation, or tool isolation.
- **Flat by default**: delegation is one level deep; depth-3 nesting becomes a
  deliberate escape hatch with an explicit "one brief, one lead, one report"
  pattern for when it IS warranted; fan-outs beyond ~5 agents route to workflows.
- **Delivery contract scoped**: full report/progress/SendMessage ceremony applies
  to background and long runs only; short foreground spawns deliver by their
  returned message.
- **Install first-drive**: install-crew now ends with a guided first session
  (identity check, inline answer, first delegation) and writes a QUICKSTART.md.

## 0.2.2 — 10 August 2026

- Added the delivery contract to the orchestrator template, learned from a live miss:
  idle is a finished agent's normal parked state, but delivery is never automatic —
  every brief must end with an explicit deliver-before-you-stop step (message the
  spawner AND write to disk), and the orchestrator chases idle agents that haven't
  delivered (disk, then message, then collect; resume by name, don't respawn).

## 0.2.1 — 9 August 2026

- Updated orchestration doctrine for Claude Code v2.1.219+: subagents can now spawn
  nested subagents to depth 3 by default, so a spawned lead can run its own sub-team
  under one brief. The old "only the main session can delegate" hard limit is kept as
  a documented fallback for older runtimes and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`.
- Documented cross-agent visibility (v2.1.224+): `ListAgents` discovery and
  cross-session/cross-machine `SendMessage`, with report-to-disk retained as the
  delivery fallback for background agents.

## 0.2.0 — 22 July 2026

- Added a safe `update-crew` workflow for existing installations, with inventory,
  preview, scoped backups and preservation of user customisation.
- Added the namespaced `/chief-of-staff-kit:advisor` adoption and verification runbook.
- Added generic content-engine, web-builder, video-editor and skool-writer-and-publish
  specialist templates.
- Replaced the obsolete manual-only Codex path with native `.codex/agents/*.toml`
  rendering and current one-level subagent orchestration guidance.
- Documented the exact marketplace/plugin update path for existing users.

## 0.1.0

- Initial public release of the customisable chief-of-staff crew.
