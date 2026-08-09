# Lesson 248 — SSD Export & Promote

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~100 minutes  
**Prereq:** Lessons 216–247 (objects you actually changed in the UI)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 101 / 108 / 103

> **Why:** If it only lives in the UI database, it is not engineered. Everything you built in this arc must survive `./tools/lab/docker/down.sh -v` or it never happened for compliance purposes.

## What this is

`config/` is this repo’s **Services Standard Build (SSB / SSD)** root — the source of truth promoted through real environments with `./build.sh`. Earlier lessons may have left durable objects only inside the running IIQ database. This lesson:

1. Inventories **exact** objects from prior sandbox lessons  
2. Exports clean XML into the matching `config/<Type>/` folders  
3. **Strips** instance ids / timestamps  
4. Tokenizes env-specific values with **`%%TOKENS%%`**  
5. Proves the classic **103 wrong-env banner** cue (`sandbox` vs `prod` properties + `web/` overlay)  
6. Runs **`./build.sh clean war`** + **`importdynamic`** and reads the log  
7. Diffs git, writes a real impact note, re-runs smoke  

| Promote surface | How it enters an environment |
| --- | --- |
| IIQ objects (Bundle, Workflow, Rule, Form, …) | Export → `config/` → `importdynamic` |
| Env-specific hosts / paths / banner text | `%%TOKENS%%` in `*.target.properties` substituted at build |
| UI branding / messages / CSS | `web/` overlays baked into the WAR (`./build.sh war`) |

> **Watch out:** MCP `export_sailpoint_object` / `import_sailpoint_object` can soft-fail on reference-heavy types (`IdentityTrigger`, `CertificationDefinition`). Config-as-code via `./build.sh importdynamic` is the path that must actually work for those.

## Know these

```text
Write inventory checklist (objects you really changed)
  → Export each object → matching config/ folder
  → Strip id/created/modified (+ Reference ids)
  → Replace hard-coded env values with %%TOKENS%%
  → Add / verify wrong-env banner token (%%MNB_BANNER%% / %%TARGET%%)
  → export SPTARGET=sandbox && ./build.sh clean war
  → ./build.sh importdynamic  (read per-object results)
  → git diff -- config/ web/ *.target.properties
  → 3-line impact note + e2e-smoke.sh
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **SSD / SSB** | Standard build layout for IIQ customization | Repo root `build.sh` + `config/` + `web/` |
| **`SPTARGET`** | Which `*.target.properties` file substitutes tokens | `sandbox` → `sandbox.target.properties` |
| **`%%TOKENS%%`** | Placeholders replaced at build time | `%%MNB_WIRE_FILE%%`, `%%MNB_BANNER%%` |
| **`importdynamic`** | Console import of `config/` XML into live IIQ | Per-object success/skip/fail lines |
| **Wrong-env banner** | Visible SANDBOX vs PROD cue (Lesson 103) | Prevents irreversible “I thought this was lab” edits |
| **Scrub** | Remove instance ids so XML re-imports cleanly | Drop `id` / `created` / `modified` |

- **Wrong way:** Committing Debug exports with `id="0a1b2c…"` and hoping the next env accepts them.  
- **Wrong way:** Hard-coding `localhost` / lab paths into shared XML without tokens.  
- **Wrong way:** Treating MCP soft-fail as “imported.”  
- **Wrong way:** Shipping branding that looks identical in sandbox and prod (no banner).  
- **Wrong way:** Writing a placeholder impact note that does not match `git diff`.

## Intent

- Export every object you changed across Lessons 216–247 into durable `config/`.  
- Scrub ids; tokenize env values; prove wrong-env banner wiring.  
- Run real `clean war` + `importdynamic` and read results line by line.  
- Leave git-ready evidence + a 3-line impact note + green smoke.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] You have **saved** (not only previewed) UI changes from the lessons you completed in 216–247
- [ ] Read [`config/README.md`](../../config/README.md) and [`docs/SSD.md`](../SSD.md) once
- [ ] From repo root, confirm build tooling:

```bash
cd /Users/alishaghatane/Documents/Sailpoint
./build.sh -version
```

- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/248
```

## Do this

### Task 1 — Exact inventory checklist (what you actually changed)

You cannot export what you forgot you changed. Copy this checklist into evidence and **check only objects that exist in your live IIQ** (create/export gaps are findings — do not invent files for objects you never built).

#### Roles / Bundles → `config/Bundle/`

