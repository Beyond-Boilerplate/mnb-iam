# Lesson 31 — Leaver & Access Disablement

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 60–90 minutes  
**Prereq:** Lesson 30 (mover / transfer events); `MNB-HR` and target apps aggregated; identity refresh working  

**Lab data:**
- `lab-data/scenarios/leaver/hr-delta-terminate-jordan.csv` → `~/iiq-lab-data/scenarios/leaver/`
- Residual access context: `lab-data/apps/MNB-SAP-Finance.csv`, `lab-data/apps/MNB-AWS-Cloud.csv`, `lab-data/apps/MNB-IT-Access.csv`
- HR baseline: `lab-data/HRApplications.txt` (or `~/iiq-lab-data/HRApplications.txt`)

---

## Learning objectives

You will be able to:

1. Apply an HR leaver delta for `jordan.reed` (`MNB00092`) and propagate it through Account Aggregation and identity refresh.
2. Distinguish **leaver** (`inactive=true` / `status=Terminated` + `terminationDate`) from **leave of absence** (`exceptions=LOA`) on Meridian HR rows.
3. Inventory residual high-risk access (`SAP_FI`, `AWS_ADMIN`, `GL_POST`) still present after HR marks the person inactive.
4. Execute or document disable/revoke steps for directory and privileged links in the lab.
5. Write a Meridian **leaver control standard** covering timing, scope, notifications, and evidence retention.
6. Answer examiner questions about same-day privileged disablement for finance/cloud leavers.

---

## Why this matters

**Business.** A terminated staff accountant with live SAP Finance and AWS Admin keys can move money, alter journals, or destroy cloud evidence. Same-day disablement is a board-level expectation — not a “nice to have” backlog item. Jordan Reed (`jordan.reed`) is Meridian’s flagship Sev-1 leaver for that reason.

**Control / audit.** Examiners ask: *When HR marked the employee terminated, what systems were disabled, by whom, and within what SLA?* Your Aggregate → Refresh → residual inventory → disable → evidence pack is the answer. Control owner: IAM Ops with Finance and Technology app owners for privileged residuals.

---

## Concepts

### Leaver signal vs leave signal

Do not confuse Jordan (terminate) with `sofia.torres` (leave). Wrong playbook = wrong outcome.

| Attribute | Leaver (this lesson) | Leave of absence (Lesson 33) |
| --- | --- | --- |
| `status` | `0` (inactive) | Usually still `1` |
| `terminationDate` | Populated (e.g. `2026-07-26`) | Empty |
| `exceptions` | `false` | `true` |
| Intent | End employment; destroy/disable access path | Temporary freeze; expected return |

### Lab persona — why Jordan is a Sev-1 leaver

| Field | Value |
| --- | --- |
| Identity | `jordan.reed` / `MNB00092` |
| Email | `jordan.reed@meridiannb.com` |
| Manager | `deepa.nair` (`MNB00003`) |
| Job | Staff Accountant (`FIN` / `GL01`) |
| Known entitlements | `ELDAP`, `SAP_FI`, `AWS_ADMIN`, `GL_POST` |

Jordan also embodies the **finance-cloud toxic pair** (`SAP_FI` + `AWS_ADMIN`) from the SoD matrix — Lesson 39 will detect it as policy; this lesson removes the employment signal that makes residual privilege indefensible.

### Disable vs revoke

- **Disable** marks an account link inactive (login blocked; account may still exist for audit/hold).
- **Revoke** removes entitlements/roles from the account.
- HR `inactive=true` alone does **not** disable SAP or AWS — residual inventory is mandatory.

The wrong way: mark HR inactive, skip residual hunt, tell Audit “leavers are automatic.” That is how `AWS_ADMIN` survives termination.

---

## How it works

