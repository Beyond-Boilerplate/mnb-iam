# 50 OOTB IdentityIQ UX gaps (operator discoverability)

**Scope:** Stock SailPoint IdentityIQ 8.x **operator UX** — hard to find, prove, or safely change from primary menus without Debug / tribal knowledge.  
**Not:** Meridian MCP/API gaps (see [`UI-VS-API-GAPS.md`](UI-VS-API-GAPS.md)).  
**Seed:** Lab Joiner (Events processed = 1, empty WorkflowCase, proof in Task Results) · Aug 2026.

Interactive filter view: Cursor canvas `ootb-iiq-ux-gaps-50`.

| Sev | Count |
| --- | ---: |
| Critical | 8 |
| High | 24 |
| Medium | 18 |

---

## Lifecycle / JML

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-01 | Critical | No Joiner run history screen | Events processed visible; no Lifecycle history | Monitor → Task Results `Event: Person` |
| UX-02 | Critical | WorkflowCase empty after Joiner | RapidSetup + `approvalScheme=none` finishes instantly | Treat TaskResult type=Workflow as proof |
| UX-03 | High | Create silent on existing cube | Re-agg Nina never re-fires | New `userId` or AttributeChange |
| UX-04 | Critical | Process events buried on Refresh | Agg+Refresh without it = zero launches | Document Refresh task checkbox |
| UX-05 | High | Stock + custom Create double-fire | Joiner + MNB-LE both Create | Inventory / disable overlaps |
| UX-06 | High | LoA vs Leaver not distinguished | Easy to wire LOA → Leaver WF | Separate `MNB-LE-*` + naming |
| UX-07 | Medium | Rapid Setup vs LE naming split | Search misses one family | Inventory both patterns |
| UX-08 | Medium | No per-identity JML timeline | Cube lacks joiner→leaver storyboard | Task Results filter / console |

## Workflows / evidence

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-09 | Critical | WorkflowCase not in primary menus | Operators open Debug first | Prefer Task Results |
| UX-10 | High | Monitor → Processes sparse | Empty / license variance | Task Results + Analytics |
| UX-11 | High | No launches on Lifecycle Event page | Config without run history | Search Task Results by event name |
| UX-12 | High | Email success not on Joiner TaskResult | WF Success, mail failed in logs | SMTP + EmailTemplate + mail sink |
| UX-13 | Medium | No operator step debugger | Failed step → logs/XML | Open WorkflowCase vars if stuck |
| UX-14 | High | OOTB edit not blocked | Patch RapidSetup in place | Always clone `MNB-WF-*` |
| UX-15 | Medium | IR / WorkflowCase / TaskResult triad | Joiner often only TaskResult | Teach evidence by journey |

## Identity / correlation

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-16 | High | Unanswered account selections noise | 96 warnings drown Events=1 | Hygiene debt; don’t fail Joiner |
| UX-17 | High | No “why didn’t correlate” UI | Orphans need manual app hunt | Analytics + Lesson 19 |
| UX-18 | Medium | Manager blank root-cause opaque | Map vs missing manager | HR row + ObjectConfig + manager cube |
| UX-19 | Medium | Display vs login search | Nina Foster vs nina.joiner | Search identity name / userId |
| UX-20 | High | No “created by which agg” badge | Can’t link cube → TaskResult | Timestamp + nearest Aggregate |
| UX-21 | Medium | Attr promotion = ObjectConfig | exceptions never lands | ObjectConfig + Refresh Attributes |
| UX-22 | Medium | Merge identities obscure | Dupes after bad correlation | Document merge; prevent via rules |

## Requests / work items

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-23 | High | Owner vs proxy inbox | spadmin can’t see Emily’s items | Login as manager / forward (36b) |
| UX-24 | Medium | Approved vs provision lag | Looks stuck after approve | Request plan + Task Results |
| UX-25 | Medium | Why not requestable unexplained | Missing from Manage Access | requestable flag + LCM config |
| UX-26 | High | Dual-control collapse | Same human both Wire legs | Process/workgroups; UI won’t stop |
| UX-27 | Medium | Form answers buried | Audit can’t reopen payload | IdentityRequest detail / export |
| UX-28 | Medium | Sunset easy to miss | Temp access looks permanent | Request detail + sunset tasks |

## Certifications

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-29 | High | Progress vs sign-off split | “Done” but unsigned | Progress + sign-off screens |
| UX-30 | Medium | Remediation not one binder view | Revoke ≠ account gone | Decision + re-agg + cube |
| UX-31 | Medium | Bulk certify temptation | Rubber-stamp large pops | Targeted campaigns + policy |
| UX-32 | High | Email vs Work Item disconnect | Mail says certify; inbox empty | Cert notifications + owner |
| UX-33 | Medium | Edit definition mid-flight | Confuses running campaign | Freeze; new campaign |

## Policy / SoD

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-34 | High | Violation timeline thin | No open→mitigate→expire strip | Violations list + Audit |
| UX-35 | Medium | Simulation results not sticky | Impact analysis ephemeral | Save Policy Impact TaskResult |
| UX-36 | Medium | Constraint editor opaque | Role SOD packs hard to see | External matrix → careful entry |
| UX-37 | High | Residual after mover quiet | Role gone, WIRE_INIT remains | Residual hunt (Lesson 30) |

## Apps / connectors

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-38 | Critical | Green Success / zero updates | Wrong path still “ok” | Counters + persona spot-check |
| UX-39 | High | Test Connection ≠ schema health | Green test, broken map | Schema preview + sample get |
| UX-40 | Medium | Watermark/partition buried | Delta agg stuck | TaskDefinition args |
| UX-41 | High | Create identities on targets | AD creates cubes by mistake | Authoritative HR only |
| UX-42 | Medium | Feature matrix not in app UI | Guess disable/unlock support | Lesson 55 + connector docs |

## Roles / birthright

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-43 | High | Assigned vs detected misread | Role “there,” no provision | Lesson 27; check Accounts |
| UX-44 | Medium | Assignment miss silent | Refresh Roles Success, no role | Rule filters + population |
| UX-45 | Medium | IT vs business pack unclear | Cube lists both | `MNB-Role-*` / `MNB-IT-*` naming |

## Admin / Debug dependence

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-46 | Critical | EmailTemplate Debug-first | Hard to browse templates | Debug EmailTemplate (L49) |
| UX-47 | Critical | IdentityTrigger advanced = Debug | Wizard incomplete for filters | Setup LE + Debug filters |
| UX-48 | High | Export/import not operator UX | Promotion feels SSD-only | Lessons 101 / 108 |

## Search / reporting

| ID | Sev | Gap | Symptom | Workaround |
| --- | --- | --- | --- | --- |
| UX-49 | High | Saved searches poorly shared | Rebuild Joiner evidence query | Canonical runbook searches |
| UX-50 | Medium | Audit thin for lifecycle proof | Examiners want Joiner trail | Task Results + binder screenshots |

---

## Operator model (three layers)

1. **Config** — Setup menus (Lifecycle Events, apps, roles) for happy-path create.  
2. **Evidence** — **Monitor → Task Results** for auto-JML (`MNB-LE-Joiner-HR: Saransh Bhandari`).  
3. **Deep authoring** — Debug / XML clones for EmailTemplates, WF steps, trigger filters.

Related: [`UI-VS-API-GAPS.md`](UI-VS-API-GAPS.md) (MCP register) · Lesson [34b](../lessons/34b-lcm-automation-in-action.md) · [93](../lessons/93-workflow-lcm-customization.md) · [49](../lessons/49-email-templates-notifications.md).
