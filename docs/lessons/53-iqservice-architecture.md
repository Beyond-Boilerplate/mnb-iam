# Lesson 53 — IQService Architecture

**Level:** Intermediate  
**Track:** Connectors  
**Time:** 90–120 min  
**Prereq:** Lesson 52 — Connector Selection for Meridian; Corporate AD selected as Active Directory - Direct  

**Lab data:**
- Repo: `lab-data/connectors/ad/iqservice-checklist.md`
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Corporate AD row)
- Homelab copy: `~/iiq-lab-data/connectors/ad/`

---

## Learning objectives

You will be able to:

- Explain why Active Directory Direct depends on a Windows **IQService** agent and what the IIQ JVM cannot do alone
- Sketch Meridian’s IQService placement (near DCs, TLS, ports, forest/domain trust assumptions)
- Complete the enterprise IQService install/config worksheet and checklist without a live domain
- Document SPN/cert, least-privilege service account, and OU/group/Exchange scope decisions
- Separate IIQ server duties from IQService host duties for runbooks and examiner questions
- Produce failure-mode and monitoring notes ready for Lesson 56 AD connector build

---

## Why this matters

**Business.** IdentityIQ often runs on Linux or containers. Meridian’s Corporate AD provisioning — password set, enable/disable, many Exchange mailbox operations — does **not** complete inside the IIQ JVM alone. Those operations execute on a Windows host running **IQService**, talking to domain controllers near the AD site. When IQService was mis-placed across a WAN last year, password resets for `amelia.brooks` timed out during a Monday morning helpdesk surge, and the business blamed “SailPoint” instead of network design.

**Control / audit.** Network diagrams, TLS evidence, and least-privilege service-account documentation are examiner artifacts. “We configured the AD application” without IQService architecture is incomplete. The OCC-style question is: *Where does IdentityIQ terminate TLS to perform AD password reset, and who owns that Windows host?*

---

## Concepts

### Why a Windows agent exists

The Active Directory - Direct connector is designed so that **directory-mutating and Windows-security operations** run where Windows APIs and AD admin protocols are native. IQService is that agent:

| Concern | Without IQService (naive) | With IQService (Meridian design) |
| --- | --- | --- |
| Password set / change | IIQ Linux process tries remote Windows crypto/RPC — fragile or unsupported for Meridian’s pattern | IQService executes password ops near the DC |
| Enable / disable | May partially work via LDAP modify depending on build/path — not the enterprise pattern Meridian standardizes | IQService path for consistent ENABLE ops |
| Exchange / mailbox | Needs Windows/Exchange management surface | IQService host in scope when Exchange = yes |
| Network blast radius | IIQ tier opened wide to every DC | IIQ → IQService (TLS) only; IQService → DC |

**Real-life Meridian example.** A contractor proposed “just open LDAPS from the IIQ pod CIDR to every DC in `meridiannb.com`.” Security rejected it: the IIQ tier would hold broad directory reach, and password operations still needed a Windows execution host. The approved pattern: **narrow allowlist IIQ → IQService**, IQService adjacent to DCs, TLS on the IQService listener, service account least privilege — not Domain Admin.

### TLS, ports, and trust

| Item | What to decide | Meridian lab default (document, then confirm in install guide) |
| --- | --- | --- |
| **Listener TLS** | IQService must not run cleartext in production | TLS enabled; cert CN/SAN matches hostname |
| **Port** | Build-specific — never hardcode without checking | Common lab placeholder `:5050` — **confirm in your IQService install guide** |
| **Trust** | IIQ must trust the IQService cert (or private CA) | Import issuing CA into IIQ trust store |
| **Forest / domain** | Single forest vs multi-domain | Lab: `meridiannb.com`; production: document GC usage |
| **Forest trust** | Cross-forest accounts? | If Meridian acquires a bank with a separate forest, IQService placement and trust path become a project — do not assume one IQService sees everything |

Cleartext IQService on the corporate network is a finding. Treat the IQService credential and TLS private key like domain-admin-adjacent secrets: vault them, rotate them, never commit them.

### Least privilege and the service account

The IQService Windows service (and the AD account used for connector operations) must be **documented least privilege**, not Domain Admin:

- Create/modify/disable users in scoped OUs (employees vs contractors)
- Manage membership of security groups in scope
- Password reset rights only where helpdesk/JML requires them
- Exchange rights **only if** mailbox provisioning is in scope

**Wrong way:** “Give it Domain Admin so Test Connection works.” That passes a lab demo and fails every bank audit. Record the rights model in the worksheet even when the lab has no live DC.

### What the Meridian checklist covers

The repo checklist (`ad/iqservice-checklist.md`) is the enterprise punch list:

