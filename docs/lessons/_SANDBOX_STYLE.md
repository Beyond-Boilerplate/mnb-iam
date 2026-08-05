# Enterprise Sandbox Path — style (lessons 201–255)

Practical, live, iterative. Distinct from Core Path [`_STYLE.md`](_STYLE.md).
Author coverage map (classic → sandbox): [`_COVERAGE_01_110.md`](_COVERAGE_01_110.md).

Target length per lesson: **~90–130 lines / ~1.1–1.8k words** (about 1.5–2× the old runbook style). Dense prose beats classic’s 280-line worksheet sprawl.

## Required sections (every lesson)

1. **Header** — Track, Time, Prereq, Stack, **Maps to classic**
2. **Why (1–2 lines)** — bank/ops outcome **and** a control/examiner hook
3. **What this is** — name the tool/service/IIQ feature; what it does in *this* estate vs Core CSV (no essay)
4. **Know these** — 3–5 term bullets **or** one small table + short ASCII/flow; include **one wrong-way** sentence
5. **Intent** — 3–6 bullets of what you will prove before leaving
6. **Before you start** — 4–6 checkboxes (stack, prereq objects, persona, evidence dir)
7. **Do this** — numbered steps; each step: **action** + **why** + **Expect:** one-liner. Prefer exact URLs, DNs, app names, curl paths
8. **If it fails** — symptom → fix list
9. **You are done when** — observable proof (SSO, Mailpit, SQL, Task Result, ldapsearch, etc.)
10. **Control note** — 3–5 lines: control name/owner, SLA target, evidence path under `~/iiq-lab-evidence/sandbox/` (not a binder worksheet)
11. **Quick check** — optional ≤3 short Qs with one-line answers inline
12. **Navigate** — prev/next + catalog

## Rules

- No worksheets, no Capstone essays, no “Further reading” blocks
- No fluff / motivational padding — every sentence earns its place
- Pull classic concepts into **Know these** and step **Expect:** lines; do not re-teach all of 01–110
- Encourage create → tweak → re-run against live targets (portal, Mailpit, LDAP, Gitea, Vault/PAM)
- Stack: `./tools/lab/docker/up.sh --enterprise`
- Evidence under `~/iiq-lab-evidence/sandbox/<lesson#>/` when asked

## Anti-patterns

- Bare 4–5 line checklists with no context
- Soft “discuss with your team” without a clickable next step
- Cloning classic Knowledge-check / Binder / Stretch sections wholesale
- Re-teaching all of lessons 01–110 theory — map with **Maps to classic** + **Know these** and move on
