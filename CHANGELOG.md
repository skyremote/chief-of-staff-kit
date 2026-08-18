# Changelog

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
