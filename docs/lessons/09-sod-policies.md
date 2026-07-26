# Lesson 09 — SoD Policies for Banking

**Level:** Intermediate  
**Prereq:** Lessons 04–08  
**Meridian story:** Regulators expect Separation of Duties. Nobody who can *initiate* a payment-like function should also *approve* it—or hold toxic admin combos like `SAP` + `AWS` without scrutiny.

---

## Story

You will create an **SoD policy** that flags a toxic combination of entitlements (lab stand-in for real payment duties). Then run policy scanning during refresh and inspect violations.

Suggested lab toxic pair (adjust to entitlements you actually have):

| Policy | Entitlement A | Entitlement B | Why (fictitious) |
| --- | --- | --- | --- |
| `MNB-SOD-Finance-Cloud` | `SAP` | `AWS` | ERP finance duties + cloud admin bypass risk |
| `MNB-SOD-Digital` | `IBSI` | `Ecom` | Dual control on digital banking changes |

---

## How it works

Policies evaluate identities (or accounts) against rules. On violation, IIQ can:

- Show a policy violation on the identity  
- Block access requests  
- Require mitigating control / approval  
- Appear in reports for auditors

SoD is usually **preventive** (block request) and/or **detective** (flag existing access).

---

## Lesson goals

- [ ] Create at least one Entitlement SoD policy
- [ ] Demonstrate a violating identity (use existing data or grant both sides)
- [ ] Run refresh/policy check and view the violation
- [ ] Decide Meridian’s response: revoke, mitigate, or exception

---

## Tasks

### Task 1 — Find a candidate violator

From `EmployeeData.txt`, look for users with multiple high-risk `itAccess` values. If none have your toxic pair, temporarily request/add the second entitlement on a test user (Lesson 08).

### Task 2 — Create the policy

1. Policies → create **Separation of Duties** / Entitlement SOD policy.  
2. Name: `MNB-SOD-Finance-Cloud` (or your pair).  
3. Left set / Right set: choose the two entitlements.  
4. Set violation owner (security team / `spadmin`).  
5. Save / enable.

### Task 3 — Evaluate

1. Run `Refresh MNB Identities` with policy checking enabled.  
2. Open the violating identity → Policies / Violations.  
3. Open policy violation work items if created.

### Task 4 — Remediate in lab

Pick one:

- Remove one entitlement (preferred for true toxic access)  
- Document a **compensating control** exception (time-boxed)

Re-refresh and confirm violation clears or remains as accepted exception (depending on configuration).

### Task 5 — Bank control write-up

Write a half-page control description suitable for an ITRC / audit binder:

- Policy purpose  
- How detected  
- How prevented on requests  
- Who owns exceptions  

---

## Tips & tricks

- SoD design starts in **business workshops**, not in the IIQ UI. Interview finance ops before encoding.  
- Too many SOD rules creates alert fatigue—start with top 5 banking risks.  
- Always test both: existing violators (detective) and new requests (preventive).  
- Name policies with business language, not only technical entitlement codes.

---

## Checkpoint

1. What is SoD in one sentence?  
2. Preventive vs detective policy use?  
3. Why is `SAP` + `AWS` a reasonable lab stand-in for banking risk?

---

## Stretch

Add a policy that flags inactive (`status=0`) identities that still have any `MNB-IT-Access` entitlements—leaver hygiene control.

**Next:** [Lesson 10 — Manager access certifications](10-access-certifications.md)
