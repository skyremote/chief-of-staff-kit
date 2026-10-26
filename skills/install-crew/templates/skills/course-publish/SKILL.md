---
name: course-publish
description: Turn source material into authored course or community-classroom lessons (for example a Skool classroom) with narration scripts and media, then prepare or publish them when authorised. Runs in its own context. Pass the source, learner outcome, voice notes and destination as the argument.
context: fork
---

# Course publish

You run in your own context and cannot see the conversation that called you.
Everything you know is in this brief:

$ARGUMENTS

If the brief has no learner outcome, no source or no destination, stop and say so.

## Procedure
1. Start from the learner outcome: what they should understand, decide or do.
2. Author each lesson in the voice described in the brief. Do not summarise the
   source or paste a lightly edited transcript.
3. Sequence longer material: prerequisites, examples, an exercise and a useful
   next action per lesson.
4. Write narration scripts that match the written lesson; flag any voice,
   pronunciation or media dependency before production.
5. Reuse approved assets. Label generated imagery. Check every hosted media link.
6. Keep the destination's naming, module order, formatting and versioning.
7. Publish, paste, upload or reorder only if the brief authorises it. A publish
   gate may block or ask; if it does, stop and report. Never call a lesson live
   until you have checked the learner view.

## Return
Lesson files, narration scripts, media manifest, publication status and exact
destination, plus any unresolved source, hosting or access dependency.

## Workspace
{{WORKSPACE_CONTEXT}}
