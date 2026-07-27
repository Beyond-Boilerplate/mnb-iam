# Lesson 97 — Plugin Framework Basics

**Level:** Intermediate  
**Track:** Plugins, APIs & SSD  
**Time:** 75–90 min  
**Prereq:** Lesson 96 — Workgroups, Capabilities & Scopes  

**Lab data:**
- Repo: `lab-data/connectors/plugins/README.md`
- Study trees: `pluginsrc/AccessRequestApprovalAddins/`, `pluginsrc/SWECertificationsAddins/`

---

## Learning objectives

You will be able to:

- Explain what an IdentityIQ **Plugin** packages: `manifest.xml`, REST resources, page snippets, settings, and install-time XML
- Read and critique `manifest.xml` keys (`restResources`, `snippets`, `settings`, `fullPage`, versioning, `rightRequired`)
- Inventory plugins via the Plugin UI (or document the WAR-bake path used in this SSD repo)
- Apply Meridian’s six-item enterprise plugin checklist before any promotion
- State why secrets must never live in plugin XML and how `rightRequired` gates custom UI/REST

---

## Why this matters

**Business.** Meridian’s operators need bank-specific helpers on approval and certification screens — approval add-ins, cert widgets, toolkit pings — without forking IdentityIQ. Plugins are the supported extension point. Last year a contractor dropped an unsigned ZIP into a shared sandbox “just to demo a banner.” It worked for a week, then broke after a patch because nobody owned the version or the capability rights. That is how shadow IT appears inside the IAM control plane.

**Control / audit.** Examiners treat custom UI and REST as part of the production system. When they ask *"show me every non-product code path that can approve access or call privileged APIs,"* your answer is a versioned plugin inventory with required rights, install evidence, and a signed promotion checklist — not “someone uploaded something once.” Credentials in plugin XML are an automatic finding.

---

## Concepts

### What a plugin actually is

An IIQ **Plugin** is a versioned package that registers extensions with the product at install (or WAR bake) time. It is not a random jar in `WEB-INF/lib`. Think of it as a mini-product with a contract:

| Artifact | What it is | Meridian example |
| --- | --- | --- |
| `manifest.xml` | Plugin identity, version, REST classes, snippets, settings | `name`, `version`, `minSystemVersion` |
| `import/install/*.xml` | Objects created on install | QuickLinks, Configuration, Rules |
| `ui/js`, `ui/css` | Scripts/styles injected into matching pages | Approval-page add-in CSS |
| REST resource class | Server endpoints under the plugin | Toolkit ping (Lesson 98) |
| Settings | Admin-configurable non-secret parameters | Banner text, feature toggles |

### Snippets and rights — define before you trust them

A **Snippet** injects JS/CSS when the browser URL matches a `regexPattern`. That means the script runs in the authenticated user’s session on that page. **`rightRequired`** on a snippet or QuickLink gates visibility by capability right. Empty `rightRequired` means any authenticated user who hits the page gets the script — unacceptable for approval or certification pages at a bank.

The naive approach: ship a helpful approval snippet with no right so “everyone can see it.” Under exam that becomes: *"any teller who can open a work item also loads your custom approval logic."* Meridian requires non-empty rights and grants them only to `MNB-WG-IAM-Ops` (or tighter).

### Study examples in this repo

| Plugin | What to notice |
| --- | --- |
| `AccessRequestApprovalAddins` | Snippets on `commonWorkItem`, `identities`, `accessRequest`; REST resource list |
| `SWECertificationsAddins` | Cert page snippets; `settings` entry; empty `serviceExecutors` placeholder |

Treat empty `rightRequired` values in study manifests as **teaching anti-patterns**, not production templates.

### Enterprise checklist (from the plugins README)

1. Manifest with REST / Snippets / Settings  
2. Import install XML for QuickLinks / config objects  
3. Version + upgrade strategy (`minUpgradableVersion`)  
4. SSB `plugins` build flag / image bake for homelab  
5. Capability-based authorization for custom REST  
6. No secrets in plugin XML — encrypted IIQ config or K8s secrets  

---

## How it works

```text
  Plugin ZIP / WAR bake
        │
        ▼
  manifest.xml ──► register REST + snippets + settings
        │
        ├── import/install ──► QuickLink / Rule / Config objects
        │
        ▼
  Capability check (rightRequired) ──► authorized operators only
        │
        ▼
  Browser (snippet JS/CSS)  and/or  HTTP client (plugin REST)
```

| Stage | What happens | Failure mode |
| --- | --- | --- |
| Install / bake | Product reads manifest; registers classes and snippets | `minSystemVersion` mismatch → install rejected |
| Install XML | Creates named objects (`MNB-*`) | Stub/empty XML → REST works, QuickLink missing |
| Page load | URL matches snippet regex → JS/CSS inject | Wrong path → 404; empty right → over-exposure |
| REST call | Framework + capability check | Missing right → 403 (correct); no check → finding |
| Upgrade | Version bump vs `minUpgradableVersion` | Schema skip → blank settings after upgrade |

