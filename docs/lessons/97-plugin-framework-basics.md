# Lesson 97 — Plugin Framework Basics

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Plugins, APIs & SSD |
| **Time** | 60–75 minutes |
| **Prereq** | [Lesson 96 — Workgroups, Capabilities & Scopes](96-workgroups-capabilities-scopes.md) |
| **Lab data** | `lab-data/connectors/plugins/README.md`; study trees `pluginsrc/AccessRequestApprovalAddins/`, `pluginsrc/SWECertificationsAddins/` |

## Learning objectives

You will be able to:

- Explain what an IIQ **Plugin** packages (manifest, REST, snippets, install XML)
- Read `manifest.xml` keys: `restResources`, `snippets`, `settings`, `fullPage`, versioning
- Install or inspect a plugin via the Plugin UI (or document bake-into-WAR path)
- List Meridian enterprise checklist items before promoting a plugin
- State why secrets must not live in plugin XML

## Why this matters

Plugins extend IdentityIQ with Meridian-specific UI and REST without forking the product. Unversioned, ungated plugins become shadow IT inside the bank’s control plane.

**Control / audit:** Examiners treat custom UI/REST as part of the production system. You must show version, required rights, install evidence, and that credentials are not hardcoded.

## Concepts

| Artifact | Role |
| --- | --- |
| `manifest.xml` | Plugin identity, version, REST classes, page snippets, settings |
| `import/install/*.xml` | Objects created on install (QuickLinks, Configuration, Rules) |
| `ui/js`, `ui/css` | Snippet scripts/styles injected into matching pages |
| REST resource class | Server endpoints under the plugin |
| Settings | Admin-configurable plugin parameters (non-secret) |

```text
  Plugin ZIP / WAR bake
        |
        v
  manifest.xml  ---> register REST + snippets + settings
        |
        +-- import/install --> QuickLink / Rule / Config objects
        |
        v
  Capability check (rightRequired) ---> authorized operators only
```

**Study examples in this repo**

| Plugin | Interesting pieces |
| --- | --- |
| `AccessRequestApprovalAddins` | Snippets on `commonWorkItem`, `identities`, `accessRequest`; REST resource list |
| `SWECertificationsAddins` | Cert page snippets; `settings` entry; `serviceExecutors` placeholder |

**Enterprise checklist** (from `lab-data/connectors/plugins/README.md`):

1. Manifest with REST / Snippets / Settings  
2. Import install XML for QuickLinks / config  
3. Version + upgrade strategy (`minUpgradableVersion`)  
4. SSB `plugins` build flag / image bake for homelab  
5. Capability-based authorization for custom REST  
6. No secrets in plugin XML — encrypted IIQ config or K8s secrets  

**IIQ terms:** A **Snippet** injects JS/CSS when the browser URL matches a regex. **rightRequired** on a snippet or QuickLink gates visibility by capability right.

## Before you start

- [ ] IIQ up; `spadmin` login
- [ ] Repo paths readable: `pluginsrc/*/manifest.xml`
- [ ] Read `lab-data/connectors/plugins/README.md`
- [ ] Lesson 96 capabilities understood (who may install plugins)
- [ ] Note: lab may use UI install **or** WAR bake only—follow your LOCAL_SETUP / SSD path

## Lab procedure

### Task 1 — Read AccessRequestApprovalAddins manifest

1. Open `pluginsrc/AccessRequestApprovalAddins/manifest.xml`.
2. Record: `name`, `version`, `minSystemVersion`, `displayName`.
3. List every class under `restResources`.
4. For each `Snippet`, note `regexPattern` and script paths.
5. Confirm whether `rightRequired` is empty (lab gap to fix in production design).

**Expected result:** One-page manifest digest for AccessRequestApprovalAddins.

**If it fails:** File missing—clone/pull repo; do not invent paths.

### Task 2 — Read SWECertificationsAddins + settings

1. Open `pluginsrc/SWECertificationsAddins/manifest.xml`.
2. Note `settings` → `defaultName` and empty `serviceExecutors`.
3. Note certification page snippet regex `.*\/certification\.?(jsf|xhtml)`.
4. Skim `import/install/configuration.xml` and `rule.xml` for install-time objects.

**Expected result:** Digest comparing the two plugins (REST vs cert UI focus).

**If it fails:** Read only manifests; mark install XML as deferred.

### Task 3 — Locate install QuickLink XML

1. Open `pluginsrc/AccessRequestApprovalAddins/import/install/QuickLink.xml`.
2. Note whether the file is a stub or populated in your checkout.
3. Write the Meridian rule: install XML must create **named** objects (`MNB-*`) and reference capabilities—not anonymous leftovers.

**Expected result:** Note on install XML role + whether this example is stubbed.

**If it fails:** Document expected structure from README checklist anyway.

### Task 4 — Plugin UI inventory

