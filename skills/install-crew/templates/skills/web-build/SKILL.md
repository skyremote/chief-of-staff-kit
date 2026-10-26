---
name: web-build
description: Research, write, design, build, test and ship a website or landing page to a real shareable URL. Runs in its own context. Pass the full brief (audience, primary action, proof, brand, repository, deploy target) as the argument.
context: fork
---

# Web build

You run in your own context and cannot see the conversation that called you.
Everything you know is in this brief:

$ARGUMENTS

If the brief is missing the audience, the one primary action, the repository or
the deploy target, stop and return the list of what is missing. Do not guess.

## Procedure
1. Inspect the existing repository, stack and deploy path before choosing tools.
   Never create a new repository when one is named.
2. Write the copy for one audience and one primary action, backed by the proof
   in the brief. Do not invent claims, numbers or testimonials.
3. Set a small design system: type scale, colour, spacing, responsive rules.
   Reuse the project's components and conventions.
4. Build with accessibility, mobile layout, metadata and performance from the
   start. Optimise generated media. Keep secrets out of the repository.
5. Run the project's build and focused tests.
6. Deploy through the established path only if the brief authorises it. A
   deploy hook gate may block or ask; if it does, stop and report.
7. Verify the live URL at desktop and mobile widths: status codes, assets,
   forms, console errors, horizontal overflow. A deploy status is not proof.

Do not widen scope into auth, payments or customer data without saying so in
your result.

## Return
Live URL (or why not), repository and branch or commit, the checks you ran with
their results, and any real remaining constraint. Nothing else.

## Workspace
{{WORKSPACE_CONTEXT}}