**Versioning strategy Meridian uses**

| Situation | Version action |
| --- | --- |
| New plugin | Start at `1.0.0` |
| Settings schema change | Minor/major bump; set `minUpgradableVersion` thoughtfully |
| Security fix only | Patch bump; re-test snippets on target pages |
| Abandoned plugin | Uninstall in lower env first; remove install objects |

---

## Real-world setup (outside the lab UI)

Even when the lab only inspects manifests, production plugin work starts outside IIQ:

### Step 1 — Decide the trust boundary

1. Who may install plugins? (Almost always SystemAdministrator / break-glass — Lesson 109.)
2. Who may *use* plugin REST/UI? (Named capability → `MNB-WG-IAM-Ops`.)
3. Who signs off AppSec review before CAB? (Record owners: IAM `helen.ross`, AppSec, CAB ticket.)

### Step 2 — Signing and artifact provenance

1. Build plugins only from the SSD repo (`pluginsrc/`), never from random internet ZIPs.
2. Prefer SSB bake into the WAR/image so production never accepts ad-hoc Plugin UI uploads.
3. If your bank requires signed artifacts, treat the plugin ZIP like any other release binary: CI builds it, signs it, stores it in the artifact registry, and deploy pulls that digest.

### Step 3 — Secret handling

1. Plugin settings hold non-secrets (banner text, thresholds).
2. API keys, passwords, and tokens go in encrypted IIQ attributes, vault, or K8s secrets — never `manifest.xml`, never install XML.
3. Document the secret location on the promotion checklist.

### Step 4 — Upgrade rehearsal

1. In sandbox, install `1.0.0`, change a setting, upgrade to `1.0.1`, confirm settings survive.
2. Uninstall a disposable plugin and note orphan QuickLinks — cleanup debt before prod.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; Lesson 96 capabilities clear
- [ ] Repo paths readable: `pluginsrc/*/manifest.xml`
- [ ] Read `lab-data/connectors/plugins/README.md`
- [ ] Know whether your lab uses Plugin UI install **or** WAR bake only (LOCAL_SETUP / SSD)
- [ ] No untrusted ZIPs — only repo-built artifacts

---

## Lab procedure

### Task 1 — Read AccessRequestApprovalAddins manifest

You cannot design Meridian’s toolkit until you can read a real manifest. This task builds that literacy on a study plugin.

1. Open `pluginsrc/AccessRequestApprovalAddins/manifest.xml`.
2. Record: `name`, `version`, `minSystemVersion`, `displayName`.
3. List every class under `restResources`.
4. For each `Snippet`, note `regexPattern`, script paths, and whether `rightRequired` is empty.
5. Mark empty `rightRequired` as a **finding** (teaching anti-pattern).

**Expected result:** One-page manifest digest for AccessRequestApprovalAddins with at least one authz finding noted.

**If it fails:** File missing — clone/pull the repo; do not invent paths.

### Task 2 — Read SWECertificationsAddins + settings

Different plugins emphasize different surfaces. Cert UI add-ins are where CSS/JS risk is highest because decision buttons live on those pages.

1. Open `pluginsrc/SWECertificationsAddins/manifest.xml`.
2. Note `settings` → `defaultName` and the empty `serviceExecutors` list (Lesson 102 will use that extension point).
3. Note certification page snippet regex `.*\/certification\.?(jsf|xhtml)`.
4. Skim `import/install/configuration.xml` and `rule.xml` for install-time objects.

**Expected result:** Digest comparing the two plugins (REST/approval focus vs cert UI focus).

### Task 3 — Locate install QuickLink XML

Install XML is how plugins create durable IIQ objects. Anonymous leftovers after uninstall are operational debt.

1. Open `pluginsrc/AccessRequestApprovalAddins/import/install/QuickLink.xml`.
2. Note whether the file is a stub or populated in your checkout.
3. Write the Meridian rule: install XML must create **named** objects (`MNB-*`) and reference capabilities — not anonymous leftovers.

**Expected result:** Note on install XML role + whether this example is stubbed.

### Task 4 — Plugin UI inventory

Examiners ask what is installed *now*, not what exists in git. Inventory the running system.

1. Log in as `spadmin`.
2. Open **Gear** → **Plugins** (or **Setup** → Plugins / equivalent menu path).
3. List installed plugins: name, version, status.
4. Do **not** upload untrusted ZIPs; only repo-built artifacts.
5. Screenshot the plugin list for the binder.

**Expected result:** Inventory of installed plugins with versions (or WAR-bake inventory from `pluginsrc/` if UI is absent).

**If it fails:** Plugins menu missing — confirm SystemAdministrator; else document WAR-baked plugins only.

### Task 5 — Meridian promotion gate (paper)

Promotion without a gate is how the contractor ZIP story happens.

