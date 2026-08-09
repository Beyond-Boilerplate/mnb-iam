# Lesson 244 — QuickLinks That Operators Use

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~75 minutes  
**Prereq:** Lessons 212, 221–222, 243  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 95

> **Why:** If it takes seven clicks, nobody opens it. An operator who avoids the platform because every daily tool is buried three menus deep is a control gap, not a training issue.

## What this is

A **QuickLink** is a Home-page tile (or menu entry) that opens an IIQ screen or an external URL. Visibility is not “everyone with a login” — each tile is granted through a **DynamicScope** (who sees it) and optionally capabilities.

This estate already has SSD XML under `config/QuickLink/` for Request Access, Certifications, Work Items, Toolkit Console, and Employee Portal. Nothing in this drill assumes those objects survived your wipe. You will:

1. Inventory what `helen.ross` actually sees  
2. **Verify-or-create** `Self Service` DynamicScope + core operator QuickLinks  
3. Add **external** tiles for Mailpit and Gitea  
4. Prove every tile opens the right destination  
5. Remove or repoint any stale / broken binding  

| Tile type | Points at | Meridian example |
| --- | --- | --- |
| **Internal / relative** | IIQ JSF under `/identityiq/…` | Request Access → `/identityiq/accessRequest/accessRequest.jsf` |
| **External absolute** | Full `http(s)://…` URL | Mailpit → `http://localhost:8025` |
| **DynamicScope** | Who may see the tile | Stock `Self Service` for workforce |

> **Watch out:** Relative URLs like `/identityiq/...` open inside IIQ. Absolute URLs like `http://localhost:8025` open a separate browser tab. Mixing them up (relative path to Mailpit) produces a 404 inside IIQ.

## Know these

```text
Inventory Helen Home tiles
  → Verify-or-create DynamicScope "Self Service"
  → Verify-or-create MNB-QuickLink-Request-Access + Certifications (+ Work Items)
  → Create MNB-QuickLink-Mailpit + MNB-QuickLink-Gitea (external)
  → Grant both via Self Service (allowSelf)
  → Log in as helen.ross → every tile opens correct target
  → Audit / remove broken DynamicScope bindings
  → Screenshot final Home under evidence
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **QuickLink** | Named Home tile definition | `MNB-QuickLink-Request-Access` |
| **DynamicScope** | Population/capability gate for who sees a tile | `Self Service` |
| **messageKey** | Label the user reads on the tile | `Request Access`, `Mailpit` |
| **External QuickLink** | Tile whose `url` is a full browser URL | Mailpit `:8025`, Gitea `:8093` |
| **Stale binding** | Scope/population renamed or deleted | Tile missing or 404 with no loud error |

- **Wrong way:** Assuming tiles from Lesson 221 still exist after a DB wipe.  
- **Wrong way:** Granting a tile to a typo’d DynamicScope — silent empty Home for Helen.  
- **Wrong way:** Leaving a tile that 404s “for later.”  
- **Wrong way:** Pointing Mailpit at `localhost:8025` without `http://` (relative → IIQ 404).  
- **Wrong way:** Using only `spadmin` to judge operator UX — admins see different menus.

## Intent

- Prove Helen’s Home tiles map 1:1 to named QuickLink + DynamicScope objects.  
- Create missing QuickLinks (and `Self Service` if gone) — do not skip.  
- Add working external Mailpit + Gitea tiles.  
- Leave zero broken tiles for the Self Service population.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Helen login works: `helen.ross` / `LabUser1!` (or your seed password from Lesson 206)
- [ ] Mailpit reachable:

```bash
curl -sf -o /dev/null -w '%{http_code}\n' http://localhost:8025/
```

  - **Expect:** `200` (or any non-connection-refused success).

- [ ] Gitea reachable:

```bash
curl -sf -o /dev/null -w '%{http_code}\n' http://localhost:8093/
```

- [ ] Repo QuickLink XML present (for import fallback):

```bash
ls config/QuickLink/MNB-QuickLink-*.xml
```

- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/244
```

## Do this

### Task 1 — Inventory Helen’s Home tiles (as-is)

1. Log out of `spadmin` if needed  
2. Log in as `helen.ross` / `LabUser1!`  
3. On **Home**, list every QuickLink tile / card you see (name + what you think it opens)  
4. Save the list under evidence as `helen-home-before.txt`

- **Why:** you need a before-state so “I added Mailpit” is measurable, not assumed.  
- **Expect:** at least some self-service tiles **or** an honestly empty Custom area — both are valid starting points.

> **Tip:** If Helen has almost no tiles, that is the lesson — create them. Do not switch to `spadmin` and declare the drill done.

### Task 2 — Verify-or-create DynamicScope `Self Service`

Workforce tiles in this curriculum grant through **`Self Service`**.

1. As `spadmin`, open **Debug** (gear → Debug, or `/identityiq/debug`)  
2. **Object Browser** → type **`DynamicScope`** → search `Self Service`  

**If it exists:** open it and confirm it is not disabled / empty in a way that excludes Helen.

**If missing — create it:**

1. Still in Debug → **DynamicScope** → **New** (or import a minimal object)  
2. **Name:** `Self Service` (exact spelling — matches SSD XML)  
3. Configure selector / population so **active workforce** is included (common lab pattern: everyone, or population of active identities). Save.  
4. Alternative UI path on some builds: **Gear → Global Settings → IdentityIQ Configuration → QuickLinks** / **Quicklink Populations** — create population named so QuickLinks can reference **`Self Service`**.

Confirm Helen is in scope: if your DynamicScope uses a population, open that population’s member preview and find `helen.ross`.

- **Why:** QuickLinkOptions with `<DynamicScopeRef name="Self Service"/>` do nothing if the scope is missing.  
- **Expect:** object `Self Service` exists and includes Helen.

### Task 3 — Verify-or-create core operator QuickLinks

Preferred path — import SSD XML from the repo (creates exact names downstream lessons expect):

```bash
# From repo root — use Debug Import UI, or your usual importdynamic for these files:
# config/QuickLink/MNB-QuickLink-Request-Access.xml
# config/QuickLink/MNB-QuickLink-Certifications.xml
# config/QuickLink/MNB-QuickLink-Work-Items.xml
```

In IIQ as `spadmin`:

1. **Gear → Debug → Import** (or **Setup → Import from File**)  
2. Import each file above that is missing  
3. Confirm in Debug → **QuickLink** that these names exist:
   - `MNB-QuickLink-Request-Access`  
   - `MNB-QuickLink-Certifications`  
   - `MNB-QuickLink-Work-Items` (optional but useful)

**If you create manually instead of import:**

| Field | Request Access | Certifications |
| --- | --- | --- |
| **Name** | `MNB-QuickLink-Request-Access` | `MNB-QuickLink-Certifications` |
| **Label / messageKey** | `Request Access` | `Certifications` |
| **URL** | `/identityiq/accessRequest/accessRequest.jsf` | `/identityiq/certification/certifications.jsf` |
| **Window** | `_self` | `_self` |
| **QuickLinkOptions** | allowSelf + DynamicScope `Self Service` | same |

UI path varies by build — try in order:

1. **Gear → Global Settings → QuickLink Configuration** (or **IdentityIQ Configuration → QuickLinks**)  
2. Debug → QuickLink → New  
3. Import XML (always works)

- **Why:** Lessons 221–226 assume these names; inventing `QL-Request` breaks later drills.  
- **Expect:** all three objects present with `Self Service` options.

### Task 4 — Create external QuickLink `MNB-QuickLink-Mailpit`

1. As `spadmin`, create a new QuickLink (same UI path as Task 3)  
2. Set exactly:

| Field | Value |
| --- | --- |
| **Name** | `MNB-QuickLink-Mailpit` |
| **Label / messageKey** | `Mailpit` |
| **Category** | `Custom` (or equivalent) |
| **URL** | `http://localhost:8025` |
| **Window** | `_blank` |
| **Description** | `Lab SMTP catcher — Lesson 203/222 mail proof` |
| **QuickLinkOptions** | `allowSelf=true`, DynamicScope **`Self Service`** |

3. **Save**  
4. Re-open the object and confirm the URL is absolute `http://localhost:8025` (not `/identityiq/8025`)

- **Why:** operators check assignment mail constantly; burying Mailpit behind a bookmark trains the wrong habit.  
- **Expect:** QuickLink saved; not yet proven until Helen clicks it.

### Task 5 — Create external QuickLink `MNB-QuickLink-Gitea`

1. Create another QuickLink:

| Field | Value |
| --- | --- |
| **Name** | `MNB-QuickLink-Gitea` |
| **Label / messageKey** | `Gitea` |
| **URL** | `http://localhost:8093` |
| **Window** | `_blank` |
| **Description** | `Lab Git forge — SSD / PR evidence` |
| **QuickLinkOptions** | `allowSelf=true`, DynamicScope **`Self Service`** |

2. **Save**

- **Why:** Enterprise stack operators live in Gitea for config promotion evidence (Lesson 248).  
- **Expect:** object exists alongside Mailpit.

> **Watch out:** Employee Portal (`http://localhost:8092/`) may already exist as `MNB-QuickLink-Employee-Portal`. Do not confuse Portal with Gitea — different ports.

### Task 6 — Prove tiles as Helen (not spadmin)

1. Log out  
2. Log in as `helen.ross` / `LabUser1!`  
3. Hard-refresh Home (browser refresh)  
4. Confirm tiles for at least: **Request Access**, **Certifications**, **Mailpit**, **Gitea**  
5. Click each:

