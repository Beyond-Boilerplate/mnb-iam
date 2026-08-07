# Playbook: release guardrails (pre-release checklist automation)

**Trigger:** you're about to cut a release and want the boring, easy-to-forget checks done consistently instead of from memory.

**Composes:** hook (pre-release hard checks) + skill (changelog draft) + plan mode (see the release plan before anything executes) + optional MCP (kick off the actual CI/deploy job).

## Steps

1. **Plan mode — see the release plan before it runs.**
   - Ask Claude, in Plan mode, to lay out what this release actually touches: version bump, migration files, feature flags being flipped, anything marked "do not ship without X."
   - **Why plan mode specifically:** a release is exactly the "unclear blast radius until you look" case module 09 describes — you want the file/step list before anything executes.

2. **Hook — pre-release hard checks.**
   - A hook (or a scripted check the plan calls out) verifies non-negotiables: no `TODO`/`FIXME` in changed prod code, no debug logging left at INFO+, version bumped consistently, migrations have a rollback path documented.
   - **Why a hook and not just asking Claude to "check for this":** these are mechanical, deterministic checks — a hook enforces them the same way every time, whether or not the model remembers to look.

3. **Skill — draft the changelog / release notes.**
   - Invoke a skill that reads the merged PRs/commits since the last tag and drafts changelog entries grouped by type (feature, fix, breaking change).
   - A human edits this before it's the real release notes — the skill removes the blank-page problem, not the judgment.

4. **Human gate — approve the release plan.**
   - A person reviews the plan-mode output + hook check results + changelog draft and explicitly approves cutting the release.
   - **This is never automated**, even if every check passed — "all checks green" and "safe to ship right now" are related but not identical questions (freeze windows, on-call coverage, customer-facing timing).

5. **(Optional) MCP — kick off the actual CI/deploy pipeline.**
   - If a CI/deploy MCP is configured, trigger the release job directly from the approved plan.
   - **Fallback if MCP is down:** the human runs the existing release script/pipeline manually — the guardrail checks and changelog draft from steps 1–3 still hold.

## What "it worked" looks like

- Plan mode surfaced the actual file/version/migration list before any check ran, and nothing in the eventual release was a surprise.
- The pre-release hook caught at least one real mechanical issue (or ran clean and you trust why).
- The changelog draft needed editing, not rewriting from scratch.
- A specific human approved the release, distinct from "all automated checks passed."

## Known gaps / open questions

<!-- Fill in after your dry run: what did this playbook get wrong about your real release process? -->
