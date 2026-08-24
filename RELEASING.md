# Releasing

Every content release ships THROUGH this checklist, in order. The failure mode
this file exists to prevent is real and has happened: v0.3.0–v0.4.1 shipped to
main with the manifests still at 0.2.2, so marketplace update detection told
every existing install there was nothing new, and users quietly ran old
orchestrators for weeks believing they were current. Content on main is not a
release. A release is: manifests bumped, changelog written, tag pushed, GitHub
release cut.

## Checklist

1. **Bump BOTH manifests** to the new version — they must always agree:
   - `.claude-plugin/plugin.json` → `"version"`
   - `.claude-plugin/marketplace.json` → `"metadata"."version"`

   The marketplace manifest is the one update detection reads. Skipping it
   silently strands every existing install on the old version.

2. **Write the changelog entry** in `CHANGELOG.md` — heading format
   `## vX.Y.Z — YYYY-MM-DD`, newest first. Say what changed and why; numbers
   need their units ("per run", "per token", "per task") next to them.

3. **Commit** with the version in the message: `vX.Y.Z: <one-line summary>`.

4. **Tag and push**:
   ```bash
   git tag vX.Y.Z
   git push origin main --tags
   ```

5. **Cut the GitHub release** from the changelog entry:
   ```bash
   gh release create vX.Y.Z --title "chief-of-staff-kit vX.Y.Z" --notes "<changelog entry>"
   ```

6. **Verify from the outside** — the check a user would run:
   ```bash
   git ls-remote --tags https://github.com/skyremote/chief-of-staff-kit | tail -3
   curl -s https://raw.githubusercontent.com/skyremote/chief-of-staff-kit/main/.claude-plugin/plugin.json | grep version
   ```
   The tag must exist and the manifest version must match the changelog head.
   If they disagree, the release is not done.

## Rules

- No release without a manifest bump; no manifest bump without a release.
- Tags are immutable — a mistake gets a new patch version, never a re-tagged
  commit.
- If a release is ever found missing after the fact, retro-tag the exact
  release commit and cut the release late (done for v0.2.1–v0.4.1 in v0.4.2) —
  a navigable history matters more than a tidy one.
