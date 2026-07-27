# Lesson 95 — QuickLinks and Custom UI

**Level:** Intermediate  
**Track:** Rules, Workflows, Forms  
**Time:** 75–90 min  
**Prereq:** Lesson 94 — Forms and Field Validation  

**Lab data:**
- Repo: `lab-data/connectors/plugins/README.md`
- Repo: `lab-data/connectors/rules/README.md`
- Runtime: `~/iiq-lab-data/connectors/`
- Prior: Lesson 93 `MNB-WF-*` clones if linking to workflows

---

## Learning objectives

You will be able to:

- Explain IdentityIQ **QuickLinks** as governed entry points to workflows, forms, and URLs — not decoration
- Create Meridian QuickLinks `MNB-QL-Request-Payments` and `MNB-QL-BreakGlass-Info`
- Control visibility with dynamic scopes / capabilities (preview Lesson 96) so break-glass process links are not global
- Distinguish QuickLink XML config from full **plugin** UI customization and when to escalate
- Prove differential visibility with two personas and publish binder evidence for examiners

---

## Why this matters

**Business.** Users cannot adopt IAM if the only path is “ask IT to click seventeen menus.” When `rachel.evans` needs Payments dual-control access for a new operator, a curated QuickLink “Request Payments Access” steers her into the Lesson 94 form + Lesson 93 workflow — not a random Access Request with the wrong entitlement.

**Control / audit.** A QuickLink that exposes break-glass instructions (or worse, a grant path) to every employee is a control failure. Visibility must be capability-scoped; plugins must not embed secrets (`plugins/README.md`). Examiners ask: *Who can see privileged entry points, and what do they launch?*

---

## Concepts

### What a QuickLink is

A **QuickLink** is a configured home-page (or menu) entry that launches a workflow, opens a form/request UI, navigates to an internal URL, or invokes plugin UI. It is first-class configuration — exportable, promotable, and auditable — not a browser bookmark.

| Object | Controls | Meridian example |
| --- | --- | --- |
| **QuickLink** | What action users can start from home | `MNB-QL-Request-Payments` |
| **DynamicScope / population** | Who *sees* the link | Payments managers / ops |
| **Capability / right** | Who may *execute* the underlying action | Access request rights |
| **Plugin** | Packaged UI/REST when QuickLink + OOTB insufficient | Lessons 97–98 toolkit |

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| One global “Admin tools” QuickLink | Everyone sees privileged paths | Scoped links; break-glass info ≠ grant |
| Secrets in QuickLink URL query | Leak in screenshots/logs | Server-side config / vault only |
| Custom JSP before trying QuickLink | Upgrade and support cost | QuickLink → form/WF first; plugin later |
| Break-glass link that provisions | Undermines Lesson 109 | Informational URL only |

### Plugin vs QuickLink

From `plugins/README.md`: import install XML for QuickLinks; capability-based auth for custom REST; **no secrets in plugin XML**. QuickLinks cover 80% of Meridian navigation needs; plugins appear when you need custom REST or UI beyond OOTB request flows (Lessons 97–98).

---

## How it works

```
Home / QuickLinks bar
        │
        ├── MNB-QL-Request-Payments
        │         │
        │         ▼
        │   Access Request / MNB-WF-* + Lesson 94 form
        │         │
        │         ▼
        │   WIRE_INIT / payments entitlements (SoD still applies)
        │
        └── MNB-QL-BreakGlass-Info
                  │
                  ▼
            Read-only runbook URL (no provision)
```

| QuickLink type | Typical target | Audit angle |
| --- | --- | --- |
| Workflow | `MNB-WF-AccessRequest-Lab` | IdentityRequest evidence |
| URL | Internal runbook / wiki | Process awareness only |
| Plugin action | Custom REST/UI | Capability + Lesson 97 rights |

Visibility evaluation: IIQ intersects QuickLink enablement, category, DynamicScope/population, and the user’s capabilities. Missing any layer can hide a link from operators who need it — or show it to people who must not see it.

---

## Real-world setup (outside pure UI clicks)

### Step 1 — Navigation design card

1. List the three actions Meridian wants on the home page for IAM consumers (payments request, cert inbox if used, break-glass *process* info).
2. Name owners: IAM `helen.ross`; Payments business `rachel.evans`.
3. Forbid: QuickLinks that deep-link to Debug, Console, or secret stores.

