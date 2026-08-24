# Changelog

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
