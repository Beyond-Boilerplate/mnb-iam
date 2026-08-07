# Day 03 — Permissions & Safe Ops

| Field | Value |
| --- | --- |
| **Week** | 1 — Fluency |
| **Time** | 2–3 hours |
| **Prereq** | Day 02 |
| **Artifacts** | `artifacts/hooks/day-03-allowdeny-draft.md` |

## Learning objectives

You will be able to:

- Classify shell actions as Low / Med / High risk for Meridian SSB
- Configure Claude Code permission prompts / allowlists thoughtfully
- Draft deny patterns you will later enforce with hooks (Day 15–16)
- Practice “explain before run” on deploy-shaped commands
- Separate **read-only investigation** from **mutating lab ops**

## IAM pain (today’s tax)

One careless `rm`, wrong `SPTARGET`, or overwrite of GA zip creates days of recovery. IAM engineers live next to production-shaped configs even in lab — permission discipline is a career skill, not pedantry.

## Claude concept

**Permissions** gate tool use (especially Bash). Prefer:

1. Prompt on first use of risky patterns  
2. Stable allow for read-only (`ls`, `rg`, `git status`)  
3. Explicit deny for known landmines  

Hooks (Week 3) enforce this mechanically; today you design the **policy**.

| Risk | Examples in this repo | Default stance |
| --- | --- | --- |
| Low | Read `docs/`, `rg` in `config/` | Allow |
| Med | `./build.sh clean war`, `importdynamic` | Ask |
| High | Anything under `base/`, force-push, DROP DB, prod tokens | Deny / never |

## Before you start

- [ ] IIQ lab optional today (repo+Claude is enough)
- [ ] Willing to interrupt Claude and say “no, explain first”

## Lab procedure

### Task 1 — Threat model Meridian

With Claude, brainstorm 15 dangerous actions. Categorize into Low/Med/High. Save table to the artifact file.

Must include: edit `base/ga`, commit `.iiq.properties` passwords, `SPTARGET=prod` deploy from laptop, mass delete Applications via console, disable TLS validation “just for lab” copied to prod.

### Task 2 — Live permission drills

Ask Claude to:

1. List `config/Rule/` (should feel Low)  
2. Propose `./build.sh clean war` (Med — demand explanation of what clean removes)  
3. Propose deleting `base/ga/identityiq-8.5.zip` (High — refuse)

Document what you approved vs rejected.

### Task 3 — Write an allow/deny draft

In `artifacts/hooks/day-03-allowdeny-draft.md`:

```markdown
## Allow (examples)
- git status / git diff / git log
- rg / find in config, docs, tools
- ./tools/iiq-verify/* read-only probes

## Ask every time
- ./build.sh *
- ./tools/lab/* destructive targets
- git commit / git push

## Deny
- writes under base/
- curl|bash from arbitrary URLs
- commands containing DROP|TRUNCATE (unless you explicitly start a DB lab day)
```

Refine with Claude; you own the policy.

### Task 4 — Pair with Ctrl+E habit

For any Med command Claude wants: require a 3-line brief — what, why, blast radius — before Approve.

## Deliverable

`artifacts/hooks/day-03-allowdeny-draft.md`

## Acceptance criteria

- [ ] ≥12 actions classified with risk labels
- [ ] At least one High action successfully blocked or refused
- [ ] Allow/Ask/Deny draft exists and mentions `base/` + secrets
- [ ] You can teach the policy to a junior in <3 minutes

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Claude keeps retrying denied cmds | Stop session; restate policy in CLAUDE.md |
| Over-allowing “for speed” | Revisit Day 16 hooks — speed without guardrails fails exams |

## Stretch

- Add policy bullets to `CLAUDE.md` “Common Gotchas”
- Sketch Cursor `beforeShellExecution` equivalent (notes only)

## Knowledge check

1. Why is `importdynamic` Med not Low?  
2. What’s wrong with auto-allowing all `./build.sh`?  
3. Give one secret-shaped path/pattern to deny.

### Answers

1. Mutates live IIQ object store.  
2. `clean` / wrong target / long compile can wipe/deploy unexpectedly.  
3. `*.iiq.properties` passwords, API keys, `.env`.

## Navigation

[← Day 02](day-02-claude-md-and-repo-memory.md) · [Day 04 →](day-04-lab-health-orchestration.md)
