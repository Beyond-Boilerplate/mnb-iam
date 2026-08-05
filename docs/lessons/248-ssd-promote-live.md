# Lesson 248 — SSD Export & Promote

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lessons 216–242  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 101 / 108

> **Why:** If it only lives in the UI database, it is not engineered. Everything you built in this arc must survive `./tools/lab/docker/down.sh -v` or it never happened for compliance purposes.

## What this is

Every earlier lesson in this arc — birthright roles (216), the joiner workflow edit (242), the before/after rules (241), the SOD policy — currently exists only inside the running IIQ database. `config/` is this repo's Services Standard Build root, the source of truth promoted through real environments via `./build.sh`. This lesson exports every object you changed, runs the real build/import pipeline, imports the two object types the MCP layer can soft-fail on, diffs it in git, and re-runs the automated smoke.

## Know these

| Object type | Export folder |
| --- | --- |
| Application | `config/Application/` |
| Role/Bundle | `config/Bundle/` |
| Workflow | `config/Workflow/` |
| Rule | `config/Rule/` |
| Form | `config/Form/` |

**Wrong way:** Trusting MCP's `export_sailpoint_object`/`import_sailpoint_object` for reference-heavy objects like `IdentityTrigger`/`CertificationDefinition` — these can soft-fail; config-as-code via `./build.sh` is the path that must actually work for them.

## Intent

- Export every Application/Role/Workflow/Rule you changed in Lessons 216–242 into `config/`.
- Run `./build.sh` for the sandbox target and `importdynamic`, reading actual results.
- Import `IdentityTrigger` and `CertificationDefinition` objects via the config-as-code path.
- Diff `git diff -- config/` and write a real 3-line impact note.
- Re-run `./tools/lab/enterprise/e2e-smoke.sh` and confirm it's still green after promotion.

## Before you start

- [ ] All of 216, 217/242, 241, 243 objects saved (not just previewed) in the UI
- [ ] `config/README.md` export/clean steps reviewed
- [ ] `SPTARGET=sandbox` build environment available
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/248`

## Do this

1. List what you actually changed across Lessons 216–242 in the UI: birthright roles (216), joiner/leaver workflows (217/242), before/after rules (241), any form (243) or SOD constraint touched.  
   **Expect:** A written list — you can't export what you forgot you changed.
2. For each object, export clean XML (Debug export page or Object Exporter), stripping internal ids/timestamps per `config/README.md`, into the matching folder.  
   **Expect:** Files land under `config/Application/`, `config/Bundle/`, `config/Workflow/`, `config/Rule/`, `config/Form/`.
3. `export SPTARGET=sandbox && ./build.sh clean war`.  
   **Expect:** Read the actual build output for errors; check for DTD validation warnings, not just the exit code.
4. `./build.sh importdynamic`.  
   **Expect:** Read the per-object import results line by line — note anything skipped or failed, not just the summary line.
5. Confirm `IdentityTrigger` (`MNB-IdentityTrigger-Joiner`, `MNB-IdentityTrigger-Leaver`) and `CertificationDefinition` (`MNB-Cert-Manager-Access-Review`, `MNB-Cert-App-Owner-Wire`) are present in `config/` and imported cleanly.  
   **Expect:** These specifically go through the config-as-code path, not the MCP API shortcut.
6. `git status` and `git diff -- config/` from the repo root.  
   **Expect:** Real content changes (your rule logic, workflow step, role provisioning policy), not just reformatting noise.
7. Write a genuine 3-line impact note, e.g.: `1) MNB-Workflow-Joiner now gates on manager approval before provisioning.  2) MNB-Rule-Wire-Dept-Guard blocks wire-role grants outside Treasury/Commercial Banking.  3) MNB-Cert-Manager-Access-Review unchanged structurally but now has real campaign history.`  
   **Expect:** Note reflects actual diffs, not a placeholder.
8. Re-run `./tools/lab/enterprise/e2e-smoke.sh` (and `./tools/lab/enterprise/contract-tests.sh` if present).  
   **Expect:** Every check still passes.
9. Save the build/import log excerpts, `git diff` output, impact note, and smoke test summary under `~/iiq-lab-evidence/sandbox/248/`.

## If it fails

- **`importdynamic` reports "object already exists, skipped"** — fine for idempotent re-imports, but for objects you specifically edited, confirm the skip didn't leave the *old* version live; check for an overwrite/force flag equivalent.
- **Build fails DTD validation** — almost always a leftover internal attribute (`id`, `created`); re-export through the clean path or strip manually.
- **Git diff shows only whitespace/id churn, no real content** — you exported before saving your UI change, or exported the wrong object; re-verify the edit persisted, then re-export.
- **Smoke test fails after promotion** — bisect: which object imported last before it broke; does reverting just that file restore green locally.

## You are done when

Git has durable XML for everything you changed since Lesson 216, the import log shows real success (not silent skips), and `e2e-smoke.sh` is still green.

## Control note

- **Control:** Config-as-code durability for governance objects.  
- **Owner:** IAM Engineering / Release.  
- **SLA (lab):** Every UI change from 216–242 has a matching `config/` file and passes import.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/248/` — build/import logs, `git diff`, impact note, smoke summary.

## Quick check

1. Which two object types are most likely to soft-fail via MCP export/import? → `IdentityTrigger`, `CertificationDefinition`.  
2. What proves a diff is real, not noise? → Actual content changes (rule logic, workflow step), not just id/timestamp churn.  
3. What must you re-run after promotion to prove nothing broke? → `e2e-smoke.sh` (and `contract-tests.sh` if present).

## Navigate

- Previous: Lesson 247
- Next: Lesson 249
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