| Tile | Must open |
| --- | --- |
| Request Access | Access request UI (Lesson 221 catalog) |
| Certifications | Certifications list / campaigns UI |
| Mailpit | Mailpit web UI on `:8025` |
| Gitea | Gitea web UI on `:8093` |

6. From **Request Access**, search a known requestable role (e.g. Wire Initiator from 221) — prove the tile is not a dead shell  
7. From **Certifications**, confirm the page loads (empty list is OK if no open campaign)

- **Why:** `spadmin` Home is not the control surface helpdesk uses.  
- **Expect:** four working destinations; screenshot Helen Home as `helen-home-after.png`.

If a new tile is missing for Helen: re-check Task 2 membership and that QuickLinkOptions reference **`Self Service`** exactly (case/spacing).

### Task 7 — Audit stale DynamicScope bindings

1. As `spadmin`, Debug → **QuickLink** → list all QuickLinks (or Global Settings QuickLink list)  
2. For each Custom / Meridian tile, open **QuickLinkOptions** and note the DynamicScope name  
3. For every referenced DynamicScope, confirm the object still exists (Task 2 method)  
4. Fix actions:

| Finding | Action |
| --- | --- |
| Scope missing | Repoint to `Self Service` **or** recreate the named scope |
| URL 404 / wrong port | Fix URL; retest as Helen |
| Duplicate confusing tiles | Disable/delete the broken one; keep the `MNB-QuickLink-*` name |

5. Write `audit-quicklinks.txt` under evidence: name → scope → URL → pass/fail

- **Why:** renamed populations from earlier lessons silently hide tiles.  
- **Expect:** no Custom tile left that Helen can see but that fails on click.

### Task 8 — Final Home proof + evidence pack

1. Log in once more as `helen.ross`  
2. Screenshot final Home tile set  
3. Save under `~/iiq-lab-evidence/sandbox/244/`:
   - `helen-home-before.txt`  
   - `helen-home-after.png`  
   - `audit-quicklinks.txt`  

- **Why:** examiners ask “how does helpdesk get to mail and certs?” — one screenshot answers.  
- **Expect:** evidence folder complete.

## If it fails

| Symptom | Fix |
| --- | --- |
| Helen sees no new tiles | DynamicScope `Self Service` missing/excludes her; or QuickLinkOptions not saved; log out/in |
| Tile click → IIQ 404 | External URL missing `http://`; or relative path typo |
| Mailpit/Gitea connection refused | Stack not up — `curl` ports 8025/8093; restart enterprise compose |
| Import fails on QuickLink XML | Create manually with the field table in Tasks 3–5; keep exact **Name** values |
| Request Access tile opens blank | LCM / access request not configured — Lessons 221–222; tile itself may still be correct |
| Only `spadmin` sees tiles | Options granted to an admin-only scope — switch to `Self Service` |
| Certifications 404 | URL must be `/identityiq/certification/certifications.jsf` (check spelling) |

## You are done when

- [ ] DynamicScope **`Self Service`** exists and includes Helen  
- [ ] `MNB-QuickLink-Request-Access` and `MNB-QuickLink-Certifications` exist (imported or created)  
- [ ] `MNB-QuickLink-Mailpit` and `MNB-QuickLink-Gitea` exist with absolute URLs  
- [ ] As **helen.ross**, all four tiles open the correct destinations  
- [ ] Stale-binding audit file saved; no known-broken Custom tile remains  
- [ ] Evidence under `~/iiq-lab-evidence/sandbox/244/`

## Control note

- **Control:** Operator self-service usability (one-click access to daily tools)  
- **Owner:** IAM Engineering + Helpdesk Ops  
- **SLA (lab):** Zero broken/mystery tiles on an active persona’s Home  
- **Evidence:** `~/iiq-lab-evidence/sandbox/244/`  
- **Out of scope:** Designing brand-new LCM workflows (Lessons 222/242) — only the QuickLink surface

## Quick check

1. What object decides whether Helen sees a tile? → **DynamicScope** (here `Self Service`) on QuickLinkOptions  
2. Internal vs external QuickLink? → Relative `/identityiq/…` vs absolute `http://…` URL  
3. Why not validate tiles only as `spadmin`? → Admin menus ≠ workforce Home  
4. What silent failure hides a new tile? → Typo’d / missing DynamicScope name  
5. Exact Mailpit URL for this lab? → `http://localhost:8025`

## Feedback

Could you rebuild Helen’s operator Home from a wiped QuickLink list (Self Service → Request Access / Certs → Mailpit / Gitea → click-test) without this page?

If something failed, note the **task number**, the QuickLink **name**, and whether the failure was missing tile vs wrong URL vs scope.

## Navigate

- Previous: [Lesson 243](243-forms-live.md)
- Next: [Lesson 245](245-workgroups-scopes-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
