# Lesson 237 — Web Services Connector Depth

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lesson 209  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 68

> **Why:** WS outages trace to one of three things — bad root path, unfollowed pagination, or silent auth breakage. Practice diagnosing all three before a real one pages you.

## What this is

`MNB-WirePortal`/`MNB-ServiceNow` use `sailpoint.connector.webservices.WebServicesConnector`, IIQ's generic REST/SOAP adapter. Unlike purpose-built connectors, WS makes you configure every knob by hand: `genericWebServiceBaseUrl`, `authenticationMethod`, per-endpoint `connectionParameters` (`httpMethodType`, `contextUrl`, `sequenceNumberForEndpoint`). You read the mock's actual response shape, adjust the mapping, break `rootPath` on purpose, then fix it.

## Know these

| Failure mode | Symptom |
| --- | --- |
| Wrong `rootPath`/JSON path | Zero accounts imported, or a parse warning |
| Pagination not followed | Only page one imports |
| Auth broken (token rotation) | Distinct auth-failure text, separate from mapping failure |

**Wrong way:** Trusting **Test Connection** alone as proof the data path works — some builds only check reachability, not the actual aggregation endpoint's auth.

## Intent

- Inspect the raw JSON the connector-mock returns for `/users` and identify the real root array path.
- Adjust the WS application's aggregation root/attribute mapping to match.
- Break `rootPath` deliberately and read the exact aggregation error IIQ produces.
- Fix it and confirm a clean re-aggregation with the right account count.

## Before you start

- [ ] Lesson 209 `MNB-WirePortal` aggregating cleanly
- [ ] `connector-mock` reachable at `http://localhost:8091`
- [ ] Baseline account count noted from a prior clean aggregation
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/237`

## Do this

1. `curl -s http://localhost:8091/users | python3 -m json.tool`.  
   **Expect:** Note the exact root: top-level array `[...]` or nested (`{"users": [...]}` / `{"Resources": [...]}`).
2. **Applications → Application Definition → MNB-WirePortal → Aggregation** (root-path/JSON field).  
   **Expect:** Configured root path matches what you observed in step 1.
3. Run **Aggregate**.  
   **Expect:** Task Result shows a baseline account count — note it.
4. Break it: change the root path to a key that doesn't exist (e.g. `resources` when the real key is `users`), save, re-run **Aggregate**.  
   **Expect:** Either zero accounts with a warning, or a parse exception referencing the missing path.
5. Read the Task Result's error/warning and copy the exact text.  
   **Expect:** Text is specific enough to diagnose without guessing.
6. Fix the root path back, re-run **Aggregate**.  
   **Expect:** Account count matches step 3 again — the mapping, not luck, drives correct aggregation.
7. Change `authenticationMethod` to something wrong (e.g. `Basic` with fake creds) and **Test Connection**.  
   **Expect:** A distinct auth-failure error, visibly different from the mapping failure in step 5.
8. Revert auth, confirm **Test Connection** passes again.  
   **Expect:** Green again with original config.
9. Document one paragraph: if `/users` paginated, which fields (`nextPageUrl`/`offset`/`totalResults`) the WS pagination config would need — compare to the SCIM mock's shape from 210/238.  
   **Expect:** Note saved, no need to implement against this mock.
10. Save the raw JSON, both error texts, and your pagination note under `~/iiq-lab-evidence/sandbox/237/`.

## If it fails

- **Aggregation "succeeds" with zero accounts, no visible error** — check the Task Result's warning log level, not just the summary line.
- **Test Connection passes even with wrong auth** — run a real aggregate to be sure; some checks only verify reachability.
- **Can't find where root path is configured** — check **Schema Map** or a **JSON Path** field; a custom `JDBCBuildMap`/`WebServicesResponseHandler` rule under the app's **Rules** tab may be doing the parsing instead.

## You are done when

You've diagnosed and fixed a WS mapping failure by reading the real error text, and separately observed a distinct auth-failure error for comparison.

## Control note

- **Control:** WS connector fault-diagnosis competency (mapping vs auth vs pagination).  
- **Owner:** IAM Engineering.  
- **SLA (lab):** Root cause identified from Task Result text, not guesswork.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/237/` — raw JSON, mapping error, auth error, pagination note.

## Quick check

1. Name the three common WS failure modes. → Bad root path, unfollowed pagination, broken auth.  
2. Does Test Connection always prove the data path works? → No — some builds only check reachability.  
3. Where might mapping logic hide instead of a declarative field? → A custom rule under the app's **Rules** tab.

## Navigate

- Previous: Lesson 236
- Next: Lesson 238
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