### Step 2 — Scope populations first

1. Define who may see payments request: managers / payments ops populations (Lesson 96).
2. Define who may see break-glass info: IT + Security — not contractors like `raj.external` by default.
3. Document intended populations even if you configure scopes in Lesson 96.

### Step 3 — Promotion hygiene

1. Export QuickLink XML into `config/` for SSB (Lesson 101/108).
2. Environment-specific URLs use tokens — never hardcode prod runbook URLs in sandbox-only objects without tokens.

### Step 4 — Accessibility and ops

1. Labels must be plain language (“Request Payments Access”), not internal workflow names.
2. Help text points to Lesson 94 field rules (ticket `MNB-####`).

---

## Before you start

- [ ] IIQ up; Debug access to QuickLinks (or Gear → Global Settings → QuickLinks — version dependent)
- [ ] Read `lab-data/connectors/plugins/README.md`
- [ ] Lesson 93 clone workflow name available if linking to workflow
- [ ] Lesson 94 form concepts fresh
- [ ] Binder path: `~/iiq-lab-data/ui/quicklinks/`

---

## Lab procedure

### Task 1 — Inventory existing QuickLinks

You cannot govern what you have not named. Baseline first.

1. Open QuickLinks configuration list (UI or Debug → QuickLinks).
2. Note OOTB Access Request / Manage Accounts style links.
3. Screenshot current home QuickLink area as baseline.
4. Flag any link that looks privileged or points outside Meridian standards.

**Expected result:** Baseline inventory + screenshot.

**If it fails:** Use Debug object list; export one QuickLink XML for study.

### Task 2 — Create `MNB-QL-Request-Payments`

This is the guided path for dual-control entitlements — framing matters as much as the click target.

1. Add QuickLink named `MNB-QL-Request-Payments`.
2. Label: “Request Payments Access.”
3. Action: launch Access Request workflow **or** deep-link to request UI filtered for `MNB-WirePortal` / `MNB-Wire-Portal-WS` / logical payments rail if supported; else generic Access Request with Description instructing payments only.
4. Category: Access / Meridian.
5. Description: remind requesters of `businessJustification` + `MNB-[0-9]{4,}` ticket (Lesson 94).
6. Save.

**Expected result:** QuickLink object exists with Meridian label and payments intent.

**If it fails:** URL QuickLink to internal runbook is acceptable interim — document limitation.

### Task 3 — Create `MNB-QL-BreakGlass-Info`

Break-glass must never be a silent privilege grant from the home page.

1. Add QuickLink `MNB-QL-BreakGlass-Info`.
2. Type: URL to lab runbook placeholder (IIQ help page or binder-published static note) — **do not** link production secret stores or vault consoles.
3. Label: “Break-Glass Process (Read Only).”
4. Description: “Does not grant access; process overview only. See Lesson 109 for sealed `spadmin`.”
5. Save.

**Expected result:** Informational QuickLink created; clearly non-provisioning.

### Task 4 — Scope visibility (preview Lesson 96)

1. Restrict `MNB-QL-Request-Payments` to population of payments ops / managers if DynamicScope available — include `rachel.evans`, managers of `priya.wire` / `marcus.approve` conceptually.
2. Restrict `MNB-QL-BreakGlass-Info` to IT + Security capabilities/populations — not all employees.
3. If scoping UI missing: document intended populations in binder as **mandatory** Lesson 96 follow-up — do not leave break-glass global without a note.

**Expected result:** Scopes configured **or** written intent table.

### Task 5 — Verify as two users

Differential visibility is the control evidence.

1. Log in as `spadmin` — confirm both links visible (or expected for admin).
2. Log in as a limited lab user (e.g., `raj.external` if enabled) — confirm payments/break-glass links **hidden** per design.
3. Capture two screenshots.

**Expected result:** Differential visibility evidence in binder.

**If it fails:** Simulate by checking DynamicScope script results; document; still complete intent table.

### Task 6 — Plugin vs QuickLink decision note

Using `plugins/README.md`, write:

1. When QuickLink-to-workflow is enough (this lesson).
2. When to build `mnb-iam-toolkit` plugin (REST ping + QuickLink install XML) — Lessons 97–98.
3. Checklist: no secrets in QuickLink URL query strings; no Debug links.

