# Day 10 — Skill: Export → Tokenize

| Field | Value |
| --- | --- |
| **Week** | 2 — Skills |
| **Time** | 2.5–3.5 hours |
| **Prereq** | Day 06; Day 08 template |
| **Artifacts** | `artifacts/skills/meridian-export-tokenize/SKILL.md` |

## Learning objectives

You will be able to:

- Encode the Meridian promotion path: clean export → `config/` path → tokens → properties
- Build a skill that proposes `%%TOKENS%%` without inventing token names blindly
- Cross-check against existing `*.target.properties`
- Practice on a real Application or Rule export (or HelloWorld as drill)

## IAM pain (today’s tax)

Tokenization is detail-heavy and easy to half-finish. Missed absolute paths survive in sandbox and break the next environment. This skill is your CAB pre-flight for XML.

## Claude concept

Skill procedure must **read property files first**, then propose tokens — never invent `%%MNB_FOO%%` without registering it.

```text
1) Locate export + target folder
2) Diff against hygiene checklist
3) Load sandbox/dev/prod target.properties
4) Propose replacements + property additions
5) Stop for human approve before write
```

## Before you start

- [ ] XML hygiene checklist available  
- [ ] At least one XML under `config/` or a cleaned export ready  

## Lab procedure

### Task 1 — Author skill

`artifacts/skills/meridian-export-tokenize/SKILL.md`

Include: naming table from `config/README.md`; forbidden Rewrite-Everything; require human approval before editing properties.

### Task 2 — Add `reference.md`

Paste folder map + common token patterns (file paths, JDBC, LDAP). Keep SKILL.md thin.

### Task 3 — Dry run on HelloWorld or Application

Prompt:

> Use meridian-export-tokenize on `<path>`. Propose tokens only; do not write yet.

Review proposal quality.

### Task 4 — Approved write (lab only)

If safe, apply token edits + property lines for sandbox. Re-run hygiene review.

## Deliverable

Skill (+ reference) and a before/after snippet saved under `artifacts/skills/meridian-export-tokenize/examples.md`.

## Acceptance criteria

- [ ] Skill refuses to invent tokens without property registration step  
- [ ] Example before/after captured  
- [ ] Aligns with SSB importdynamic expectations  
- [ ] Description triggers on “tokenize”, “export XML”, “promotion ready”

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Over-tokenization | Only env-specific values; leave business constants |
| Wrong folder | Enforce Type folder map in skill invariants |

## Stretch

- Script helper in `skills/.../scripts/list-tokens.sh` scanning `%%...%%`
- Tie to Lesson 101 promotion narrative

## Knowledge check

1. When is a hostname a token vs a constant?  
2. Why approve before writing properties?  
3. What naming convention for files?

### Answers

1. Token if env-specific.  
2. Properties affect entire target set — easy to break silently.  
3. `MNB-<Type>-<Business>.xml`.

## Navigation

[← Day 09](day-09-skill-lab-bootstrap.md) · [Day 11 →](day-11-skill-aggregation-triage.md)