```text
HR delta (inactive=true / status=Terminated, terminationDate)
        │
        ▼
Account Aggregation task (MNB-HR)
        │
        ▼
Refresh MNB Identities (roles + optional leaver workflow)
        │
        ▼
Identity inactive / terminated flags visible
        │
        ▼
Residual entitlement inventory (SAP / AWS / GL / ELDAP)
        │
        ▼
Disable links / revoke roles / ticket residuals
        │
        ▼
Notify manager (deepa.nair) + evidence pack
```

| Stage | What IIQ does | What you prove |
| --- | --- | --- |
| HR terminate | File row update for `MNB00092` | `inactive=true`, `terminationDate` set |
| Aggregate + refresh | Task Results | Inactive signals on cube |
| Residual inventory | Read Accounts/Entitlements | `SAP_FI`, `AWS_ADMIN`, `GL_POST` disposition |
| Disable / revoke | Manage Accounts / file + agg / LCM | Critical access dead or ticketed |
| Evidence | Screenshots + tickets | Examiner-ready leaver pack |

**IIQ terms:** *Account Aggregation task* pulls HR file changes. *Identity Refresh* re-evaluates attributes, roles, and (if configured) lifecycle events. Do not wait on LCM access-request objects (Lessons 35–38) to stop a terminated finance user.

---

## Before you start

- [ ] IIQ reachable at `http://localhost:8080/identityiq` (homelab URL only as alternate).
- [ ] Logged in as `spadmin` (or equivalent lab admin).
- [ ] Lab files under `~/iiq-lab-data/` including `scenarios/leaver/hr-delta-terminate-jordan.csv`.
- [ ] `MNB-HR` (or your authoritative HR app) aggregates successfully.
- [ ] Prior apps from Applications track present: at least IT inventory / SAP / AWS links for Jordan.
- [ ] Optional: `init-lcm.xml` imported if you want automated leaver lifecycle events — **not required** for file-driven status change in this lesson.
- [ ] Notebook ready for residual inventory and control-standard draft.

---

## Lab procedure

### Task 1 — Inspect the leaver delta before you touch production HR

Read the delta like a change ticket. Mixing Sofia’s leave flags with Jordan’s terminate columns is the classic lab mistake.

1. Open `~/iiq-lab-data/scenarios/leaver/hr-delta-terminate-jordan.csv` (or repo `lab-data/scenarios/leaver/hr-delta-terminate-jordan.csv`).
2. Confirm the row: `userId=MNB00092`, `name=jordan.reed`, `inactive=true`, `exceptions` empty (not LOA), `terminationDate=2026-07-26`, manager `MNB00003`.
3. Open the live HR feed your connector reads (often `~/iiq-lab-data/HRApplications.txt`). Locate Jordan’s current row and note `inactive=false` / `status=Active` before change.

**Expected result:** Delta clearly shows inactive employee with termination date; current HR still shows Jordan active. You know exactly which columns will flip.

**If it fails:** Re-copy `lab-data/scenarios` into `~/iiq-lab-data/` per [README](README.md).

### Task 2 — Apply the terminate delta into the authoritative HR file

Only Jordan’s row changes. Leave Sofia (`exceptions=LOA`) and Samir (already `inactive=true`) alone. Prefer the scenario runner:

```bash
./tools/lab/scripts/scenarios/apply-leaver.sh
```

1. Runner (or hand-edit) updates Jordan’s HR row to match the leaver CSV (do not invent columns). Upsert key is `userId=MNB00092`.
2. Validate column count matches the header (comma count / CSV lint) if editing by hand.
3. Leave other employees unchanged — especially `sofia.torres` (`exceptions=LOA`) and `samir.hassan` (already `inactive=true`).

**Expected result:** Only Jordan’s authoritative row shows `inactive=true` and `terminationDate=2026-07-26`. `exceptions` stays empty (not LOA).

**If it fails:** Restore from the runner `.bak-*` or `lab-data/HRApplications.txt` and re-apply.

### Task 3 — Aggregate HR and refresh identities

Aggregation first — refresh without a successful HR aggregate reads stale status.

