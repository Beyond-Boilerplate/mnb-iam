# Meridian IAM Academy — Enterprise lesson style guide (v2)

Use this for every lesson authored or rewritten. Voice: **a senior IAM engineer teaching a new teammate**, not a checklist generator. Every lesson must read as a true tutorial — explain, then do, then verify.

## Required sections (in order)

1. **Title block** — Lesson number, title, level, track, time, prereq, lab data paths
2. **Learning objectives** — 4–7 measurable bullets ("You will be able to…")
3. **Why this matters** — 1 short business paragraph + 1 control/audit paragraph, grounded in a concrete Meridian scenario (a named persona, a real consequence)
4. **Concepts** — See "Concept depth rules" below. This is the teaching core, not a warm-up.
5. **How it works** *(Intermediate+ and all connector lessons)* — Architecture, object model, and data flow of the target system and the connector. At least one table AND one ASCII diagram.
6. **Real-world setup** *(connector lessons)* — What a production engineer must do **outside IIQ** before the connector works (service accounts, app registrations, API scopes, network, IQService, least-privilege policy). Written step-by-step even when the lab uses mocks, so the reader could execute it against a real tenant.
7. **Before you start** — Checklist (IIQ up, lab files copied, prior objects exist)
8. **Lab procedure** — Numbered tasks (Task 1, Task 2…). Each task must include:
   - A short **framing paragraph first**: why this step exists and what it would look like in production
   - Exact navigation / commands
   - **Expected result** callout (what the screen/file should show)
   - Optional **If it fails** one-liner
9. **Acceptance criteria** — Checkbox list for "done"
10. **Troubleshooting** — 3–6 common failures with fixes
11. **Training binder evidence** — What to screenshot / note for enterprise training records
12. **Knowledge check** — 4–6 questions (answers in an **Answers** subsection at bottom of that section)
13. **Further reading** *(required for Intermediate+ / connector / policy lessons)* — 3–6 curated links: SailPoint product docs, SailPoint Community/Compass topics, target-vendor admin guides, and relevant standards/whitepapers (NIST, FFIEC, CIS). One-line annotation per link explaining why it's worth the reader's time. Only link real, stable resources; if unsure of an exact URL, link the docs landing page and say what to search for.
14. **Stretch lab** — Optional harder practice
15. **Summary** — 3 bullets of what you built/learned
16. **Navigation** — Previous / Next links

## Concept depth rules

- **Define before use.** Every IIQ or target-system term (aggregation, native identity, Org Unit, service principal, ARN…) gets a plain-English definition the first time it appears.
- **2–4 concept subsections** for Intermediate+ topics, each anchored by a **real-life Meridian example** — e.g. "Sofia goes on leave; her Google account is suspended but her Shared Drive group still grants access. This is why groups are entitlements, not attributes."
- Contrast with the wrong way: show the naive approach and why it fails at a bank under exam.
- At least one comparison table and one ASCII flow per lesson; more for complex topics.

## Tutorial voice rules

- Teach → do → verify. Never open a task with a bare imperative; one or two sentences of context first.
- Imperative steps after the framing: "Open…", "Click…", "Run…", "Confirm…"
- Name Meridian objects with `MNB-` prefix
- Use real lab personas: `helen.ross`, `priya.wire`, `marcus.approve`, `jordan.reed`, `raj.external`, `samir.hassan`, `sofia.torres`, `kai.nguyen`, `amelia.brooks`, `nina.joiner`
- Corporate email domain: `@meridiannb.com`
- Paths: `~/iiq-lab-data/...` and repo `lab-data/...`
- IIQ URL: `http://localhost:8080/identityiq` (mention homelab URL only as alternate)
- Prefer "Account Aggregation task" over vague "run aggregation"
- Never invent UI labels you are unsure of—say "or equivalent menu path"
- Include enterprise framing: control owner, SLA, evidence, examiner question

## Realistic onboarding rule (no more "CSV = the connector")

- Lessons 09–16 use Delimited File deliberately to teach governance mechanics. Each of those lessons **must** include a **"Production reality"** callout box naming the real connector (AD Direct, AWS IAM, Salesforce, Office365…) and linking forward to the Part II lesson that teaches it.
- Connector lessons (51+) teach the **native connector as the primary path**: real prerequisites, real field-by-field configuration, real aggregation/provisioning behavior. The **lab-without-live-target** path stays, but as a clearly labeled fallback ("If you have no tenant…"), never as the main event.
- Where `docker-compose.connectors.yml` provides a live backend (OpenLDAP, Postgres), the live path is mandatory, not optional.

## Length targets

- Foundations / early: ~200–300 lines
- Intermediate governance (correlation, roles, SoD, certs, LCM): ~250–350 lines
- Connector lessons — directories, databases, SaaS, cloud, ERP: **~320–450 lines** (Google, M365, AWS, Workday, SAP, Okta and peers must justify their runtime with real setup depth)
- Capstone modules (50, 110): ~300–400 lines

## Filename

`docs/lessons/NN-slug.md` — keep existing slug; only deepen content.