| Object | Source lesson | In live IIQ? | Exported? |
| --- | --- | --- | --- |
| `MNB-Bundle-Birthright-Employee` | 216 | [ ] | [ ] |
| `MNB-IT-*` birthright IT packs you created (LDAP / IdP / Wire) | 216 | [ ] | [ ] |
| `MNB-Bundle-Wire-Initiator` | 216 / 221 | [ ] | [ ] |
| `MNB-Bundle-Wire-Approver` | 224 | [ ] | [ ] |
| `MNB-IT-BreakGlass-WireAppr` / `MNB-Bundle-BreakGlass-WireAppr` | 223 | [ ] | [ ] |
| `MNB-Bundle-Birthright-Contractor` (if created) | 220 | [ ] | [ ] |
| Other `MNB-Bundle-*` / `MNB-IT-*` you created | — | [ ] | [ ] |

#### Workflows → `config/Workflow/`

| Object | Source lesson | In live IIQ? | Exported? |
| --- | --- | --- | --- |
| `MNB-Workflow-Joiner` (with your manager-approval edit) | 217 / 242 | [ ] | [ ] |
| `MNB-Workflow-Leaver` | 219 | [ ] | [ ] |
| `MNB-Workflow-Access-Approval` | 222 | [ ] | [ ] |

#### Rules → `config/Rule/`

| Object | Source lesson | In live IIQ? | Exported? |
| --- | --- | --- | --- |
| Before/After provisioning rules from Lesson 241 | 241 | [ ] | [ ] |
| FieldValue / validation helper rules from Lesson 243 (if separate Rule objects) | 243 | [ ] | [ ] |
| Correlation / other `MNB-Rule-*` you created | — | [ ] | [ ] |

#### Forms → `config/Form/`

| Object | Source lesson | In live IIQ? | Exported? |
| --- | --- | --- | --- |
| `MNB-Form-AccessRequest-Extras` | 243 | [ ] | [ ] |

#### Policy → `config/Policy/`

| Object | Source lesson | In live IIQ? | Exported? |
| --- | --- | --- | --- |
| `MNB-Policy-SOD-Wire-Dual-Control` (or live name you imported/edited) | 224–225 | [ ] | [ ] |

#### IdentityTrigger → `config/IdentityTrigger/` (config-as-code path required)

| Object | Source lesson | In live IIQ? | Exported? |
| --- | --- | --- | --- |
| `MNB-IdentityTrigger-Joiner` | 217 | [ ] | [ ] |
| `MNB-IdentityTrigger-Leaver` | 219 | [ ] | [ ] |

#### CertificationDefinition → `config/CertificationDefinition/` (config-as-code path required)

| Object | Source lesson | In live IIQ? | Exported? |
| --- | --- | --- | --- |
| `MNB-Cert-Manager-Access-Review` (file often `MNB-CertificationDefinition-Manager.xml`) | 226 | [ ] | [ ] |
| `MNB-Cert-App-Owner-Wire` (file often `MNB-CertificationDefinition-AppOwner-Wire.xml`) | 227 | [ ] | [ ] |

#### Applications / Tasks / QuickLinks / Email (if you changed them)

| Object | Folder | Exported? |
| --- | --- | --- |
| Edited `MNB-*` Applications (schema, forms, URLs) | `config/Application/` | [ ] |
| Custom TaskDefinitions | `config/TaskDefinition/` | [ ] |
| QuickLinks from 244 | `config/QuickLink/` | [ ] |
| EmailTemplate edits from 232 | `config/EmailTemplate/` | [ ] |

Save the filled checklist as `~/iiq-lab-evidence/sandbox/248/inventory.md`.

- **Why:** Promotion without inventory is how “it worked in my lab” becomes missing in the next environment.
- **Expect:** a written list before any export.

### Task 2 — Export each checked object into `config/`

For every checked row:

1. In IIQ: **Debug → Export** (or Object Exporter) for that object name  
2. Place under the matching folder with SSB naming:

```text
config/<Type>/MNB-<Type>-<BusinessName>.xml
```

Examples:

```text
config/Bundle/MNB-Bundle-Wire-Initiator.xml
config/Workflow/MNB-Workflow-Access-Approval.xml
config/Form/MNB-Form-AccessRequest-Extras.xml
config/IdentityTrigger/MNB-IdentityTrigger-Joiner.xml
config/CertificationDefinition/MNB-CertificationDefinition-Manager.xml
```

3. Prefer the helper when MCP is healthy (scrubs automatically):

```bash
cd /Users/alishaghatane/Documents/Sailpoint
export MCP_API_KEY=mnb-lab-mcp-key
./tools/lab/scripts/sync-iiq-config.sh --write
git status -- config/
```

- **Why:** Folders map 1:1 to object types — wrong folder = silent miss on import.
- **Expect:** files land under the folders in [`config/README.md`](../../config/README.md).

### Task 3 — Strip ids and instance noise

If you exported by hand (not via sync script), scrub before build:

Remove from roots and nested elements:

- `id="…"`
- `created="…"`
- `modified="…"`
- `significantModified="…"`

On references, keep name only:

