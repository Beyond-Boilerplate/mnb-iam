# Lesson 252 — Entra-Shaped Lifecycle (Mock Graph/SCIM)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~75 minutes  
**Prereq:** Lessons 210–212, 251  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 59 (Azure / Entra connector narrative)

> **Why:** You need an Entra-shaped account API for IIQ labs without a Microsoft tenant tax — but confusing “account disabled in the directory mock” with “SSO actually dead” is exactly the silent failure that breaks leaver proof.

## What this is

**`MNB-EntraID`** is a SCIM 2.0 application pointing at **connector-mock** Entra-shaped APIs — not a real Entra tenant.

| Surface | URL (from your Mac) | Role |
| --- | --- | --- |
| Graph-shaped users | `http://localhost:8091/entra/v1/users` | Inventory shaped like Graph |
| SCIM Users | `http://localhost:8091/entra/scim/v2/Users` | What IIQ aggregates |
| SCIM PATCH | `PATCH …/entra/scim/v2/Users/{id}` | Disable / group metadata on the mock |
| IIQ app | `MNB-EntraID` | Host `http://connector-mock:8091/entra/scim/v2` |

**Browser SSO still uses Keycloak.** This app exists so aggregation, disable, and group metadata look like cloud-directory work inside IIQ. Login proofs after disable still require Keycloak changes.

Nothing for this drill’s lifecycle subject is assumed. You will:

1. Curl Graph + SCIM (see fixtures, then your disposable account)  
2. Seed disposable **`lab.entra1`** into the Entra mock + create the IIQ cube  
3. Import/verify **`MNB-EntraID`**, Test Connection, aggregate, correlate  
4. PATCH `active:false` on the mock → re-aggregate → IIQ inactive  
5. Prove Employee Portal SSO for `lab.entra1` **still works** until Keycloak is touched  
6. Write the honest split in evidence  

> **Watch out:** PATCHing the mock does **not** kill Keycloak SSO. If you skip the Portal proof, you will ship a false leaver story.

## Know these

```text
curl Graph + SCIM inventory
  → Create lab.entra1 (HCM + IIQ cube + Keycloak for SSO proof)
  → Inject entra-lab.entra1 into connector-mock Entra state + restart mock
  → Verify-or-import MNB-EntraID → Test Connection → Aggregate
  → Correlate account to lab.entra1
  → PATCH active:false on mock → re-agg → IIQ shows inactive
  → Portal SSO as lab.entra1 still succeeds
  → Evidence note: mock = IIQ lifecycle; Keycloak = login
```

| System | Owns | Does **not** own |
| --- | --- | --- |
| `MNB-EntraID` (connector-mock) | IIQ aggregation, disable flag, group metadata | Browser login cookies |
| Keycloak (`meridian`) | Actual SSO / password for Portal / Workstation | Entra mock `active` flag |
| HCM / `MNB-Workday` | Authoritative cube create for `lab.entra1` | Cloud-directory mock rows |

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Entra-shaped** | APIs that look like Microsoft Graph/SCIM | `/entra/v1/users`, `/entra/scim/v2` |
| **accountEnabled / active** | Directory disable flag on the mock | SCIM `active: false` |
| **Correlation** | Link app account → Identity cube | `userName` / `externalId` → `lab.entra1` |
| **SoR boundary** | Which system is truth for which question | Mock for IIQ lifecycle; Keycloak for login |

- **Wrong way:** Assuming mock disable kills Employee Portal.  
- **Wrong way:** Using only Helen/Priya/Marcus for the disable drill and leaving them inactive.  
- **Wrong way:** Wrong SCIM host (`localhost` inside IIQ container) — use `http://connector-mock:8091/entra/scim/v2`.  
- **Wrong way:** Calling this a real Entra tenant in evidence notes.

## Intent

- Exercise Graph- and SCIM-shaped curls against connector-mock.  
- Aggregate `MNB-EntraID` and correlate a disposable account.  
- Disable on the mock and prove IIQ sees inactive.  
- Prove SSO still works until Keycloak changes — document the split.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] Stack:

