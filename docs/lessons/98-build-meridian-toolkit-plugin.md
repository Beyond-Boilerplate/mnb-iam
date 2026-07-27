# Lesson 98 — Build Meridian Toolkit Plugin

**Level:** Advanced  
**Track:** Plugins, APIs & SSD  
**Time:** 90–120 min  
**Prereq:** Lesson 97 — Plugin Framework Basics  

**Lab data:**
- Repo: `lab-data/connectors/plugins/README.md`
- Patterns: `pluginsrc/AccessRequestApprovalAddins/`
- SSD: [docs/SSD.md](../SSD.md)

---

## Learning objectives

You will be able to:

- Scaffold plugin `mnb-iam-toolkit` (display name **Meridian IAM Toolkit**) at version `1.0.0`
- Author `manifest.xml` with one REST resource, one settings entry, and non-empty `rightRequired`
- Add install XML for QuickLink `MNB-QL-Toolkit-Ping`
- Bind capability access to `MNB-WG-IAM-Ops` / `helen.ross` and prove positive/negative authz
- Describe how SSB / image bake includes the plugin for sandbox vs homelab promotion

---

## Why this matters

**Business.** Meridian IAM ops (`helen.ross` and `MNB-WG-IAM-Ops`) need a supported place for health pings and lab helpers. Without it, people paste Debug console hacks into runbooks. Those hacks rot, are unversioned, and show up in exams as “undocumented custom code.” A disciplined toolkit plugin is the pattern for every later custom UI.

**Control / audit.** Custom code in banking IAM must be named, versioned, rights-gated, and promoted via SSB — not copied anonymously into `web/`. When the examiner asks *"how do you deploy custom REST into production?"* the answer is: git → SSB WAR/image → capability-gated plugin `mnb-iam-toolkit` v1.0.0 — with install evidence and access tests.

---

## Concepts

### Target shape

```text
pluginsrc/mnb-iam-toolkit/
  manifest.xml
  src/.../rest/MnbToolkitPingResource.java
  ui/js/mnb-toolkit.js          (optional snippet)
  ui/css/mnb-toolkit.css        (optional)
  import/install/QuickLink.xml
  import/install/Capability.xml (optional custom right)
  README.md                     (operator runbook)
```

| Piece | Meridian requirement |
| --- | --- |
| Plugin name | `mnb-iam-toolkit` |
| Display name | `Meridian IAM Toolkit` |
| REST | `GET` ping → JSON `{ "status":"ok", "bank":"MNB" }` |
| QuickLink | `MNB-QL-Toolkit-Ping` |
| Authz | Non-empty `rightRequired` (e.g. `MNBToolkitAccess`); grant to `MNB-WG-IAM-Ops` |
| Secrets | None — ever |

### Why ping first, not a revoke button

The naive first plugin builds a “fix access” button. That is how you create an uncertified privileged control surface. Meridian’s v1 is deliberately boring: a **ping** that proves packaging, rights, and promotion work. Privileged revoke buttons require workflow, audit actions, and SoD review — backlog only after ping + rights are proven.

### Build vs scaffold

Exact JAX-RS annotations and package names vary by IIQ plugin SDK version. This lesson prioritizes **correct structure and Meridian naming**. Compile against your lab’s plugin API jars. If compile is blocked, deliver a complete scaffold plus a binder compile plan — structure and authorization still count as evidence.

### Post-ping backlog (do not implement in v1)

| Feature | Type | Right |
| --- | --- | --- |
| Env banner helper | Snippet | `MNBToolkitAccess` |
| Open SoD count widget | REST + UI | `MNBToolkitAccess` |
| Aggregation last-success board | REST | Task read + toolkit |
| Break-glass instruction page | FullPage | SystemAdministrator only |

---

## How it works

```text
  Operator (helen.ross)
        │
        ▼
  QuickLink MNB-QL-Toolkit-Ping
        │
        ▼
  Plugin REST /plugin/mnb-iam-toolkit/.../ping
        │
        ▼
  Capability check (MNBToolkitAccess)
        │
        ├── allowed → 200 OK + {"status":"ok","bank":"MNB"}
        └── denied  → 403 (and QuickLink hidden)
```

| Path | Mechanism | Evidence |
| --- | --- | --- |
| SSB bake | `plugins` flag / image layer includes plugin | WAR/image digest in CI |
| Plugin UI upload | Controlled upload of **your** built ZIP only | Install screenshot + version |
| Install XML | Creates `MNB-QL-Toolkit-Ping` | QuickLink visible to entitled users |
| Settings | `toolkitBanner` default string | Survives upgrade when versioning correct |

