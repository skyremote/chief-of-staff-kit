# Changelog

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
