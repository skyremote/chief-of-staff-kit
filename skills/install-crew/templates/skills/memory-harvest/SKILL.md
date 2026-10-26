---
name: memory-harvest
description: >-
  Pull context out of memory-bearing tools (meeting-notes apps, notebooks, memory servers): what was said in a meeting, prior context on a person or topic. Read-only.
---

# Memory harvest

## Integration
{{INTEGRATION_SETUP}}

Check which sources are actually connected before assuming one exists. If a
source is missing, say so; never invent a meeting, note or quote.

- Pull only what the question needs; the value is the distillation.
- Prefer the real transcript or record over a second-hand summary when accuracy
  matters.
- One block per source: **source and date → key points → decisions → actions**,
  each with a pointer back to the original.

If the harvest would read far more than the answer needs (months of transcripts,
a large archive), call the `researcher` helper with the question instead, so the
raw material stays out of the main context. Anything worth keeping goes to `notes`.