---

## Real-world setup (plugin signing & promotion)

### Step 1 — Source of truth

1. All Meridian plugins live under `pluginsrc/<name>/` in the SSD repo.
2. No production install from a laptop Downloads folder.
3. Operator README states purpose, version, required capability, smoke curl, owner `helen.ross`.

### Step 2 — Build and sign

1. Enable plugins in SSB per [docs/SSD.md](../SSD.md) / `build.properties`.
2. `./build.sh -Dtarget=sandbox clean war` produces the deployable that includes the plugin.
3. CI archives the WAR/image; optional cosign/signing per bank supply-chain policy.
4. Homelab: follow image bake notes in [docs/HOMELAB-CD.md](../HOMELAB-CD.md) when present.

### Step 3 — Capability before install

1. Create right `MNBToolkitAccess` (name may vary) and Capability wrapping it.
2. Assign to `MNB-WG-IAM-Ops`; `spadmin` retains break-glass install only (Lesson 109).
3. Install plugin only after rights exist — otherwise you ship a 403-only experience and blame “the plugin.”

### Step 4 — Smoke and negative tests

1. As `helen.ross`: QuickLink visible; ping returns 200 + `bank=MNB`.
2. As unprivileged user (e.g. `raj.external`): QuickLink hidden; REST 403.
3. Record version `1.0.0` on the binder cover.

---

## Before you start

- [ ] Lesson 97 digests and checklist complete
- [ ] `pluginsrc/` writable in your clone
- [ ] JDK matching lab IIQ available **or** scaffold-only mode accepted
- [ ] `MNB-WG-IAM-Ops` exists (Lesson 96)
- [ ] Read [docs/SSD.md](../SSD.md) plugins / WAR bake concepts

---

## Lab procedure

### Task 1 — Create directory tree

Every production plugin starts as a boring, complete tree. Missing folders become “we’ll add install XML later” — and later never comes.

1. Under repo root, create `pluginsrc/mnb-iam-toolkit/`.
2. Create subdirs: `import/install/`, `ui/js/`, `ui/css/`, and `src/` package folders for your REST class.
3. Add empty placeholders for JS/CSS if you will not inject snippets yet.

**Expected result:** Tree matches Concepts “Target shape” (files may be stubs).

**If it fails:** Create under `~/iiq-lab-data/plugins/mnb-iam-toolkit/` and note “promote into pluginsrc before PR.”

### Task 2 — Author manifest.xml

Copy structure, change Meridian names, and never leave rights empty.

1. Copy structure from `pluginsrc/AccessRequestApprovalAddins/manifest.xml`.
2. Set `name="mnb-iam-toolkit"`, `displayName="Meridian IAM Toolkit"`, `version="1.0.0"`, `minSystemVersion` to your lab (e.g. `8.0` / `8.4`).
3. Set `minUpgradableVersion` to `1.0.0`.
4. Register `restResources` with your fully qualified REST class name.
5. Add settings string `toolkitBanner` default `Meridian National Bank IAM Toolkit`.
6. Set `rightRequired` on FullPage/snippets to `MNBToolkitAccess` (or your chosen right name).

**Expected result:** Valid-looking `manifest.xml` with Meridian names and non-empty rights.

### Task 3 — REST ping resource (stub or compile)

The ping is the contract other systems and synthetic monitors will call.

1. Create Java class exposing a ping endpoint (follow existing `*AddinsUI.java` style in `pluginsrc`).
2. Return OK payload including bank code `MNB`.
3. Ensure methods check plugin authorization (framework + capability).
4. If you cannot compile: leave clear stub comments and record classpath dependency on IIQ plugin API jars.

**Expected result:** Source file present; binder notes compile command or “scaffold-only”; OpenAPI-style contract written either way.

### Task 4 — Install QuickLink XML

Operators should not memorize REST paths. QuickLinks are the governed entry point.

1. Create `import/install/QuickLink.xml` with QuickLink name `MNB-QL-Toolkit-Ping`.
2. Point action to the plugin full page or REST helper URL pattern for your IIQ version.
3. Require the same right as the manifest.
4. Set owner/category for IAM Ops — not global “everyone.”

**Expected result:** Install XML ready for plugin install / `importdynamic`.

### Task 5 — Capability / workgroup binding

1. Create or document Capability including right `MNBToolkitAccess`.
2. Assign to `MNB-WG-IAM-Ops` / `helen.ross`.
3. Confirm `spadmin` retains access for break-glass install only.

**Expected result:** Rights matrix line for toolkit plugin.

