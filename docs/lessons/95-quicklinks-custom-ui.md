# Lesson 95 — QuickLinks and Custom UI

**Level:** Intermediate  
**Track:** Rules, Workflows, Forms  
**Time:** 60–90 min  
**Prereq:** Lesson 94 — Forms and Field Validation  

**Lab data:**
- Repo: `lab-data/connectors/plugins/README.md`
- Repo: `lab-data/connectors/rules/README.md`
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Explain IdentityIQ **QuickLinks** as entry points to workflows, forms, and URLs
- Create Meridian QuickLinks `MNB-QL-Request-Payments` and `MNB-QL-BreakGlass-Info`
- Control visibility with dynamic scopes / capabilities (preview Lesson 96)
- Distinguish QuickLink XML config from full **plugin** UI customization
- Publish binder evidence and hand off to workgroups/capabilities lesson

---

## Why this matters

**Business.** Users cannot adopt IAM if the only path is “ask IT to click seventeen menus.” Curated QuickLinks guide payments and privileged processes.

**Control / audit.** A QuickLink that exposes break-glass to everyone is a control failure. Visibility must be capability-scoped; plugins must not embed secrets (`plugins/README.md`).

---

## Concepts

```
Home / QuickLinks bar
        │
        ├── Workflow QuickLink → LCM / custom WF
        ├── External URL QuickLink → runbook / wiki
        └── Plugin snippet QuickLink → custom UI (later lessons)
```

| Object | Meridian use |
| --- | --- |
| QuickLink | First-class navigation to approved actions |
| DynamicScope / population | Who sees the link |
| Capability | Who may execute underlying action |
| Plugin | Packaged UI/REST when QuickLink + OOTB insufficient |

From `plugins/README.md`: import install XML for QuickLinks; capability-based auth for custom REST; no secrets in plugin XML.

---

## Before you start

- [ ] IIQ up; Debug access to QuickLinks (or Gear → Global Settings → QuickLinks—version dependent)
- [ ] Read `lab-data/connectors/plugins/README.md`
- [ ] Lesson 93 clone workflow name available if linking to workflow
- [ ] Binder: `ui/quicklinks/`

---

## Lab procedure

### Task 1 — Inventory existing QuickLinks

1. Open QuickLinks configuration list.
2. Note OOTB Access Request / Manage Accounts style links.
3. Screenshot current home QuickLink area as baseline.

**Expected result:** Baseline inventory + screenshot.

**If it fails:** Use Debug → QuickLinks object list.

---

### Task 2 — Create `MNB-QL-Request-Payments`

1. Add QuickLink named `MNB-QL-Request-Payments`.
2. Label: “Request Payments Access.”
3. Action: launch Access Request workflow **or** deep-link to request UI filtered for `MNB-WirePortal` / `MNB-Logical-Payments-Rail` if supported; else generic Access Request with Description instructing payments only.
4. Category: Access / Meridian.
5. Save.

**Expected result:** QuickLink object exists with Meridian label.

**If it fails:** URL QuickLink to internal runbook is acceptable interim—document limitation.

---

### Task 3 — Create `MNB-QL-BreakGlass-Info`

1. Add QuickLink `MNB-QL-BreakGlass-Info`.
2. Type: URL to lab runbook placeholder `http://localhost:8080/identityiq` help page **or** binder-published static note path—do not link production secret stores.
3. Label: “Break-Glass Process (Read Only).”
4. Description: “Does not grant access; process overview only.”
5. Save.

**Expected result:** Informational QuickLink created; clearly non-provisioning.

---

### Task 4 — Scope visibility (preview Lesson 96)

1. Restrict `MNB-QL-Request-Payments` to population of payments ops / managers if DynamicScope available—include `rachel.evans`, managers of `priya.wire`/`marcus.approve` conceptually.
2. Restrict `MNB-QL-BreakGlass-Info` to IT + Security capabilities/populations—not all employees.
3. If scoping UI missing: document intended populations in binder as mandatory Lesson 96 follow-up.

**Expected result:** Scopes configured **or** written intent table.

**If it fails:** Intent table satisfies lab; do not leave break-glass link global without note.

---

### Task 5 — Verify as two users

1. Log in as `spadmin`—confirm both links visible (or expected).
2. Log in as a limited lab user (e.g., `raj.external` if enabled)—confirm payments/break-glass links **hidden** per design.
3. Capture two screenshots.

**Expected result:** Differential visibility evidence.

**If it fails:** Simulate by checking DynamicScope script results; document.

---

### Task 6 — Plugin vs QuickLink decision note

Using `plugins/README.md`, write:

1. When QuickLink-to-workflow is enough.
2. When to build `mnb-iam-toolkit` plugin (REST ping + QuickLink install XML)—Lessons 97–98.
3. Checklist item: no secrets in QuickLink URL query strings.

**Expected result:** Decision note page.

---

## Acceptance criteria

- [ ] Baseline inventory captured
- [ ] `MNB-QL-Request-Payments` created
- [ ] `MNB-QL-BreakGlass-Info` created as read-only process link
- [ ] Visibility scoping done or explicitly deferred to Lesson 96 with intent table
- [ ] Two-user visibility evidence captured
- [ ] Plugin vs QuickLink note written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Link missing on home | Not enabled / category | Enable QuickLink; check user prefs |
| Everyone sees break-glass | No scope | Add DynamicScope; Lesson 96 |
| Workflow launch error | Wrong WF name | Point to valid `MNB-WF-*` or OOTB |
| URL 404 | Bad href | Fix placeholder; use IIQ-relative path |
| Secrets in URL | Anti-pattern | Remove; use server-side config |

---

## Training binder evidence

- Baseline home screenshot
- Two QuickLink config screenshots
- Scope intent / config
- Dual-user visibility screenshots
- Plugin vs QuickLink decision note
- Pointer to Lesson 96 for capabilities/workgroups

---

## Knowledge check

1. What is a QuickLink?
2. Name both Meridian QuickLinks created here.
3. Why is the break-glass link informational only?
4. Where are plugin packaging notes for Meridian?
5. Which lesson covers workgroups, capabilities, and scopes next?

### Answers

1. A configured entry point to a workflow, form, URL, or plugin UI from the IIQ home experience.  
2. `MNB-QL-Request-Payments` and `MNB-QL-BreakGlass-Info`.  
3. It must not grant privileged access—only explain process; grants stay request/PAM controlled.  
4. `lab-data/connectors/plugins/README.md`.  
5. Lesson 96 — Workgroups, Capabilities, and Scopes.

---

## Stretch lab

Draft install XML snippet (names only) that would import both QuickLinks for SSB promotion—align with plugin README checklist item 2.

---

## Summary

- QuickLinks steer Meridian users into approved payments and process paths.
- Visibility scoping is part of the control—not optional polish.
- Plugins extend UI when QuickLinks are not enough; secrets never go in XML/URLs.

---

**Previous:** [Lesson 94 — Forms and Field Validation](94-forms-and-field-validation.md)  
**Next:** [Lesson 96 — Workgroups, Capabilities, and Scopes](96-workgroups-capabilities-scopes.md)