- Domain-join / install account with least privilege documented
- IQService on Windows host near DCs, TLS enabled
- Service account + SPN / cert plan
- Application type: **Active Directory - Direct**
- Forest/domain; GC usage
- Account OU search DNs (employees vs contractors)
- Group aggregation scope (security groups only?)
- Exchange / mailbox required? Password Interceptor in scope?
- Provisioning policies: create, enable, disable, move OU on leaver
- Correlation: `sAMAccountName` ↔ `userName`, `employeeID` ↔ `employeeId`
- Test plan: aggregate → correlate → create → disable → delete (lab only)

---

## How it works

```text
  IdentityIQ (Linux / container)
        │  TLS to IQService host:port
        │  (Application: IQService host, domain, forest, creds)
        ▼
  IQService (Windows service, DC-adjacent site)
        │  AD / Windows APIs
        ▼
  Domain Controllers / Global Catalog
        │
        ├── Users (employee OU, contractor OU)
        ├── Security groups
        └── Optional: Exchange mailbox ops
```

| Component | Duty | Not responsible for |
| --- | --- | --- |
| **IdentityIQ** | Orchestrates plans, stores Application config, schedules aggregation, stores Task Results | Native Windows password API execution |
| **IQService** | Executes AD/Windows connector operations securely near DCs | Being the identity source of truth |
| **DC / GC** | Directory source of truth for accounts/groups | Running IIQ workflows |
| **Service account** | Authenticated principal for directory ops | Interactive human login / Domain Admin |

Traffic intent for Meridian (document actual ports from your build):

```text
  [IIQ pods / VM :8080]
        |
     TLS :5050 (example — confirm in install guide)
        |
  [Windows IQService — site-adjacent to DCs]
        |
  [DC / GC — meridiannb.com]
```

Firewall story examiners like: **allowlist IIQ → IQService only**; do not open IIQ → every DC for the Direct+IQService pattern unless your build’s documentation explicitly requires additional LDAP paths — and if it does, document them.

---

## Real-world setup (outside IIQ)

This is the install/config worksheet a production engineer executes. Complete it on paper even when the lab has no DC — Lesson 56 consumes these decisions.

### Step 1 — Place the Windows host

1. Choose a Windows Server in the **same AD site** (or low-latency adjacency) as the DCs that hold Meridian users.
2. Hostname plan: e.g. `mnb-iqsvc-01.meridiannb.com` (lab fictional: `mnb-iqsvc-lab`).
3. Confirm patching, monitoring, and backup ownership with Windows ops — IQService is a production dependency, not a “lab toy.”

### Step 2 — Install IQService with TLS

1. Obtain the IQService installer matching your IdentityIQ version from SailPoint packaging (version skew causes subtle failures).
2. Install the Windows service; enable **TLS**; generate or request a certificate whose CN/SAN matches the hostname clients will use.
3. Record listener port from the install guide / config (do not assume).
4. Confirm the service starts as a dedicated Windows service account (not a personal admin login).

### Step 3 — Service account, SPN, and rights

1. Create AD account `svc-iiq-iqservice` (name per Meridian standard) in a protected OU.
2. Document rights: OU-scoped user management, group management, password reset as required — **not Domain Admin**.
3. SPN / cert plan: record who registers SPNs if Kerberos mutual auth patterns apply in your build; owner = Windows + IAM jointly.
4. Vault the password; set rotation on the joint IAM/Windows calendar. Never store secrets in git or binders.

### Step 4 — Forest, domain, OU, and Exchange decisions

1. Forest/domain: `meridiannb.com` (lab); decide Global Catalog usage for multi-domain forests.
2. Employee OU vs contractor OU search DNs — write the DNs even if TBD suffixes remain.
3. Group scope: security groups only? Exclude distribution lists?
4. Exchange / mailbox provisioning: **yes/no**. If no, do not grant Exchange rights “just in case.”
5. Password Interceptor: in scope or not? (Usually a separate design — note TBD with owner.)

### Step 5 — Wire IIQ Application fields (design now, build in Lesson 56)

1. Application type: **Active Directory - Direct**.
2. IQService hostname, port, TLS.
3. Domain/forest, aggregation search DNs, correlation attributes.
4. Test Connection only when live IQService exists — this lesson accepts design-only.

### Step 6 — Record owners and evidence

| Item | Owner |
| --- | --- |
| Windows host + patching | Windows ops |
| IQService service health | Windows ops + IAM |
| AD service account rights | IAM + AD admins |
| Application object `MNB-ActiveDirectory` | IAM (`helen.ross`) |
| TLS cert lifecycle | PKI / Windows |

---

## Before you start

