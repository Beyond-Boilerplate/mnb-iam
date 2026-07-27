# Lesson 98 — Build Meridian Toolkit Plugin

| Field | Value |
| --- | --- |
| **Level** | Advanced |
| **Track** | Plugins, APIs & SSD |
| **Time** | 75–90 minutes |
| **Prereq** | [Lesson 97 — Plugin Framework Basics](97-plugin-framework-basics.md) |
| **Lab data** | `lab-data/connectors/plugins/README.md`; patterns from `pluginsrc/AccessRequestApprovalAddins/` |

## Learning objectives

You will be able to:

- Scaffold plugin `mnb-iam-toolkit` (display name Meridian IAM Toolkit) with version `1.0.0`
- Define `manifest.xml` with one REST resource and one settings entry
- Add install XML for QuickLink `MNB-QL-Toolkit-Ping`
- Document capability `rightRequired` for REST and QuickLink
- Describe how SSB / image bake includes the plugin for sandbox vs homelab

## Why this matters

Meridian needs a supported extension point for ops utilities (health ping, lab helpers) instead of one-off Debug hacks. A disciplined toolkit plugin is the pattern for every later custom UI.

**Control / audit:** Custom code in banking IAM must be named, versioned, rights-gated, and promoted via SSB—not copied into `web/` anonymously.

## Concepts

**Target shape**

```text
pluginsrc/mnb-iam-toolkit/
  manifest.xml
  src/.../rest/MnbToolkitPingResource.java   (or package path you choose)
  ui/js/mnb-toolkit.js                       (optional snippet)
  ui/css/mnb-toolkit.css                     (optional)
  import/install/QuickLink.xml
  import/install/Capability.xml              (optional custom right)
```

| Piece | Meridian requirement |
| --- | --- |
| Plugin name | `mnb-iam-toolkit` |
| REST | `GET` ping returns JSON `{ "status":"ok", "bank":"MNB" }` |
| QuickLink | `MNB-QL-Toolkit-Ping` → toolkit page or REST docs note |
| Authz | Non-empty `rightRequired`; grant to `MNB-WG-IAM-Ops` |
| Secrets | None |

```text
  Operator (helen.ross)
        |
        v
  QuickLink MNB-QL-Toolkit-Ping
        |
        v
  Plugin REST /plugin/mnb-iam-toolkit/.../ping
        |
        v
  Capability check ---> 200 OK + JSON
```

**Build note:** Exact Java package and JAX-RS annotations vary by IIQ plugin SDK version. This lesson prioritizes **correct structure and Meridian naming**; compile against your lab’s plugin API. If compile is blocked, deliver complete scaffold + binder compile plan.

## Before you start

- [ ] Lesson 97 digests complete
- [ ] `pluginsrc/` writable in your clone
- [ ] JDK matching lab IIQ (17/21 per project docs) available **or** scaffold-only mode accepted
- [ ] `MNB-WG-IAM-Ops` exists (Lesson 96)
- [ ] Read [docs/SSD.md](../SSD.md) plugins / WAR bake concepts

## Lab procedure

### Task 1 — Create directory tree

1. Under repo root, create `pluginsrc/mnb-iam-toolkit/`.
2. Create subdirs: `import/install/`, `ui/js/`, `ui/css/`, and `src/` package folders for your REST class.
3. Add empty placeholders for JS/CSS if you will not inject snippets yet.

**Expected result:** Tree matches Concepts “Target shape” (files may be stubs).

**If it fails:** Create under `~/iiq-lab-data/plugins/mnb-iam-toolkit/` and note “promote into pluginsrc before PR.”

### Task 2 — Author manifest.xml

1. Copy structure from `pluginsrc/AccessRequestApprovalAddins/manifest.xml`.
2. Set `name="mnb-iam-toolkit"`, `displayName="Meridian IAM Toolkit"`, `version="1.0.0"`, `minSystemVersion` to your lab (e.g., `8.0` / `8.4`).
3. Set `minUpgradableVersion` to `1.0.0`.
4. Register `restResources` with your fully qualified REST class name.
5. Add a `settings` string `toolkitBanner` default `Meridian National Bank IAM Toolkit`.
6. Set `rightRequired` on FullPage/snippets to a Meridian right name you will create or reuse (e.g., `MNBToolkitAccess`).

**Expected result:** Valid-looking `manifest.xml` with Meridian names and non-empty rights.

**If it fails:** Keep XML well-formed; fix class name later when compiling.

### Task 3 — REST ping resource (stub or compile)

1. Create Java class exposing a ping endpoint (follow existing `*AddinsUI.java` style in `pluginsrc`).
2. Return a simple OK payload including bank code `MNB`.
3. Ensure methods check plugin authorization (framework + capability).
4. If you cannot compile in this session: leave compilable stub comments and record classpath dependency on IIQ plugin API jars.

**Expected result:** Source file present; binder notes compile command or “scaffold-only.”

**If it fails:** Document OpenAPI-style contract for the ping anyway—contract is still evidence.

### Task 4 — Install QuickLink XML