**Expected result:** Decision note page.

### Task 7 — Examiner question drill

*“Show how a payments manager starts a dual-control access request without using SystemAdministrator menus.”*

Answer: Home → `MNB-QL-Request-Payments` → scoped visibility → Access Request / `MNB-WF-*` → Lesson 94 validated fields → SoD still evaluates `WIRE_INIT`/`WIRE_APPR`.

**Expected result:** Written three-step examiner answer.

### Task 8 — Export / CHANGELOG

1. Note export path for SSB later: QuickLink XML under `config/`.
2. CHANGELOG: “Lesson 95 Meridian payments + break-glass-info QuickLinks.”

**Expected result:** Promotion note + CHANGELOG line.

### Task 9 — Accessibility and label review

QuickLinks are user-facing controls — labels matter under exam and under WCAG-minded ops.

1. Confirm labels use plain language (“Request Payments Access”), not internal workflow names.
2. Confirm `MNB-QL-BreakGlass-Info` description states it does **not** grant access.
3. Note who maintains the runbook URL when it moves (IAM vs platform).

**Expected result:** Label/accessibility checklist initialed.

---

## Acceptance criteria

- [ ] Baseline inventory captured
- [ ] `MNB-QL-Request-Payments` created
- [ ] `MNB-QL-BreakGlass-Info` created as read-only process link
- [ ] Visibility scoping done or explicitly deferred to Lesson 96 with intent table
- [ ] Two-user visibility evidence captured
- [ ] Plugin vs QuickLink note + examiner answer written
- [ ] Label/accessibility checklist initialed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Link missing on home | Not enabled / category / prefs | Enable QuickLink; check user prefs |
| Everyone sees break-glass | No scope | Add DynamicScope; Lesson 96 |
| Workflow launch error | Wrong WF name | Point to valid `MNB-WF-*` or OOTB |
| URL 404 | Bad href | Fix placeholder; use IIQ-relative path |
| Secrets in URL | Anti-pattern | Remove; use server-side config |
| Contractor sees payments QL | Scope too broad | Tighten population; retest as `raj.external` |

---

## Training binder evidence

- Baseline home screenshot
- Two QuickLink config screenshots (redact any URLs with secrets)
- Scope intent / config
- Dual-user visibility screenshots
- Plugin vs QuickLink decision note + examiner answer

---

## Knowledge check

1. What is a QuickLink?
2. Name both Meridian QuickLinks created here.
3. Why is the break-glass link informational only?
4. Where are plugin packaging notes for Meridian?
5. Which lesson covers workgroups, capabilities, and scopes next?
6. Why must QuickLink URLs never carry secrets?

### Answers

1. A configured entry point to a workflow, form, URL, or plugin UI from the IIQ home experience.
2. `MNB-QL-Request-Payments` and `MNB-QL-BreakGlass-Info`.
3. It must not grant privileged access — only explain process; grants stay request/PAM controlled (Lesson 109).
4. `lab-data/connectors/plugins/README.md`.
5. Lesson 96 — Workgroups, Capabilities, and Scopes.
6. URLs appear in screenshots, logs, and browser history — secrets belong in vaults/server config.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “QuickLinks” and “DynamicScope” for version-specific configuration.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search “QuickLink DynamicScope” for visibility troubleshooting.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — QuickLink vs plugin packaging threads.
- [OWASP Cheat Sheet — Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) — why secrets never belong in URLs or install XML.
- [WCAG 2.2 Overview](https://www.w3.org/WAI/standards-guidelines/wcag/) — plain-language labels and accessible navigation for home QuickLinks.

---

## Stretch lab

Draft install XML snippet (names only) that would import both QuickLinks for SSB promotion — align with plugin README checklist. Optionally add `rightRequired` notes for Lesson 96 capability gating.

---

## Summary

- QuickLinks steer Meridian users into approved payments and process paths without sharing admin menus.
- Visibility scoping is part of the control — not optional polish; break-glass info must not be global.
- Plugins extend UI when QuickLinks are not enough; secrets never go in XML or URLs.

---

**Previous:** [Lesson 94 — Forms and Field Validation](94-forms-and-field-validation.md)  
**Next:** [Lesson 96 — Workgroups, Capabilities, and Scopes](96-workgroups-capabilities-scopes.md)
