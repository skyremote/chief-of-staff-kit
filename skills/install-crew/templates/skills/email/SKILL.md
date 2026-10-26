---
name: email
description: Draft outbound email in the right division's voice: client replies, outreach, follow-ups, introductions. Drafts by default; sending is gated. Use for any email the user wants written.
---

# Email

Load the division skill's `voice.md` first. One email speaks for one division;
if it is unclear which, ask rather than blend.

## Draft by default
Produce **To / Subject / Body** and a one-line note on the tone you chose. Send
only when the user says "send", and restate the recipient and subject first.
Sending is an irreversible action and should be gated by a hook; if the gate
blocks or asks, wait for the user.

## Integration
{{INTEGRATION_SETUP}}

If the email integration is not wired, return the draft and say plainly that it
cannot be sent yet. Never report a send that did not happen.

## How to write
- The subject earns the open; the first line earns the second.
- One clear ask per email. Short paragraphs, no throat-clearing.
- Match the recipient's formality; mirror the thread when replying.