1. In IIQ, open **Setup → Tasks** (or equivalent Tasks menu).
2. Run the **Account Aggregation** task for `MNB-HR` (or your HR application name). Wait for success.
3. Run **Refresh MNB Identities** (or your named identity refresh task). Enable options you normally use for attribute sync / role refresh if configured.
4. Open **Identities → Identity Warehouse** (or equivalent). Search `jordan.reed`.

**Expected result:** Identity cube reflects inactive HR signals (`status` / inactive flag / termination date as mapped). Manager still resolves toward `deepa.nair` unless you remapped hierarchy.

**If it fails:** Check aggregation task result for parse errors; confirm file path on the application; re-run aggregation only, then refresh.

### Task 4 — Inventory residual SAP / AWS / GL access

HR inactive ≠ systems disabled. Build the residual table examiners will ask for.

1. On Jordan’s cube, open **Accounts** / **Entitlements** / **Detected Roles** (or equivalent tabs).
2. Build a residual table in your notebook:

| System / entitlement | Still present? | Risk | Action |
| --- | --- | --- | --- |
| `ELDAP` | | medium | Disable directory login |
| `SAP_FI` | | critical | Disable / revoke same day |
| `AWS_ADMIN` | | critical | Disable / revoke same day |
| `GL_POST` | | high | Revoke / ticket Finance |

3. Cross-check source files if links are missing in IIQ: `MNB-SAP-Finance.csv`, `MNB-AWS-Cloud.csv`, `MNB-IT-Access.csv` still list Jordan as `active` until you remediate or re-aggregate after disable.

**Expected result:** You can prove Jordan still holds (or recently held) finance + cloud privilege after HR termination — the classic residual-access finding.

**If it fails:** Re-run Account Aggregation on SAP/AWS/IT apps; confirm correlation from earlier lessons still maps Jordan’s accounts.

### Task 5 — Practice disable / revoke for critical access

Order matters: directory first (blocks interactive login), then cloud Sev-1, then finance ents.

1. Using lab-available actions (Manage Accounts, certification remediation, manual entitlement remove, or CSV “disabled” status + re-aggregate — whichever your lab supports), disable or mark inactive:
   - Directory / `ELDAP` link first (blocks interactive login).
   - `AWS_ADMIN` next (cloud Sev-1).
   - `SAP_FI` and `GL_POST` for Finance.
2. Re-run relevant **Account Aggregation** tasks if you remediated via file.
3. Refresh the identity and confirm links show disabled / entitlements removed or pending.
4. Create a work item or ticket note for anything you could not disable in-lab: owner, system, SLA (same business day for privileged).

**Expected result:** Written residual list with each critical item either disabled, revoked, or ticketed with owner and timestamp. No silent “assume it went away.”

**If it fails:** Document the gap explicitly — examiners prefer known gaps over fake green checks. Stretch later with provisioning connectors.

### Task 6 — Notify manager and draft Meridian leaver standard

1. Note manager `deepa.nair@meridiannb.com` as notification target for finance leavers.
2. Draft a one-page **MNB Leaver Control Standard** with these four parts:
   - **Timing:** HR terminate → directory disable ≤ 1 hour; privileged (`SAP_FI`, `AWS_ADMIN`, wire, core) ≤ same business day / Sev-1.
   - **Scope:** All correlated accounts + orphan hunt for uncorrelated keys (Lesson 19 pattern).
   - **Notifications:** Manager, app owners for critical residuals, Security for privileged leavers.
   - **Evidence retention:** Aggregation/refresh task results, identity screenshots, residual inventory, ticket IDs — retain per bank records policy (lab: keep in training binder).
3. Add one examiner Q&A line: *“How do you know Jordan’s AWS key is dead?”* → point to disable evidence + re-aggregation showing inactive.

**Expected result:** Control standard text you could hand to Internal Audit without rewriting. Jordan case used as the worked example.

**If it fails:** Use the four-part outline above; fill Meridian object names only.

---

## Acceptance criteria

- [ ] **Bank craft exit:** Leaver flow extends `config/Workflow/MNB-Workflow-Leaver.xml` (or documents diff to seed)