1. Create `import/install/QuickLink.xml` with QuickLink name `MNB-QL-Toolkit-Ping`.
2. Point action to the plugin full page or REST helper URL pattern used in your IIQ version.
3. Require the same right as the manifest.
4. Set owner/category appropriate for IAM Ops (not global “everyone”).

**Expected result:** Install XML ready for plugin install / `importdynamic`.

**If it fails:** Minimal sailpoint wrapper with commented QuickLink attributes still counts if you document the intended fields.

### Task 5 — Capability / workgroup binding

1. Create or document Capability including right `MNBToolkitAccess` (name may vary).
2. Assign to `MNB-WG-IAM-Ops` / `helen.ross`.
3. Confirm `spadmin` retains access for break-glass install only.

**Expected result:** Rights matrix line for toolkit plugin.

### Task 6 — Package / install path

1. Prefer SSB path: enable plugins build flag per project docs; rebuild WAR (`./build.sh -Dtarget=sandbox clean war`) when ready.
2. Alternate: Plugin UI upload of built ZIP **only** from your artifact—not random internet ZIPs.
3. After install, as `helen.ross`, open QuickLink; as an unprivileged user, confirm denial.
4. Record version `1.0.0` on binder cover.

**Expected result:** Installed (or bake plan) + positive/negative access test.

**If it fails:** Homelab image bake deferred—file PR checklist referencing [docs/HOMELAB-CD.md](../HOMELAB-CD.md).

## Acceptance criteria

- [ ] `pluginsrc/mnb-iam-toolkit/` (or lab-data mirror) scaffold exists
- [ ] `manifest.xml` with version `1.0.0`, REST entry, settings, rights
- [ ] QuickLink `MNB-QL-Toolkit-Ping` install XML present
- [ ] Capability binding to `MNB-WG-IAM-Ops` documented
- [ ] Positive + negative access test noted
- [ ] No secrets in any plugin file

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| ClassNotFound on REST | Wrong FQCN in manifest | Match package + class exactly |
| QuickLink 404 | Wrong URL / page not registered | Align FullPage title and link action |
| Everyone sees QuickLink | Empty rightRequired | Set right; reinstall |
| Upgrade skips settings | Versioning keys wrong | Set minUpgradableVersion correctly |
| Build ignores plugin | SSB plugins flag off | Enable per SSD.md / build.properties |

## Training binder evidence

- Tree listing of `mnb-iam-toolkit`  
- manifest.xml excerpt (redact nothing sensitive—there should be none)  
- QuickLink XML  
- Access test notes (helen.ross vs unprivileged)  

## Knowledge check

1. What is the plugin **name** vs **displayName** for the toolkit?
2. What JSON business marker should ping return for Meridian?
3. Which workgroup receives toolkit access?
4. Where do install-time QuickLinks live in the plugin tree?
5. Name one promotion vehicle for plugins in this repo’s SSD model.

### Answers

1. name `mnb-iam-toolkit`; displayName `Meridian IAM Toolkit`.  
2. Bank marker such as `"bank":"MNB"` with `"status":"ok"`.  
3. `MNB-WG-IAM-Ops` (via capability/right).  
4. `import/install/` (e.g., `QuickLink.xml`).  
5. SSB WAR bake / plugins flag, or controlled Plugin UI upload of built artifact; homelab image publish.

## Stretch lab

Add a second REST method that returns toolkit `settings.toolkitBanner` value; prove settings survive upgrade from `1.0.0` to `1.0.1`.

## Summary

- Scaffold `mnb-iam-toolkit` with ping REST + QuickLink + rights.
- Structure and authorization matter more than clever UI.
- Promote only through SSB/image pipelines with version evidence.

## Meridian toolkit backlog (post-ping)

Prioritize only after ping + rights work:

| Feature | Type | Right |
| --- | --- | --- |
| Env banner helper | Snippet | `MNBToolkitAccess` |
| Open SoD count widget | REST + UI | `MNBToolkitAccess` |
| Aggregation last-success board | REST | Task read + toolkit |
| Break-glass instruction page | FullPage | SystemAdministrator only |

Do not implement privileged revoke buttons in v1.

### Task 7 — README for operators

1. Create `pluginsrc/mnb-iam-toolkit/README.md` with: purpose, version, install steps, required capability, smoke test curl, owner `helen.ross`.
2. Link to `lab-data/connectors/plugins/README.md` enterprise checklist.
3. State upgrade path `1.0.0` → `1.0.1`.

**Expected result:** Operator README in plugin tree.

**If it fails:** Keep README under `~/iiq-lab-data/plugins/mnb-iam-toolkit/README.md`.

### Failure modes to test

1. User without right → 403 on REST and QuickLink hidden.
2. Wrong IIQ minSystemVersion → install rejected.
3. Duplicate plugin name → install conflict message.
4. Missing install XML → REST works but QuickLink absent (document).

Record pass/fail for each in binder.

---

**Previous:** [Lesson 97 — Plugin Framework Basics](97-plugin-framework-basics.md)  
**Next:** [Lesson 99 — IIQ Console & Automation](99-iiq-console-and-automation.md)