```xml
<!-- bad -->
<Reference class="sailpoint.object.Identity" id="0a…" name="spadmin"/>

<!-- good -->
<Reference class="sailpoint.object.Identity" name="spadmin"/>
```

Also drop aggregation run stats if present (`acctAggregationStart`, `TaskDefinition.runs`, etc.) — same rules as `scrub_xml` in `tools/lab/scripts/sync_iiq_config.py`.

Spot-check:

```bash
cd /Users/alishaghatane/Documents/Sailpoint
rg -n '\s(id|created|modified|significantModified)=' config/Bundle config/Workflow config/Form config/Rule config/Policy config/IdentityTrigger config/CertificationDefinition 2>/dev/null | head
```

- **Expect:** no instance id/timestamp hits on objects you just exported (shipped seed files may already be clean).
- **Why:** leftover ids cause DTD / “already exists” weirdness across environments.

### Task 4 — `%%TOKENS%%` for env-specific values

1. Open `sandbox.target.properties` and `prod.target.properties` at the **repo root**  
2. For any Application / Task XML that hard-codes a lab path or host, replace with an existing token (examples already in properties):

| Token | Typical use |
| --- | --- |
| `%%TARGET%%` | Environment name (`sandbox` / higher) |
| `%%MNB_WIRE_FILE%%` | Wire CSV / file path |
| `%%MNB_CORE_BANKING_FILE%%` | Core Banking file path |
| `%%AD_HOST%%` / `%%AD_PORT%%` | Directory hosts |
| `%%SERVER_HOST%%` | Generic host |

3. In XML use the token literally, e.g. `%%MNB_WIRE_FILE%%` — do **not** paste your Mac `/Users/…` path into committed Application XML  
4. If you introduce a **new** token, add it to **both** `sandbox.target.properties` and `prod.target.properties` with env-appropriate values

- **Why:** one XML, many environments — tokens are how SSB avoids “works only on my laptop.”
- **Expect:** no new hard-coded `/Users/alishaghatane/…` paths in files you exported this lesson.

### Task 5 — Wrong-env banner cue (classic 103)

Branding is a **safety control**, not decoration. Sandbox and prod must not look identical.

#### 5a — Tokenize banner text

1. Add (or confirm) in **`sandbox.target.properties`**:

```properties
%%MNB_BANNER%%=Meridian National Bank — SANDBOX
%%TARGET%%=sandbox
```

2. Add (or confirm) in **`prod.target.properties`**:

```properties
%%MNB_BANNER%%=Meridian National Bank — PRODUCTION
%%TARGET%%=prod
```

   (If `%%TARGET%%` already exists, only ensure banner differs by environment.)

#### 5b — Surface the cue in `web/`

1. Edit message overlay:

```text
web/WEB-INF/classes/sailpoint/web/messages/iiqCustom.properties
```

2. Set a visible key that operators see on login/home (example):

```properties
login_ui_welcome=%%MNB_BANNER%%
```

   If your build does not substitute tokens inside this properties file, use the sandbox literal for lab **and** document the prod value + token plan under evidence — still prove a visible **SANDBOX** string in the running UI.

3. Optional CSS cue (classic 103): add or note `web/css/mnb-branding.css` styling a header banner — keep it readable, not color-only.

#### 5c — Prove visibility

1. After Task 6 WAR path (or hot message reload if your lab allows), hard-refresh IIQ login/home  
2. Screenshot unmistakable **SANDBOX** (or your banner) under evidence  
3. Write the promotion rule:

```text
Banner text differs by SPTARGET via %%MNB_BANNER%%.
Never hard-code PRODUCTION into the only shared file without tokens.
```

- **Why:** wrong-environment administration is an incident — the banner is the cheap control (Lesson 103).
- **Expect:** evidence screenshot + token entries in sandbox vs prod properties.

> **Watch out:** QuickLink HTML is **not** a substitute for the global env banner.

### Task 6 — Build WAR for sandbox

From repo root:

```bash
cd /Users/alishaghatane/Documents/Sailpoint
export SPTARGET=sandbox
./build.sh clean war
```

- **Why:** WAR bake is what carries `web/` branding and token substitution into the deployable artifact.
- **Expect:** build completes; read the log for DTD / token warnings — not only the exit code.

Save the last ~80 lines of the build log under `~/iiq-lab-evidence/sandbox/248/build-war.log.txt`.

### Task 7 — `importdynamic` and read every result line

```bash
cd /Users/alishaghatane/Documents/Sailpoint
export SPTARGET=sandbox
./build.sh importdynamic
```

1. Read **per-object** import results — not only the summary  
2. For `IdentityTrigger` and `CertificationDefinition` rows especially: confirm **success** (or intentional overwrite), not silent MCP-era skip  
3. If a file you edited shows “already exists, skipped” and you needed overwrite: use your lab’s force/overwrite import path (Debug Import of that single file, or console import) and re-check the live object  