- [ ] Leaver CSV applied; Jordan `inactive=true` with `terminationDate` in authoritative HR.
- [ ] Account Aggregation (MNB-HR) and Refresh MNB Identities completed successfully.
- [ ] Identity cube shows inactive/terminated signals for `jordan.reed`.
- [ ] Residual inventory lists `SAP_FI`, `AWS_ADMIN`, `GL_POST` (and `ELDAP`) with disposition.
- [ ] At least one critical disable/revoke path practiced or ticketed with timestamp.
- [ ] Written leaver standard covers timing, scope, notifications, evidence.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Jordan still active after refresh | HR file not updated or wrong path | Confirm connector file path; re-aggregate HR |
| CSV parse / column shift | Extra comma or truncated field | Match header exactly to leaver delta |
| No SAP/AWS on cube | Apps not aggregated or uncorrelated | Aggregate target apps; fix correlation |
| Confused with Sofia | Mixing `exceptions` and `status` | Sofia stays leave; Jordan is terminate |
| LCM event never fired | `init-lcm.xml` / event not configured | File status change is enough for this lesson |

---

## Training binder evidence

1. Screenshot of leaver CSV row for `MNB00092`.
2. Task result success for Aggregate MNB-HR and Refresh MNB Identities.
3. Identity cube screenshot showing inactive/terminated attributes.
4. Residual entitlement table (SAP / AWS / GL) with actions.
5. Disable/revoke or ticket evidence with timestamps.
6. Final **MNB Leaver Control Standard** paragraph set.

---

## Knowledge check

1. Which HR attributes define a Meridian **leaver** in this lab versus leave of absence?
2. Why is `jordan.reed` treated as a Sev-1 leaver compared to a teller with only `ELDAP`?
3. Name the four required parts of the Meridian leaver control standard.
4. What runs first after editing HR: Account Aggregation or identity Refresh?
5. Who is Jordan’s manager for notification purposes?
6. Does HR `inactive=true` automatically remove `AWS_ADMIN`?

### Answers

1. Leaver: `inactive=true` and populated `terminationDate` with `exceptions empty (not LOA)`. Leave: `exceptions=LOA`, typically still active employment status.
2. Holds critical finance (`SAP_FI`, `GL_POST`) plus cloud admin (`AWS_ADMIN`) — material residual risk after exit.
3. Timing, scope, notifications, evidence retention.
4. Account Aggregation task for HR, then Refresh MNB Identities.
5. `deepa.nair` (`MNB00003`) / `deepa.nair@meridiannb.com`.
6. No — residual inventory and explicit disable/revoke are required.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “leaver lifecycle” and “account disable provisioning.”
- [SailPoint Community](https://community.sailpoint.com/) — search “termination residual access” for common post-leaver findings.
- [NIST SP 800-53 AC-2 — Account Management](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — disablement and removal of accounts when employment ends.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search information security / access controls for terminated-user expectations.
- [ISACA — Access Management and SOX ITGC primers](https://www.isaca.org/) — search “user access management” and “termination controls” for evidence framing.

---

## Stretch lab

1. Re-check `samir.hassan` (`inactive=true`) for residual `DWRP` / `SAP_FI` / `ODS` as a backlog defect — compare disabled flags in `MNB-IT-Access.csv`.
2. If LCM is active, configure or inspect a leaver lifecycle event on `status` change and capture the workflow name in the binder.
3. Draft a Sev-1 communications template (Security + Finance + Technology) for privileged leavers.

---

## Summary

- You terminated `jordan.reed` via the official leaver HR delta and refreshed identity state.
- You inventoried residual SAP/AWS/GL privilege that HR status alone does not remove.
- You practiced disable/revoke discipline and wrote Meridian’s leaver control standard for audit.

---

**Previous:** [Lesson 30 — Mover / Transfer Events](30-mover-transfers.md)  
**Next:** [Lesson 32 — Contractor & Contingent Worker Lifecycle](32-contractor-lifecycle.md)
