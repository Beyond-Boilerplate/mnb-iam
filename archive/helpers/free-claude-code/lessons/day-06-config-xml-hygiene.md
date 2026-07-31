# Day 06 — Config XML Hygiene

| Field | Value |
| --- | --- |
| **Week** | 1 — Fluency |
| **Time** | 2.5–3 hours |
| **Prereq** | Day 05; familiarity with Lesson 03 naming |
| **Artifacts** | `artifacts/playbooks/xml-hygiene-checklist.md` |

## Learning objectives

You will be able to:

- Spot dirty Debug exports (IDs, transient attrs, env-hardcoded paths)
- Apply `MNB-<Type>-<Business>.xml` naming and folder map
- Use Claude for **diff-aware** review of Application/Rule/Policy XML
- Draft a tokenize checklist (`%%TOKENS%%`) before Week 2’s skill

## IAM pain (today’s tax)

IAM engineers paste Debug XML into git with hostnames, absolute Windows paths, and created/modified noise. Promotion to higher envs fails or silently points at sandbox fileshares. Hygiene is the difference between CAB confidence and rollback theater.

## Claude concept

**Diff-aware editing:** always show Claude the surrounding objects and property files. Prefer “review this export” over “rewrite the Application from scratch.”

```text
IIQ UI craft → clean export → config/<Type>/MNB-*.xml → %%TOKENS%% → properties → importdynamic
```

## Before you start

- [ ] Read `config/README.md` folder map
- [ ] Skim `docs/lessons/03-lab-hygiene-and-naming.md`
- [ ] Have either an existing `config/**/*.xml` or export one lesson object

## Lab procedure

### Task 1 — Inventory config tree with Claude

> Map config/ folders to object types. Flag any file not matching MNB- naming.

### Task 2 — Hygiene review protocol

Pick one XML (Rule HelloWorld is fine). Ask:

> Review for promotion readiness: naming, secrets, hardcoded hosts/paths, unnecessary ids, token candidates. Output Severity | Finding | Fix.

Save the protocol as the day’s checklist.

### Task 3 — Token brainstorm

From `sandbox.target.properties` (and siblings), list tokens Meridian already uses. Ask Claude which Application fields usually need tokens (file paths, JDBC URLs, LDAP hosts).

### Task 4 — Red-team a bad export

Have Claude generate a **deliberately bad** sample Application XML snippet (as a markdown example in artifacts — not imported) with 6 violations. You list them first, then compare.

## Deliverable

`artifacts/playbooks/xml-hygiene-checklist.md` (+ optional bad-export counterexample)

## Acceptance criteria

- [ ] Checklist covers naming, tokens, secrets, dirty Debug fields
- [ ] Real file reviewed with severity findings
- [ ] Token list cross-checked against `*.target.properties`
- [ ] No bad sample imported into live IIQ

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Claude rewrites whole XML | Constrain: “comment findings only; no rewrite unless asked” |
| Unsure of folder | `config/README.md` map |

## Stretch

- Run `git log -- config/` and summarize promotion commit style
- Preview Day 10 skill outline in 10 bullets

## Knowledge check

1. Correct filename for HR Application export?  
2. Why strip some Debug metadata?  
3. Where do token values live?

### Answers

1. `config/Application/MNB-Application-HR.xml` (pattern).  
2. Noise + env-specific identity collisions.  
3. `*.target.properties` / env property files.

## Navigation

[← Day 05](day-05-ssb-build-deploy-loop.md) · [Day 07 →](day-07-evidence-and-verify.md)
