---
name: architecture
description: Architecture and technical-direction decisions in the house stack. Use before a significant build, for stack choices, system design, scaling, cost and technical-risk calls.
---

# Architecture

Give **a decision**, the one-line why and the single biggest risk. Not a survey
of options. If the answer is "don't build this", say so.

## Default stack
{{DEFAULT_STACK}}

Pick boring, proven defaults. Deviate only with a reason you can state in one line.

## How to decide
- The simplest thing that scales. Ask "what breaks at 10x?" for load, cost, data
  and team.
- Cost per user and model-token economics are first-class.
- Where one deployment serves several customers, tenant isolation is a
  load-bearing requirement, not a later hardening pass.
- Reversible decisions: decide fast. One-way doors: slow down and write a short
  memo.

Application code lives in version-controlled repositories, not in the workspace
docs tree. Build there, and use a scratch directory for throwaway work.

For an independent check of the resulting code, call the `code-reviewer` helper
with the spec and the diff; do not review your own build in the same breath.