- [ ] `~/iiq-lab-data/connectors/ad/iqservice-checklist.md` present (copy from repo if needed)
- [ ] Lesson 52 AD decision record available
- [ ] Network sketch paper or text file ready
- [ ] No requirement for live DC this lesson — lab-without-live-AD is valid
- [ ] No real domain passwords written into notebooks

---

## Lab procedure

### Task 1 — Read the Meridian IQService checklist

The checklist is Meridian’s definition of “done” for AD Direct readiness. You are not installing yet — you are scoring honesty.

1. Open:

```bash
cat ~/iiq-lab-data/connectors/ad/iqservice-checklist.md
```

2. Beside each line in your notebook, write **Y / N / TBD** — do not invent a live install.
3. Note the explicit lab-without-live-AD sentence at the bottom of the checklist; that sentence authorizes design-only completion.

**Expected result:** All checklist items transcribed with Y/N/TBD; TBD for live DC/IQService is acceptable.

**If it fails:** Copy from `lab-data/connectors/ad/iqservice-checklist.md`.

### Task 2 — Draw Meridian network placement

Examiners ask for the diagram before they ask for the Application screenshot.

1. Create `~/iiq-lab-data/connectors/ad/MNB-iqservice-network-53.txt` with:

```text
  [IIQ pods / VM :8080]
        |
     TLS :5050 (example port — confirm in install guide)
        |
  [Windows IQService — Meridian site DC adjacent]
        |
  [DC / GC — meridiannb.com]
```

2. Label forest/domain `meridiannb.com`; employee OU vs contractor OU (TBD names OK).
3. Mark firewall allowlist **IIQ → IQService only**; note any additional LDAP paths only if your build requires them.
4. Add a one-line forest-trust note: “Single forest assumed; cross-forest = separate design.”

**Expected result:** Network file saved under `connectors/ad/` with TLS, port placeholder, OU labels, allowlist note.

### Task 3 — Service account & cert worksheet

Secrets hygiene matters as much as the architecture.

1. Create worksheet fields (fictional lab values OK):

| Item | Meridian lab value |
| --- | --- |
| IQService hostname | `mnb-iqsvc-lab` |
| Listener port | TBD — confirm in install guide (example 5050) |
| TLS enabled | YES (design) |
| TLS cert CN/SAN | matches hostname |
| Service account | `svc-iiq-iqservice` |
| Not Domain Admin | Confirmed design |
| SPN plan | Documented TBD / owner Windows+IAM |
| Password rotation owner | Windows / IAM jointly |
| Secrets location | Vault — never repo |

2. Write explicitly: “Production values come from Secrets Manager; never commit passwords.”

**Expected result:** Worksheet complete; no real secrets stored in repo or binder photos.

### Task 4 — Install/config worksheet (real-world setup on paper)

Turn Steps 1–6 into a filled install card you could hand Windows ops.

1. Create `~/iiq-lab-data/connectors/ad/MNB-iqservice-install-worksheet-53.md` covering:
   - Host placement / AD site
   - IIQ version ↔ IQService version match
   - TLS + port
   - Service account + rights summary (bullet list, not Domain Admin)
   - Forest/domain/GC
   - OU search DNs (employee / contractor)
   - Exchange yes/no; Password Interceptor yes/no/TBD
   - Monitoring: service up + weekly Test Connection when live
2. Mark each row Installed / Designed / TBD.

**Expected result:** Install worksheet file with Designed/TBD acceptable for lab-without-live-AD.

### Task 5 — Lab without live target — Application dependency note

Lesson 56 builds `MNB-ActiveDirectory`; this lesson locks the dependencies.

1. Draft Application shell notes for `MNB-ActiveDirectory` — do not need live Test Connection.
2. Record field intents: IQService host, domain, forest, GC usage, OU DNs, correlation (`sAMAccountName` ↔ `userName`, `employeeID` ↔ `employeeId`).
3. Paste checklist + install worksheet paths into the design note.
4. Confirm create-identities will be **OFF** (AD is a target).

**Expected result:** Design note linking Application → IQService hostname → checklist → install worksheet.

**If it fails:** Keep everything in `ad/` folder files; Application UI can wait until Lesson 56.

### Task 6 — Failure modes and monitoring table

Ops will page someone at 02:00 — give them a first-check table.

1. Fill and save into the binder / install worksheet:

| Failure | Symptom | First check |
| --- | --- | --- |
| IQService down | Provision timeouts; Test Connection fails | Windows service status; host up |
| TLS mismatch | Handshake errors | Cert CN/SAN; IIQ trust store |
| Wrong site IQService | Slow / intermittent password ops | Place near DC site; latency |
| Over-privileged account | Audit finding | Reduce rights; retest |
| Port blocked | Connection refused / timeout | Firewall allowlist IIQ → IQService |
| Version skew | Odd RPC / connector errors | Match IQService build to IIQ version |

