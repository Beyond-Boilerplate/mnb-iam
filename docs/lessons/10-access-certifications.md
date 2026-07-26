# Lesson 10 — Manager Access Certifications

**Level:** Intermediate → Advanced  
**Prereq:** Lessons 05–09  
**Meridian story:** Quarterly access reviews. Managers must attest that their people still need the access they hold. Your `email.txt` sample shows what that communication looks like.

---

## Story

You will launch a **Manager Certification** for a slice of Meridian users, complete decisions (approve / revoke / delegate), and observe notifications conceptually against `email.txt`.

---

## How it works

```text
Certification campaign scheduled
  → Work items created for certifiers (managers)
  → Email notifications sent
  → Certifier decides: Maintain / Revoke / Delegate
  → Revokes generate provisioning / work items
  → Campaign signs off → audit evidence retained
```

Certification types you will hear about:

| Type | Certifier |
| --- | --- |
| Manager | People managers review direct reports’ access |
| Application owner | App owners review accounts on their app |
| Entitlement owner | Owners review who has a sensitive group |
| Advanced / Targeted | Custom populations and inclusions |

---

## Lesson goals

- [ ] Create and generate a Manager certification for Meridian
- [ ] Complete at least one certify decision and one revoke decision
- [ ] Try a delegation (compare to `email.txt`)
- [ ] Understand where campaign evidence lives after completion

---

## Tasks

### Task 1 — Read the sample mailbox

Open repo `email.txt`. Note subjects like:

- `New access certification: Manager Access Review for george bush`
- `Delegation Completed by anita malla`

Keep that UX in mind while configuring.

### Task 2 — Create certification definition

1. Certifications → schedule / create **Manager** certification.  
2. Name: `MNB Manager Access Review — Lab`.  
3. Include applications / entitlements from `MNB-IT-Access` (limit scope so the campaign is small).  
4. Choose a population that has managers populated (Lesson 03).  
5. Set short deadlines (lab: 7 days).  
6. Save.

### Task 3 — Generate / stage the campaign

1. Run the certification generation / start process.  
2. Confirm work items appear for one or more managers.  
3. Open a certification work item.

### Task 4 — Decide access

For one report:

1. **Maintain** a low-risk entitlement (`ELDAP` / `ODS`).  
2. **Revoke** something questionable.  
3. Save / sign decisions per UI rules.

### Task 5 — Delegation drill

1. Delegate a portion to another user (like Anita in the sample mail).  
2. Complete as the delegate.  
3. Return / review as the original manager if required.

### Task 6 — Close the loop

1. Finish required items until the campaign can complete / phase forward.  
2. If revokes created provisioning requests or work items, process them.  
3. Find completed certification records for audit playback.

---

## Tips & tricks

- Start **tiny** (one department). Huge first campaigns overwhelm managers and you.  
- Bad manager data = undeliverable certifications. Fix HR manager links first.  
- Bulk “approve all” trains managers to rubber-stamp—discourage it in real banks.  
- Email in lab may not send unless SMTP is configured; work items still teach the process. Configure SMTP later if you want mailbox realism.

---

## Checkpoint

1. Who is the certifier in a manager access review?  
2. What happens when access is revoked in a certification?  
3. Why does delegation show up in email samples?

---

## Stretch

Create an **Application Owner** certification for `MNB-IT-Access` owned by a security identity. Compare decision quality vs manager certification.

**Next:** [Lesson 11 — Provisioning & troubleshooting](11-provisioning-and-troubleshooting.md)
