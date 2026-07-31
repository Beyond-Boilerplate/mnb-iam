# Day 01 — Bootstrap & Mental Model

| Field | Value |
| --- | --- |
| **Week** | 1 — Fluency |
| **Time** | 2–2.5 hours |
| **Prereq** | macOS; OpenRouter account (for free track) or Anthropic auth |
| **Artifacts** | `artifacts/playbooks/day-01-session-notes.md` |

## Learning objectives

You will be able to:

- Explain the Claude Code → CCR → model path used by `scripts/free-claude-code`
- Launch Claude Code (`cc` or `claude`) against this SailPoint repo
- Toggle plan vs execution modes and explain when each reduces IAM risk
- Map four Claude primitives (skills, agents, hooks, MCPs) to IAM daily work
- Confirm Meridian IIQ is reachable while Claude has repo context

## IAM pain (today’s tax)

New IAM engineers lose half a morning to toolchain fog: wrong working directory, wrong IIQ URL, AI chat with no repo awareness, and no shared vocabulary for “what we will automate.” Today you name the stack and prove the loop works end-to-end.

## Claude concept

**Claude Code** is an agentic coding CLI that can read/edit files, run shell commands, and (later) call skills, hooks, agents, and MCPs. For IAM work, treat it as a **controlled junior** that must:

1. See the repo truth (`CLAUDE.md`, `config/`, `tools/`)
2. Prefer verify scripts over vibes
3. Never invent SSLA targets — ask or read docs

**Modes (Shift+Tab in many setups):** planning/thinking modes favor exploration; default execution edits and runs commands. For bank work, **plan first** when touching deploy paths.

```text
You  →  Claude Code  →  (optional CCR)  →  Model
              │
              ├─ files in Sailpoint SSD repo
              ├─ shell (build.sh, lab scripts)
              └─ later: skills / hooks / agents / MCPs
```

## Before you start

- [ ] Clone/open this repo at `Documents/Sailpoint`
- [ ] Internet available
- [ ] Willing to install tools via `setup-cc-free.sh` **or** already have Claude Code

## Lab procedure

### Task 1 — Install or validate Claude Code free routing

From `scripts/free-claude-code`, run the installer (or sandbox if you want isolation first — see parent README).

**Expected:** `cc` / `claude` launches; a routing smoke test succeeded or you can open a session against this repo.

### Task 2 — Open Claude in the SSD root

```bash
cd /Users/alishaghatane/Documents/Sailpoint
cc   # or: claude
```

Ask:

> Summarize CLAUDE.md in 8 bullets. List the build commands I should never forget.

**Expected:** Mentions `SPTARGET=sandbox`, `./build.sh clean war|deploy|importdynamic`, `config/`, do-not-edit `base/ga/`.

### Task 3 — Confirm IIQ lab

In a second terminal:

```bash
./tools/lab/up.sh
# or: ./tools/lab/docker/up.sh
```

Login: `http://localhost:8080/identityiq` (typically `spadmin` / lab password from docs).

In Claude:

> How do I verify HelloWorld smoke for Meridian CD?

**Expected:** Points at `./tools/iiq-verify/assert-mnb-objects.sh local` or equivalent.

### Task 4 — Mental model map (write it down)

Create `artifacts/playbooks/day-01-session-notes.md` with a table:

| Primitive | One-sentence definition | Meridian example you will automate by Day 30 |
| --- | --- | --- |
| Skill | | |
| Agent | | |
| Hook | | |
| MCP | | |

Seed your own drafts; refine later. Starter ideas: skill = tokenize XML; agent = BeanShell reviewer; hook = block `base/ga` edits; MCP = Jira ticket → plan.

### Task 5 — Run Ctrl+E / explanation habit once

Ask Claude to propose a shell command (e.g. `./build.sh -help` or list `tools/lab`). Use the product’s explanation / risk labeling if available. Write one note: which commands would you mark High risk in this repo?

## Deliverable

`artifacts/playbooks/day-01-session-notes.md` — mental model table + risk notes + confirmed IIQ URL.

## Acceptance criteria

- [ ] Claude session starts in repo root and paraphrases `CLAUDE.md` correctly
- [ ] IIQ login page loads locally
- [ ] Mental model table filled for all four primitives
- [ ] At least one “High risk for Meridian” command named (e.g. anything under `base/`, prod `SPTARGET`, mass delete)

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `cc` not found | Re-run installer; `source ~/.zshrc`; check alias |
| CCR not routing | Parent README CCR start/stop; sandbox HOME if testing |
| IIQ down | `./tools/lab/up.sh`; check Docker/Tomcat logs in `tools/lab` docs |
| Claude invents Ant on PATH | Correct it with CLAUDE.md; Day 02 hardens this |

## Stretch

- Run installer `--sandbox` once and contrast isolated vs host setup
- Skim `.claude/TUTORIAL.md` in this folder’s parent `.claude/` if present

## Knowledge check

1. Why prefer `./build.sh` over system `ant`?
2. What is `SPTARGET` for?
3. Name one thing Claude must never edit in this repo.
4. Skills vs agents in one sentence each?

### Answers

1. Bundled Ant + SailPoint SSB environment — system Ant drifts.  
2. Selects sandbox/dev/prod property sets (`*.target.properties`, etc.).  
3. `base/ga/` GA binary (or secrets).  
4. Skills = reusable procedural playbooks; agents = specialist workers with narrower roles/context.

## Navigation

← [README](README.md) · [Day 02 →](day-02-claude-md-and-repo-memory.md)
