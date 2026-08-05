# Lesson 245 — Workgroups, Capabilities, Scopes

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lesson 206  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 96

> **Why:** Least privilege inside IIQ matters like on targets. A real bank never gives every certifier `SystemAdministrator` — prove reduced privilege, don't assume it.

## What this is

Everything so far ran as `spadmin` or a full-capability persona. IIQ's **Workgroup** (a named group an identity inherits capabilities/scopes from), **Capability** (a bundle of rights like `CertificationAdministrator`), and **Scope** (a data-partitioning boundary) together let you build a reduced-privilege certifier and prove — not assume — what they can and can't reach.

## Know these

| Object | Role |
| --- | --- |
| Workgroup | Grants capabilities to members indirectly (not a direct assignment) |
| Capability | Bundle of rights, e.g. `Certification Administrator` |
| Scope | Data-partitioning boundary (e.g. only Treasury identities) |

**Wrong way:** Granting a capability directly on an identity "just to test something" and forgetting to remove it — direct grants stack with workgroup grants and don't get cleaned up when you leave the workgroup.

## Intent

- Create a workgroup carrying only certifier-level capabilities, not full admin rights.
- Add `priya.wire` to it and confirm her effective capabilities came from the workgroup, not a direct grant.
- Scope a certification to a population if the certifier should only ever see part of the org.
- Prove Priya cannot open an `spadmin`-only screen even though she can certify.

## Before you start

- [ ] Lesson 206 login/capability model understood
- [ ] `priya.wire` / `LabUser1!` credentials on hand
- [ ] `spadmin` access for setup
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/245`

## Do this

1. **Setup → Workgroups → New Workgroup**, name `MNB-WG-Wire-Owners`. Under **Capabilities**, add `Certification Administrator` only — no `SystemAdministrator`/`Full Access`.  
   **Expect:** Workgroup saves with exactly one capability.
2. Add `priya.wire` as a member. Save.  
   **Expect:** Membership recorded.
3. Log in as `priya.wire` / `LabUser1!`.  
   **Expect:** **Certifications** now visible in nav, inherited from the workgroup.
4. Attempt to open an admin-only screen directly, e.g. `http://localhost:8080/identityiq/system/globalSettings.jsf` or **Setup → Global Settings**.  
   **Expect:** Access-denied page, or the menu option isn't rendered — proof workgroup capabilities are additive and scoped, not a backdoor.
5. Back as `spadmin`, **Setup → Workgroups → MNB-WG-Wire-Owners → Members**, check Priya's capabilities tab.  
   **Expect:** Certifier right shows as *inherited from workgroup*, not a direct assignment — removing her from the workgroup later removes it cleanly.
6. If certification volume should be scoped (e.g. Priya only certifies Commercial Banking), create/reuse a **Scope** for that population and set it on the workgroup or the certification definition.  
   **Expect:** Scope attached.
7. Launch a small Targeted Certification as Priya scoped to that population.  
   **Expect:** Identities she sees are limited to the scope, not the full org.
8. Save a screenshot of Priya's denied admin screen, her inherited-capability tab, and the scoped cert row count under `~/iiq-lab-evidence/sandbox/245/`.

## If it fails

- **Priya still can't see Certifications after joining the workgroup** — capability inheritance sometimes needs a session refresh; log out/in, or force a Refresh Identity Cube if capabilities are cube-cached.
- **Priya can open the admin screen anyway** — check she wasn't already granted `SystemAdministrator` directly in an earlier lesson; direct grants stack with workgroup grants — audit her identity's own Capabilities tab too.
- **Scope doesn't restrict the certification** — confirm the scope is attached at the certification definition level, not just defined and unused.

## You are done when

Priya can certify through her workgroup-inherited capability but is denied an admin-only screen, and any scoped certification she runs is limited to the intended population.

## Control note

- **Control:** Least-privilege certifier model (workgroup-inherited, not direct-granted).  
- **Owner:** IAM Engineering + Access Governance.  
- **SLA (lab):** No certifier persona holds `SystemAdministrator` unless explicitly justified.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/245/` — denied screen, inherited-capability tab, scoped cert count.

## Quick check

1. Why prefer workgroup-inherited capabilities over direct grants? → Removing from the workgroup cleanly removes the right; direct grants can be forgotten.  
2. What blocks Priya from `Global Settings` even with a certifier capability? → Capabilities are additive/scoped, not a backdoor to full admin.  
3. What restricts which identities a certifier sees? → A `Scope` attached to the certification definition or workgroup.

## Navigate

- Previous: Lesson 244
- Next: Lesson 246
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