1. Draft a one-page “Plugin promote to prod” checklist using the six README items.
2. Add owners: IAM (`helen.ross`), AppSec review, CAB ticket ID placeholder.
3. Explicit line: “Secrets: none in manifest; use encrypted attributes / K8s.”
4. Add upgrade path: uninstall rehearsal in sandbox before prod.

**Expected result:** Signed-ready checklist template (unsigned OK in lab).

### Task 6 — Authorization gap analysis

Lesson 96 gave you capabilities; this task connects them to plugins.

1. Name which capability/right should be required to call Meridian plugin REST (e.g., `MNBToolkitAccess` in Lesson 98).
2. Mark any `rightRequired=""` in study manifests as findings.
3. Record remediation: set right + grant only to `MNB-WG-IAM-Ops`.
4. Note CSS safety: custom CSS must never hide Approve/Revoke controls (Lesson 103).

**Expected result:** At least one security finding with remediation owner `helen.ross`.

### Task 7 — Uninstall / reinstall rehearsal (sandbox only)

1. If a disposable plugin exists in lab, uninstall via Plugin UI.
2. Confirm QuickLinks from install XML disappear — or list orphans as cleanup debt.
3. Reinstall; confirm version string matches manifest.
4. Never rehearse uninstall against shared prod-like plugins without a change ticket.

**Expected result:** Notes on clean uninstall behavior or orphan objects list.

**If it fails:** Paper rehearsal with checklist only.

---

## Acceptance criteria

- [ ] Manifest digests for both `pluginsrc` examples
- [ ] Plugin UI inventory (or WAR-bake inventory) filed
- [ ] Six-item enterprise checklist drafted for Meridian
- [ ] Secret-handling rule written explicitly
- [ ] `rightRequired` gap noted with remediation
- [ ] Install XML role explained; uninstall notes captured

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Plugin install fails | Version / `minSystemVersion` mismatch | Align with IIQ 8.x lab; check logs |
| Snippet JS 404 | Wrong path in manifest | Paths relative to plugin root `ui/...` |
| REST 403 | Missing capability | Grant right; never disable auth |
| Settings blank after upgrade | `minUpgradableVersion` skip | Bump version carefully; test upgrade path |
| Duplicate QuickLink | Re-install without uninstall | Uninstall/reinstall or import idempotent XML |
| Everyone sees snippet | Empty `rightRequired` | Set right; reinstall; grant only to ops WG |

---

## Training binder evidence

- Manifest digests (two plugins)
- Plugin list screenshot
- Promotion checklist with owners
- Authz finding on empty `rightRequired`
- Uninstall/orphan notes

---

## Knowledge check

1. Name four things a plugin can register in `manifest.xml`.
2. What is a Snippet’s `regexPattern` for?
3. Why forbid secrets in plugin XML?
4. Which repo path holds Meridian study plugins?
5. What workgroup should typically receive rights to custom IAM toolkit REST?
6. Why is empty `rightRequired` on an approval-page snippet a finding?

### Answers

1. REST resources, snippets, settings, fullPage (also `serviceExecutors`, versioning keys).
2. Decide which IIQ pages receive injected JS/CSS.
3. Plugins are packaged/versioned in git and WARs — secrets would leak and resist rotation.
4. `pluginsrc/` (plus checklist in `lab-data/connectors/plugins/README.md`).
5. `MNB-WG-IAM-Ops` (or a tighter custom capability) — not all users.
6. Any authenticated user hitting that page loads custom logic that can affect approvals.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “IdentityIQ plugins” for your version’s Plugin Manager and manifest reference.
- [SailPoint Community — Services Standard Deployment](https://community.sailpoint.com/t5/Services-Standard-Deployment/ct-p/SSD) — how plugins bake into SSB/SSD deployments (Compass login).
- [OWASP ASVS v4.0.3](https://owasp.org/www-project-application-security-verification-standard/) — V4 Access Control and V14 Configuration: least privilege for custom UI/API surfaces.
- [NIST SP 800-53 Rev. 5 — CM-7 / AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — least functionality and least privilege applied to IAM platform extensions.
- [docs/SSD.md](../SSD.md) — this repo’s SSD layout and build commands for plugin bake.

---

## Stretch lab

Trace one JS file from a snippet to the UI behavior it alters; document the page URL and the risk if the script fails open (e.g., hides a control or auto-submits). Propose the exact `rightRequired` value and workgroup grant.

---

## Summary

- Plugins are versioned packages: manifest + UI + optional REST + install XML — not ad-hoc jars.
- Meridian requires the six-item checklist, rights gating, signed/baked artifacts, and no secrets in XML.
- Study `pluginsrc` anti-patterns before writing your own toolkit in Lesson 98.

---

**Previous:** [Lesson 96 — Workgroups, Capabilities & Scopes](96-workgroups-capabilities-scopes.md)  
**Next:** [Lesson 98 — Build Meridian Toolkit Plugin](98-build-meridian-toolkit-plugin.md)
