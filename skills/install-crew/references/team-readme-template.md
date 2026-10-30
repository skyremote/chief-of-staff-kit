# The crew: how it works

Your chief of staff is **one main loop**. It plans the work, does the work and
keeps the context. Your divisions and crafts are **skills** it loads when a task
needs them. Three **helpers** run in their own window when a separate context
changes the result. **Hooks** hold the actions you never want taken without a
yes. **Golden tasks** tell you whether a change to any of this helped.

## Where these live

Agents, skills, hook scripts and settings load at session start: edits take
effect in the **next** session, or after `/reload-skills`. Keep new files in the
same directories so they are found.

## The shape

```
                          YOU
                           │
                     chief-of-staff                 ← talk to this; it does the work
                           │
     ┌─────────────────────┼──────────────────────────┐
  division skills      craft skills              helpers (own window)
  (load on demand)     (load on demand;          code-reviewer · verifier · researcher
                        heavy ones run in
                        their own context)
                           │
                  hooks gate the irreversible actions
```

## The roster

{{ROSTER_TABLE}}

Some skills depend on an integration (email, notes, meeting transcripts, memory
stores). When it is not connected they say so plainly rather than inventing a
result.

## The one question before any helper

Does what the main loop already knows **help, hurt, or not matter**?

- **Helps** → the main loop does it inline. This is the usual answer.
- **Hurts** → a fresh reviewer: `code-reviewer` sees only the spec and the diff;
  `verifier` knows only the user flow.
- **Does not matter** → a clean-window helper such as `researcher`.
- **Several truly independent heavy jobs** → forks in parallel. Five or more
  belongs in a workflow.

## Gates

The actions listed in your settings under `hooks` are gated. A gate either asks
you to confirm or blocks and tells the chief of staff to ask you. To change a
gate, edit the hooks block in settings (a backup was taken at install) or the
script in the hooks directory, then start a new session.

## Changing the crew

Change one thing at a time and measure it with the golden tasks. From the
workspace, run `python3 <evals>/golden.py run baseline` once. After each change,
run `python3 <evals>/golden.py run <new-label>`, then `python3
<evals>/golden.py check <new-label>`. Each task runs twice in a fresh session in
test mode, where every send, push and live write is blocked. Keep a change only
if the check says it holds. To bring the whole crew up to a new kit version, ask
the chief of staff to update the crew. To add a division,
copy an existing division skill folder and fill it in; to add a craft, add a
skill. Add a helper agent only when the main loop's context would hurt the
result, and the golden tasks show the helper does better.

## How to run it

- **Claude Code CLI:** `claude --agent chief-of-staff`. An optional `agent`
  setting makes that the default for bare `claude`. Pin unattended `claude -p`
  jobs to the agent they need.
- **Claude desktop Code tab:** start a new local session in the workspace where
  the crew was installed; it reads the same local files. Chat, Cowork and cloud
  sessions load extensions separately and need their own check.
- **Codex app, CLI or IDE:** the root session reads the team section of
  `AGENTS.md`, skills load from `.agents/skills/`, helpers are custom agents in
  `.codex/agents/`. Review the hooks once with `/hooks`.