1. Log in as `spadmin`.
2. Open **Gear** → **Plugins** (or **Setup** → Plugins / equivalent).
3. List installed plugins: name, version, status.
4. If your lab allows upload, do **not** upload untrusted ZIPs; only use repo-built artifacts.
5. Screenshot the plugin list for the binder.

**Expected result:** Inventory of installed plugins with versions.

**If it fails:** Plugins menu missing—confirm SystemAdministrator; else document WAR-baked plugins only and list from `pluginsrc/`.

### Task 5 — Meridian promotion gate (paper)

1. Draft a one-page “Plugin promote to prod” checklist using the six README items.
2. Add owners: IAM (`helen.ross`), AppSec review, CAB ticket ID placeholder.
3. Explicit line: “Secrets: none in manifest; use encrypted attributes / K8s.”

**Expected result:** Signed-ready checklist template (unsigned OK in lab).

### Task 6 — Authorization gap analysis

1. From Lesson 96, name which capability should be required to call plugin REST.
2. Mark any `rightRequired=""` in study manifests as **finding**.
3. Record remediation: set right + grant only to `MNB-WG-IAM-Ops`.

**Expected result:** At least one security finding with remediation owner.

## Acceptance criteria

- [ ] Manifest digests for both `pluginsrc` examples
- [ ] Plugin UI inventory (or WAR-bake inventory) filed
- [ ] Six-item enterprise checklist drafted for Meridian
- [ ] Secret-handling rule written explicitly
- [ ] `rightRequired` gap noted with remediation
- [ ] Install XML role explained in binder notes

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Plugin install fails | Version / minSystemVersion | Align with IIQ 8.x lab; check logs |
| Snippet JS 404 | Wrong path in manifest | Paths relative to plugin root `ui/...` |
| REST 403 | Missing capability | Grant right; never disable auth |
| Settings blank after upgrade | `minUpgradableVersion` skip | Bump version carefully; test upgrade path |
| Duplicate QuickLink | Re-install without uninstall | Uninstall/reinstall or import idempotent XML |

## Training binder evidence

- Manifest digests (two plugins)  
- Plugin list screenshot  
- Promotion checklist  
- Authz finding on empty `rightRequired`  

## Knowledge check

1. Name four things a plugin can register in `manifest.xml`.
2. What is a Snippet’s `regexPattern` for?
3. Why forbid secrets in plugin XML?
4. Which repo path holds Meridian study plugins?
5. What workgroup should typically receive rights to custom IAM toolkit REST?

### Answers

1. REST resources, snippets, settings, fullPage (also serviceExecutors, versioning keys).  
2. Decide which IIQ pages receive injected JS/CSS.  
3. Plugins are packaged/versioned in git and WARs—secrets would leak and resist rotation.  
4. `pluginsrc/` (plus checklist in `lab-data/connectors/plugins/README.md`).  
5. `MNB-WG-IAM-Ops` (or tighter custom capability)—not all users.

## Stretch lab

Trace one JS file from a snippet to the UI behavior it alters; document the page URL and risk if the script fails open.

## Summary

- Plugins are versioned packages: manifest + UI + optional REST + install XML.
- Meridian requires checklist, rights gating, and no secrets in XML.
- Study `pluginsrc` before writing your own toolkit (Lesson 98).

## Versioning and upgrade strategy

| Situation | Version action |
| --- | --- |
| New plugin | Start at `1.0.0` |
| Settings schema change | Minor/major bump; set `minUpgradableVersion` thoughtfully |
| Security fix only | Patch bump; re-test snippets on target pages |
| Abandoned plugin | Uninstall in lower env first; remove install objects |

```text
  Develop --> unit/UI test sandbox --> peer review manifest rights
       --> SSB bake --> dev smoke --> CAB --> prod
```

### Task 7 — Uninstall / reinstall rehearsal (sandbox only)

1. If a disposable plugin exists in lab, uninstall via Plugin UI.
2. Confirm QuickLinks from install XML disappear or orphan—note orphans as cleanup debt.
3. Reinstall; confirm version string matches manifest.
4. Never rehearse uninstall against shared prod-like plugins without change ticket.

**Expected result:** Notes on clean uninstall behavior or orphan objects list.

**If it fails:** Paper rehearsal with checklist only.

### Snippet safety rules

1. Snippets run in the authenticated user’s browser session—treat JS as trusted code review surface.
2. Empty `rightRequired` means any authenticated user hitting the page gets the script—unacceptable for approval-page add-ins.
3. Prefer capability-gated snippets on `commonWorkItem` / certification pages.
4. CSS must not hide Approve/Revoke controls (Lesson 103).

Compare Meridian policy to the study manifests’ empty `rightRequired` values and treat those as teaching anti-patterns.

---

**Previous:** [Lesson 96 — Workgroups, Capabilities & Scopes](96-workgroups-capabilities-scopes.md)  
**Next:** [Lesson 98 — Build Meridian Toolkit Plugin](98-build-meridian-toolkit-plugin.md)