2. Add monitoring intent: IQService service up alert + scheduled weekly Test Connection when live.

**Expected result:** Six-row ops table + monitoring note ready for runbooks.

### Task 7 — Examiner drill and CHANGELOG

1. Answer in writing: *“Where does IdentityIQ terminate TLS to perform AD password reset, and who owns that Windows host?”*
2. Answer: TLS terminates at IQService on the Windows host (`mnb-iqsvc-lab` / prod name); Windows ops owns the host; IAM owns the Application and jointly owns the service account.
3. CHANGELOG: “Lesson 53: IQService architecture worksheet + network sketch + install card for Meridian AD.”

**Expected result:** Written examiner answer + CHANGELOG entry.

---

## Acceptance criteria

- [ ] Checklist reviewed with Y/N/TBD
- [ ] Network sketch file created under `connectors/ad/`
- [ ] Service account / TLS worksheet without secrets
- [ ] Install/config worksheet completed (Designed/TBD OK)
- [ ] Lab-without-live-target AD dependency note written
- [ ] Failure modes table + monitoring note + CHANGELOG done

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Checklist missing | Path | Copy `lab-data/connectors/ad/` |
| Confused with LDAP connector | Wrong type | Meridian AD uses AD Direct + IQService |
| Want to install IQService now | Scope | Optional; design evidence is enough here |
| Port unknown | Build variance | Document “confirm in install guide”; use placeholder |
| Secrets in notebook | Hygiene | Redact; use fictional lab names only |
| “Open IIQ to all DCs” | Wrong blast radius | Prefer IIQ → IQService allowlist |

---

## Training binder evidence

- Completed checklist with Y/N/TBD
- `MNB-iqservice-network-53.txt`
- `MNB-iqservice-install-worksheet-53.md`
- Service account / TLS worksheet (redacted)
- Examiner answer paragraph

**Examiner question:** “Where does IdentityIQ terminate TLS to perform AD password reset, and who owns that Windows host?”

---

## Knowledge check

1. Why does Meridian need IQService for AD Direct?
2. Where should IQService be placed relative to DCs?
3. Should the IQService account be Domain Admin?
4. Name three checklist items beyond “install IQService.”
5. Can this lesson complete without a live domain controller?
6. What firewall story should Meridian document for the Direct + IQService pattern?

### Answers

1. Many AD/Windows operations (password, enable, Exchange-related) execute via the Windows IQService, not solely inside the IIQ JVM.
2. On a Windows host near the domain controllers (site affinity / low latency).
3. No — use least privilege and document rights.
4. Examples: TLS enabled, forest/domain config, OU search DNs, group scope, Exchange yes/no, correlation attributes, test plan, SPN/cert plan.
5. Yes — checklist, network sketch, install worksheet, and dependency notes satisfy lab-without-live-target.
6. Allowlist IIQ → IQService (TLS); avoid opening IIQ broadly to every DC unless the build explicitly requires and documents additional paths.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “IQService” and “Active Directory connector” for your version’s install guide, TLS configuration, and supported operations.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “IQService TLS” and “IQService service account permissions” for field-hardened least-privilege lists.
- [Microsoft: Least privilege and Active Directory](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/implementing-least-privilege-administrative-models) — why Domain Admin for connector accounts fails audits.
- [NIST SP 800-52 Rev. 2 — TLS guidelines](https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final) — baseline expectations for TLS on administrative service endpoints like IQService.
- [CIS Benchmarks for Microsoft Windows Server](https://www.cisecurity.org/cis-benchmarks) — hardening expectations for the Windows host that runs IQService.

---

## Stretch lab

- Read the vendor IQService install PDF for your IIQ version and replace the port placeholder with the documented default; add Meridian-specific firewall ports to the network file.
- Draft a monitoring check: IQService service up + IIQ Test Connection scheduled weekly; name the on-call (`helen.ross` / Windows ops).
- Compare IQService vs future Cloud Gateway patterns (Lesson 88) in one paragraph: what still requires a Windows agent?

---

## Summary

- AD Direct at Meridian implies IQService architecture — placement, TLS, and least privilege — not only an Application form.
- Real-world setup is an install/config worksheet Windows ops and IAM share before Lesson 56 builds the app.
- Live DC optional; checklist + network + install card + failure modes are mandatory evidence.

---

**Previous:** [Lesson 52 — Connector Selection for Meridian](52-connector-selection-for-meridian.md)  
**Next:** [Lesson 54 — Aggregation Patterns Advanced](54-aggregation-patterns-advanced.md)