### Task 6 — Package / install and access test

1. Prefer SSB: enable plugins build flag; `./build.sh -Dtarget=sandbox clean war`.
2. Alternate: Plugin UI upload of **your** built ZIP only.
3. After install, as `helen.ross`, open QuickLink; as an unprivileged user, confirm denial.
4. Record version `1.0.0` on binder cover.

**Expected result:** Installed (or bake plan) + positive/negative access test.

**If it fails:** Homelab image bake deferred — file PR checklist referencing HOMELAB-CD.

### Task 7 — Operator README + failure modes

1. Create `pluginsrc/mnb-iam-toolkit/README.md`: purpose, version, install steps, required capability, smoke curl, owner `helen.ross`.
2. Link to `lab-data/connectors/plugins/README.md` enterprise checklist.
3. State upgrade path `1.0.0` → `1.0.1`.
4. Test and record pass/fail: no-right → 403; wrong `minSystemVersion` → install rejected; duplicate name → conflict; missing install XML → REST without QuickLink.

**Expected result:** Operator README + failure-mode matrix in binder.

---

## Acceptance criteria

- [ ] `pluginsrc/mnb-iam-toolkit/` (or lab-data mirror) scaffold exists
- [ ] `manifest.xml` with version `1.0.0`, REST entry, settings, non-empty rights
- [ ] QuickLink `MNB-QL-Toolkit-Ping` install XML present
- [ ] Capability binding to `MNB-WG-IAM-Ops` documented
- [ ] Positive + negative access test noted
- [ ] Operator README present; no secrets in any plugin file

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| ClassNotFound on REST | Wrong FQCN in manifest | Match package + class exactly |
| QuickLink 404 | Wrong URL / page not registered | Align FullPage title and link action |
| Everyone sees QuickLink | Empty `rightRequired` | Set right; reinstall |
| Upgrade skips settings | Versioning keys wrong | Set `minUpgradableVersion` correctly |
| Build ignores plugin | SSB plugins flag off | Enable per SSD.md / build.properties |
| 403 for helen.ross | Right not on workgroup | Grant Capability to `MNB-WG-IAM-Ops` |

---

## Training binder evidence

- Tree listing of `mnb-iam-toolkit`
- `manifest.xml` excerpt (there should be nothing to redact)
- QuickLink XML
- Access test notes (`helen.ross` vs unprivileged)
- Operator README path

---

## Knowledge check

1. What is the plugin **name** vs **displayName** for the toolkit?
2. What JSON business marker should ping return for Meridian?
3. Which workgroup receives toolkit access?
4. Where do install-time QuickLinks live in the plugin tree?
5. Name one promotion vehicle for plugins in this repo’s SSD model.
6. Why is a revoke button forbidden in toolkit v1?

### Answers

1. name `mnb-iam-toolkit`; displayName `Meridian IAM Toolkit`.
2. Bank marker such as `"bank":"MNB"` with `"status":"ok"`.
3. `MNB-WG-IAM-Ops` (via capability/right).
4. `import/install/` (e.g. `QuickLink.xml`).
5. SSB WAR bake / plugins flag, or controlled Plugin UI upload of built artifact; homelab image publish.
6. Privileged actions need workflow, audit, and SoD review — ping proves packaging first.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “plugin development” / “Plugin Framework” for REST and manifest details for your version.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real plugin packaging and ClassNotFound troubleshooting threads.
- [OWASP Cheat Sheet — REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html) — authz, error handling, and least privilege for toolkit endpoints.
- [NIST SP 800-218 — SSDF](https://csrc.nist.gov/publications/detail/sp/800-218/final) — secure software development practices for custom IAM code (versioning, review, provenance).
- [docs/SSD.md](../SSD.md) — Meridian SSB everyday commands and CI shape.

---

## Stretch lab

Add a second REST method that returns toolkit `settings.toolkitBanner`; prove settings survive upgrade from `1.0.0` to `1.0.1`. Then draft (do not implement) the SoD count widget backlog item with audit action name `MNB_SOD_WATCH_RUN` foreshadowing Lesson 102.

---

## Summary

- Scaffold `mnb-iam-toolkit` with ping REST + QuickLink + rights — structure before clever UI.
- Positive/negative access tests and an operator README are part of “done.”
- Promote only through SSB/image pipelines with version evidence; no secrets, no revoke buttons in v1.

---

**Previous:** [Lesson 97 — Plugin Framework Basics](97-plugin-framework-basics.md)  
**Next:** [Lesson 99 — IIQ Console & Automation](99-iiq-console-and-automation.md)
