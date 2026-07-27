# Lesson 53 — IQService Architecture

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors |
| **Time** | 60–90 minutes |
| **Prereq** | Lesson 52; AD selected as Active Directory - Direct |
| **Lab data** | `~/iiq-lab-data/connectors/ad/iqservice-checklist.md` |

## Learning objectives

You will be able to:

- Explain why Active Directory Direct depends on Windows IQService
- Sketch Meridian’s IQService placement (near DCs, TLS, service account)
- Complete the enterprise IQService checklist without a live domain
- Document SPN/cert and least-privilege service account requirements
- Separate IIQ server duties from IQService host duties

## Why this matters

IIQ on Linux/containers cannot natively perform many Windows/AD operations. Meridian’s Corporate AD provisioning (password, enable/disable, some Exchange) flows through **IQService** on a Windows host near domain controllers. Wrong placement or cleartext IQService is a finding.

**Control / audit:** Network diagrams and IQService TLS evidence are examiner artifacts. “We configured the AD app” without IQService design is incomplete.

## Concepts

| Component | Role |
| --- | --- |
| IdentityIQ | Orchestrates plans, stores Application config |
| IQService | Windows service executing AD/Windows connector ops |
| Domain controller / GC | Directory source of truth for accounts/groups |
| Service account | Least-privilege AD account used by IQService / connector |

```text
  IIQ (Linux/container)
        |  TLS to IQService
        v
  IQService (Windows, near DCs)
        |
        v
  Domain Controllers / GC
        |
        v
  AD users, groups, (optional) Exchange
```

**Meridian design rules:**

- Install IQService close to DCs (latency + site affinity).
- Enable TLS; document cert lifecycle.
- Do not run IQService as Domain Admin—document least privilege.
- One lab checklist covers forest/domain, OUs, groups, Exchange, password interceptor scope.

## Before you start

- [ ] `~/iiq-lab-data/connectors/ad/iqservice-checklist.md` present
- [ ] Lesson 52 AD decision record available
- [ ] Network sketch paper or draw.io ready
- [ ] No requirement for live DC this lesson

## Lab procedure

### Task 1 — Read the Meridian IQService checklist

1. Open:

```bash
cat ~/iiq-lab-data/connectors/ad/iqservice-checklist.md
```

2. Check every box conceptually (write Y/N/TBD beside each line in your notebook)—do not invent a live install.
3. Note the explicit lab-without-live-AD sentence at the bottom of the checklist.

**Expected result:** All checklist items transcribed with Y/N/TBD; TBD for live DC/IQService is acceptable.

**If it fails:** Copy from `lab-data/connectors/ad/iqservice-checklist.md`.

### Task 2 — Draw Meridian network placement

1. Draw ASCII or diagram:

```text
  [IIQ pods / VM :8080]
        |
     TLS :5050 (example port—use your build’s port)
        |
  [Windows IQService — Meridian site DC adjacent]
        |
  [DC / GC — meridiannb.com]
```

2. Label: forest/domain name `meridiannb.com` (lab), employee OU vs contractor OU (TBD names OK).
3. Mark firewall allowlist IIQ→IQService only; no IIQ→DC LDAP required for Direct path when IQService proxies ops (document your build’s actual traffic).

**Expected result:** Diagram saved as `~/iiq-lab-data/connectors/ad/MNB-iqservice-network-53.txt`.

### Task 3 — Service account & cert worksheet

1. Create worksheet fields:

| Item | Meridian lab value |
| --- | --- |
| IQService hostname | `mnb-iqsvc-lab` (fictional OK) |
| Service account | `svc-iiq-iqservice` (fictional) |
| Not Domain Admin | Confirmed design |
| TLS cert CN | matches hostname |
| SPN plan | Documented TBD/owner |
| Password rotation owner | Windows / IAM jointly |

2. Write: “Production values come from Secrets Manager; never commit passwords.”

**Expected result:** Worksheet complete; no real secrets stored in repo.

### Task 4 — Lab without live target — Application dependency note

1. Open (or draft) Application shell name `MNB-ActiveDirectory` in notes—do not need live Test Connection.
2. Record Application field intents: IQService host, domain, forest, GC usage.
3. Paste checklist reference path into Application design note.
4. Confirm Lesson 56 will build the AD Direct app shell against this design.

**Expected result:** Design note linking Application → IQService hostname → checklist.

**If it fails:** Keep everything in `ad/` folder files; Application UI can wait until Lesson 56.

### Task 5 — Failure modes table

1. Fill:

| Failure | Symptom | First check |
| --- | --- | --- |
| IQService down | Provision timeouts | Windows service status |
| TLS mismatch | Handshake errors | Cert CN / trust store |
| Wrong site IQService | Slow / intermittent | Place near DC site |
| Over-privileged account | Audit finding | Reduce rights; retest |

2. Add this table to the binder.

**Expected result:** Four-row ops table ready for runbooks.

### Task 6 — CHANGELOG

1. Log: “Lesson 53: IQService architecture worksheet + network sketch for Meridian AD.”

**Expected result:** CHANGELOG entry present.

## Acceptance criteria

- [ ] Checklist reviewed with Y/N/TBD
- [ ] Network sketch file created under `connectors/ad/`
- [ ] Service account / TLS worksheet without secrets
- [ ] Lab-without-live-target AD dependency note written
- [ ] Failure modes table + CHANGELOG done

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Checklist missing | Path | Copy `lab-data/connectors/ad/` |
| Confused with LDAP connector | Wrong type | Meridian AD uses AD Direct + IQService |
| Want to install IQService now | Scope | Optional; design evidence is enough here |
| Port unknown | Build variance | Document “confirm in install guide”; use placeholder |
| Secrets in notebook | Hygiene | Redact; use fictional lab names only |

## Training binder evidence

- Completed checklist with Y/N/TBD
- `MNB-iqservice-network-53.txt`
- Service account / TLS worksheet (redacted)

**Examiner question:** “Where does IdentityIQ terminate TLS to perform AD password reset, and who owns that Windows host?”

## Knowledge check

1. Why does Meridian need IQService for AD Direct?
2. Where should IQService be placed relative to DCs?
3. Should the IQService account be Domain Admin?
4. Name two checklist items beyond “install IQService.”
5. Can this lesson complete without a live domain controller?

### Answers

1. Many AD/Windows operations (password, enable, Exchange-related) execute via the Windows IQService, not directly from the IIQ JVM alone.
2. On a Windows host near the domain controllers (site affinity / low latency).
3. No—use least privilege and document rights.
4. Examples: TLS enabled, forest/domain config, OU search DNs, group scope, Exchange yes/no, correlation attributes, test plan.
5. Yes—checklist, network sketch, and worksheets satisfy lab-without-live-target.

## Stretch lab

- Read vendor IQService install PDF (external) and add Meridian-specific firewall ports to the network file.
- Draft a monitoring check: IQService service up + IIQ Test Connection scheduled weekly.
- Compare IQService vs future Cloud Gateway patterns (Lesson 88) in one paragraph.

## Summary

- AD Direct at Meridian implies IQService architecture, not only an Application form.
- TLS, placement, and least-privilege accounts are control evidence.
- Live DC optional; checklist completion is mandatory.

---

**Previous:** [Lesson 52 — Connector Selection for Meridian](52-connector-selection-for-meridian.md)  
**Next:** [Lesson 54 — Aggregation Patterns Advanced](54-aggregation-patterns-advanced.md)
