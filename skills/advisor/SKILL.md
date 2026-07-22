---
name: advisor
description: Adopt and verify Anthropic's advisor primitive for an installed crew. Checks Claude Code support, configures advisorModel without overwriting settings, adds tightly scoped escalation discipline to high-judgement agents and verifies the result.
disable-model-invocation: true
---

# Adopt the advisor for the crew

The advisor primitive lets a working Claude model consult a stronger model inside the same
session. It is not another subagent and does not change the one-level crew topology.

## Guardrails

- Inspect the installed Claude Code version and existing settings before changing anything.
- Back up `~/.claude/settings.json`; it may contain secrets and permission rules. Never
  print or commit its contents.
- Preserve every existing setting. Add or update only `advisorModel`.
- The advisor must be at least as capable as the main model. If the desired pairing is
  uncertain or unsupported, stop and explain the pairing instead of silently disabling it.
- Advisor calls consume plan/API quota. Reserve them for judgement points, repeated failure
  and final independent review; do not add advisor instructions to every low-judgement role.

## Runbook

1. Run `claude --version` and confirm that the installed release exposes `/advisor` or the
   `advisorModel` setting. If it does not, recommend updating Claude Code and stop.
2. Read the current main model without exposing other settings.
3. Ask which advisor model to use if the user has not specified one. Recommend the strongest
   model available within their quota, with the main/advisor compatibility explained.
4. Create a timestamped backup of `~/.claude/settings.json`.
5. Parse the JSON, change only `advisorModel`, and write valid formatted JSON.
6. Add a short **Reaching for the advisor** section only to installed high-judgement agents
   such as the orchestrator, architect, code auditor, problem solver and web builder. Keep
   any existing tailored version instead of duplicating it.
7. If the same crew is installed for Codex, do not add Anthropic advisor instructions to
   Codex agents; Codex uses its own reviewer/subagent mechanisms.

## Verification

- Parse the settings JSON.
- Report the advisor model value without printing unrelated settings.
- Confirm which agent files contain the escalation discipline.
- Start a fresh Claude Code session and run `/advisor` to verify the primitive is available.
  If live invocation is unavailable, distinguish a configuration success from an unverified
  runtime result.

The discipline block should say to consult the advisor only:

- before committing to a consequential approach where judgement changes the outcome;
- after the same failure repeats twice;
- before declaring high-impact work complete.

On routine or mechanical work, do not consult it.