```bash
./tools/lab/docker/up.sh --enterprise
```

- [ ] IIQ: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Employee Portal (SSO proof): [http://localhost:8092/](http://localhost:8092/)
- [ ] Keycloak Admin: [http://localhost:8085/admin/](http://localhost:8085/admin/) — `admin` / `admin` — realm **`meridian`**
- [ ] connector-mock healthy + Entra routes:

```bash
curl -sf http://localhost:8091/health | python3 -m json.tool
curl -sf http://localhost:8091/entra/scim/v2/Users | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("totalResults"), "users")'
```

- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/252
```

## Do this

### Task 1 — Inventory Graph-shaped and SCIM-shaped APIs

1. Graph-shaped list:

```bash
curl -sf http://localhost:8091/entra/v1/users | python3 -m json.tool | head -60
```

- **Expect:** `@odata.count` and `value[]` with `userPrincipalName`, `accountEnabled`, `employeeId`.

2. SCIM list + filter:

```bash
curl -sf 'http://localhost:8091/entra/scim/v2/Users?filter=userName%20eq%20%22priya.wire%22' \
  | python3 -m json.tool
```

- **Expect:** SCIM `ListResponse` with Priya’s fixture (`id` often `entra-priya`). Fixture reads are fine — your **disable subject** will be disposable.

3. Groups:

```bash
curl -sf http://localhost:8091/entra/v1/groups | python3 -m json.tool
```

- **Expect:** `mnb-workstation-users`, `mnb-hr-intranet`, `mnb-finance-portal` (names may appear under `displayName`).

Save Graph head + SCIM filter output under evidence (no secrets).

- **Why:** you must recognize both shapes before trusting IIQ aggregation.
- **Expect:** curls succeed without auth (lab mock).

### Task 2 — Create disposable `lab.entra1` (HCM + IIQ + Keycloak)

Never disable Helen/Priya/Marcus for this drill.

1. HCM joiner:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.entra1 Lab Entra \
  lab.entra1@meridiannb.com 'Technology'
```

2. Confirm:

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.entra1 | python3 -m json.tool \
  | grep -E 'userName|email|active|status|id|workerId'
```

Note the worker **id** (e.g. `MNBxxxxx`) — you will use it as Entra `externalId`.

3. IIQ: Aggregate **`MNB-Workday`** → Refresh Identity Cube for `lab.entra1` → confirm cube exists.

4. Keycloak user for later SSO proof (birthright IdP if live; else manual):

- Prefer: cube shows **`MNB-Keycloak-IdP`** with `portal-users` (Lesson 216/217).  
- Fallback: Keycloak Admin → `meridian` → Add user `lab.entra1`, email `lab.entra1@meridiannb.com`, password `LabUser1!` (Temporary OFF), join **`portal-users`**.

5. Baseline Portal login once: [http://localhost:8092/](http://localhost:8092/) as `lab.entra1` / `LabUser1!` → success → sign out.

- **Why:** you need a working SSO baseline **before** you disable the Entra mock account.
- **Expect:** cube + Keycloak user + one successful Portal login recorded.

### Task 3 — Inject disposable account into the Entra mock

The mock has no public POST create for `/entra/scim/v2/Users`. Seed the disposable row into the mock’s JSON, then restart so in-memory state reloads.

1. From your **Mac** (repo host), resolve the HCM worker id and inject the Entra Resource into the mock container:

```bash
EXT_ID=$(curl -s http://localhost:8091/hcm/v1/workers/lab.entra1 \
  | python3 -c 'import sys,json; w=json.load(sys.stdin); print(w.get("id") or w.get("workerId") or "lab.entra1")')
echo "externalId=$EXT_ID"

docker exec -e EXT_ID="$EXT_ID" mnb-connector-mock python3 -c '
import json, os
from pathlib import Path
p = Path("/opt/mnb/lab-data/connectors/entra/Users.json")
data = json.loads(p.read_text())
uname = "lab.entra1"
resources = data.setdefault("Resources", [])
resources[:] = [r for r in resources if r.get("userName") != uname]
resources.append({
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "id": "entra-lab-entra1",
    "userName": uname,
    "active": True,
    "displayName": "Lab Entra",
    "externalId": os.environ["EXT_ID"],
    "emails": [{"value": "lab.entra1@meridiannb.com", "primary": True}],
    "groups": [{"value": "mnb-workstation-users", "display": "Workstation Users"}],
})
data["totalResults"] = len(resources)
p.write_text(json.dumps(data, indent=2) + "\n")
print("wrote", uname, "externalId", os.environ["EXT_ID"], "total", data["totalResults"])
'
```

2. Restart mock so `_ENTRA_STATE` reloads:

```bash
docker restart mnb-connector-mock
sleep 5
curl -sf 'http://localhost:8091/entra/scim/v2/Users?filter=userName%20eq%20%22lab.entra1%22' \
  | python3 -m json.tool
```

- **Why:** IIQ can only aggregate accounts the mock exposes.
- **Expect:** SCIM returns one Resource for `lab.entra1`, `active: true`, `id: entra-lab-entra1`.

> **Watch out:** Restarting connector-mock also resets **HCM in-memory** workers created only via API this session if they were not persisted the way your build persists them. Re-check `curl …/hcm/v1/workers/lab.entra1` — re-run `hcm-scenario.sh joiner` if missing. IIQ cube can remain even if HCM row needs re-POST.

### Task 4 — Verify-or-import `MNB-EntraID` and Test Connection

1. IIQ → **Applications → Application Definition** → search `MNB-EntraID`  
2. If missing:

```bash
./tools/lab/enterprise/seed-enterprise.sh
# or import config/Application/MNB-Application-EntraID.xml via Debug → Import / MCP
```

3. Open the app → confirm:

| Setting | Expect |
| --- | --- |
| Type | SCIM 2.0 |
| Host | `http://connector-mock:8091/entra/scim/v2` |
| Auth | No Auth (lab) |

4. **Test Connection** → Success  
5. Run **Account Aggregation** on **`MNB-EntraID`** → Complete  

- **Why:** wrong host (`localhost:8091` from inside IIQ) fails aggregation mysteriously.
- **Expect:** aggregation completes; accounts include `lab.entra1` / `entra-lab-entra1`.

### Task 5 — Correlate to `lab.entra1`

1. Open Identity `lab.entra1` → Application Accounts  
2. Confirm a link to **`MNB-EntraID`**  
3. If uncorrelated: use enterprise correlation standard (`userName` / `externalId` ↔ identity name / `userId`) — **Application → Correlation** or Identity Correlation UI; re-aggregate / refresh as needed  

- **Why:** disable on an uncorrelated account does not teach lifecycle on a person.
- **Expect:** correlated Entra link on cube `lab.entra1` with **active / enabled** true.

Save a screenshot of Application Accounts.

### Task 6 — PATCH disable on the mock

```bash
curl -sf -X PATCH 'http://localhost:8091/entra/scim/v2/Users/entra-lab-entra1' \
  -H 'Content-Type: application/json' \
  -d '{"Operations":[{"op":"replace","path":"active","value":false}]}' \
  | python3 -m json.tool
```

- **Expect:** response shows `"active": false`.

Confirm with GET:

```bash
curl -sf 'http://localhost:8091/entra/scim/v2/Users/entra-lab-entra1' \
  | python3 -c 'import sys,json; u=json.load(sys.stdin); print(u["userName"], u["active"])'
```

- **Expect:** `lab.entra1 False`

Save PATCH JSON under evidence as `patch-disable.json.txt`.

### Task 7 — Re-aggregate and prove IIQ inactive

1. Aggregate **`MNB-EntraID`** again → Complete  
2. Open `lab.entra1` → Application Accounts → **`MNB-EntraID`**  
3. Confirm account shows **inactive / disabled** (UI label varies; native `active=false`)

- **Why:** IIQ truth for this app is aggregation, not the curl alone.
- **Expect:** IIQ reflects disable after re-agg.

Screenshot cube account state → `iiq-entra-inactive.png`.

### Task 8 — Prove SSO is **not** dead (Keycloak still wins)

1. Fresh private window  
2. Open [http://localhost:8092/](http://localhost:8092/)  
3. Sign in as `lab.entra1` / `LabUser1!`

- **Why:** this is the exam question — mock disable ≠ SSO revoke.
- **Expect:** Portal **succeeds**. Write that result explicitly — do not skip.

Save screenshot `portal-still-works-after-mock-disable.png`.

Optional contrast (not required for “done,” but good):

1. Keycloak Admin → `lab.entra1` → Disable user **or** remove `portal-users`  
2. Retry Portal → fails  
3. Re-enable for cleanliness  

### Task 9 — Evidence note (SoR boundary)

Write `~/iiq-lab-evidence/sandbox/252/SOR-BOUNDARY.txt`:

```text
Lesson 252
Subject: lab.entra1
Entra mock id: entra-lab-entra1
PATCH active=false → IIQ MNB-EntraID shows inactive after re-agg: YES
Employee Portal SSO after mock disable: STILL WORKS
What actually kills SSO: Keycloak disable or remove portal-users
One-liner: MNB-EntraID owns IIQ cloud-directory lifecycle; Keycloak owns browser login.
```

- **Expect:** file exists with the split stated in one sentence.

## If it fails

| Symptom | Fix |
| --- | --- |
| 404 on `/entra/...` | Rebuild connector-mock image so `serve.py` includes Entra routes; `docker compose … up -d --build connector-mock` |
| SCIM filter empty for `lab.entra1` | Task 3 JSON edit + `docker restart mnb-connector-mock`; re-curl |
| Test Connection / agg fails | Host must be `http://connector-mock:8091/entra/scim/v2` from IIQ’s network — not Mac `localhost` |
| Account not on cube | Correlation + re-agg; confirm `userName` matches identity name |
| IIQ still active after PATCH | Re-run aggregation; confirm PATCH id `entra-lab-entra1` (or userName) returned `active: false` |
| Portal fails after mock PATCH only | Something else broke Keycloak (session, missing user, missing `portal-users`) — fix IdP; mock is not the cause |
| HCM worker missing after mock restart | Re-run `hcm-scenario.sh joiner lab.entra1 …` |
| Disabled Helen/Priya by mistake | PATCH them back `"active": true`; prefer disposable next time |

## You are done when

- [ ] Graph + SCIM curls saved for inventory and `lab.entra1`  
- [ ] `MNB-EntraID` aggregates and correlates `lab.entra1`  
- [ ] PATCH disable + re-agg shows inactive in IIQ  
- [ ] Portal SSO still works after mock disable  
- [ ] `SOR-BOUNDARY.txt` states mock vs Keycloak ownership  

## Control note

- **Control:** Correct system-of-record boundary — cloud-directory-shaped lifecycle vs actual SSO  
- **Owner:** IAM Engineering  
- **SLA (lab):** No lesson artifact conflates mock disable with SSO revocation  
- **Evidence:** `~/iiq-lab-evidence/sandbox/252/`  
- **Out of scope:** Real Microsoft Graph tenant, Entra password reset, Conditional Access

## Quick check

1. Does disabling `MNB-EntraID` kill Employee Portal? → **No** — only Keycloak controls SSO  
2. What does `MNB-EntraID` own? → IIQ lifecycle (agg / disable / group metadata on the mock)  
3. What IIQ host string must the app use? → `http://connector-mock:8091/entra/scim/v2`  
4. Why a disposable `lab.entra1`? → Avoid leaving seeded personas permanently inactive  
5. What proves you understood the split? → Portal still works after mock PATCH + written SoR note  

## Feedback

Could you explain to an examiner — without this page — why a green “disabled in Entra” on this lab does not prove the leaver cannot open Portal?

If something failed, note the **task number**, PATCH response `active` value, and whether Portal succeeded or failed after disable.

## Navigate

- Previous: [Lesson 251](251-workstation-grant-revoke.md)
- Next: [Lesson 253](253-intranet-sso-apps.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