Save import log excerpt as `importdynamic.log.txt`.

- **Why:** “Build green” with skipped stale objects is how prod drifts from git.
- **Expect:** objects from your checklist present live after import.

### Task 8 — Diff + 3-line impact note

```bash
cd /Users/alishaghatane/Documents/Sailpoint
git status
git diff -- config/ web/ sandbox.target.properties prod.target.properties | head -200
```

Write a **genuine** 3-line impact note reflecting **your** diff (example shape — replace with real content):

```text
1) MNB-Workflow-Access-Approval + LCM-related exports now durable under config/Workflow.
2) MNB-Form-AccessRequest-Extras validation (min 20 + MNB ticket) exported under config/Form.
3) %%MNB_BANNER%% differs sandbox vs prod; iiqCustom.properties surfaces SANDBOX cue (103).
```

Save as `~/iiq-lab-evidence/sandbox/248/impact-note.txt`.

- **Why:** CAB / reviewers read impact notes — placeholders that ignore the diff fail review.
- **Expect:** note matches actual `git diff` themes (rule logic, workflow steps, form fields, banner tokens).

### Task 9 — Re-run automated smoke

```bash
cd /Users/alishaghatane/Documents/Sailpoint
./tools/lab/enterprise/e2e-smoke.sh
```

If present:

```bash
./tools/lab/enterprise/contract-tests.sh
```

Optional object assert:

```bash
./tools/iiq-verify/assert-mnb-objects.sh local
```

- **Expect:** checks still pass after promotion.  
- **Why:** import can break connectors/triggers even when Ant exits 0.

Save smoke summary under evidence.

## If it fails

| Symptom | Fix |
| --- | --- |
| `importdynamic` “object already exists, skipped” on an object you edited | Confirm live IIQ still has **new** logic; Debug Import that one XML with overwrite; do not trust skip |
| Build fails DTD validation | Leftover `id`/`created` — re-scrub Task 3 or re-run `sync-iiq-config.sh --write` |
| Git diff is only whitespace / id churn | You exported before saving the UI change, or scrub failed — re-save in IIQ, re-export |
| Token left literal `%%FOO%%` in running app | Token missing from `sandbox.target.properties`, or WAR not rebuilt after edit |
| No SANDBOX cue visible | Task 5 — message key not loaded / WAR not redeployed; set a visible login welcome string and hard-refresh |
| Smoke fails after import | Bisect last imported file; revert that XML locally and re-smoke |
| IdentityTrigger / CertDefinition missing live | Do **not** rely on MCP alone — confirm files under `config/` and Task 7 import lines |

## You are done when

- [ ] Inventory checklist filled for objects you actually changed  
- [ ] Matching scrubbed XML under the correct `config/` folders  
- [ ] `%%TOKENS%%` used for env-specific values you touched; **`%%MNB_BANNER%%`** (or equivalent) differs sandbox vs prod  
- [ ] Visible wrong-env **SANDBOX** cue evidenced (screenshot)  
- [ ] `./build.sh clean war` + `./build.sh importdynamic` logs saved and read  
- [ ] Real 3-line impact note matches `git diff`  
- [ ] `e2e-smoke.sh` still green  

## Control note

- **Control:** Config-as-code durability + wrong-environment UI cue for governance objects  
- **Owner:** IAM Engineering / Release  
- **SLA (lab):** Every intentional UI change from 216–247 has a matching `config/` (or `web/` / properties) artifact and passes import/smoke  
- **Evidence:** `~/iiq-lab-evidence/sandbox/248/` — inventory, build/import logs, banner screenshot, `git diff`, impact note, smoke summary  

## Quick check

1. Which two object types are most likely to soft-fail via MCP export/import? → `IdentityTrigger`, `CertificationDefinition`  
2. What attributes must you strip from Debug exports? → `id`, `created`, `modified` (and Reference ids)  
3. What substitutes `%%TOKENS%%` at build time? → `SPTARGET` → matching `*.target.properties`  
4. Why a SANDBOX banner (Lesson 103)? → Prevents irreversible prod changes on a look-alike UI  
5. What proves promotion did not break the estate? → `e2e-smoke.sh` (and contract tests if present) still green  

## Feedback

Could you promote a wiped lab’s custom roles/workflows/forms from `config/` alone (`clean war` → `importdynamic` → smoke) and still see a SANDBOX banner — without re-clicking the whole 216–247 arc?

If something failed, note the **task number**, the object name, and the exact `importdynamic` / build line (expected vs actual).

## Navigate

- Previous: [Lesson 247](247-iiq-rest-scim-live.md)
- Next: [Lesson 249](249-hardening-perf-lite.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · SSD: [SSD.md](../SSD.md) · Branding classic: [103](103-ui-customization-branding.md)
