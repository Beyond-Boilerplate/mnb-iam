# Lesson 244 — QuickLinks That Operators Use

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~40 minutes  
**Prereq:** Lesson 212  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 95

> **Why:** If it takes seven clicks, nobody opens it. An operator who avoids the platform because every task is buried three menus deep is a control gap, not a training issue.

## What this is

QuickLinks are the tiles on an IIQ user's Home page. This estate has real destinations worth one-click access to: Request Access, My Certifications, and — because this is the Enterprise stack — external systems like Mailpit and Gitea that a helpdesk operator checks constantly. You audit what Helen currently sees, add an external link, remove one that's broken, then prove from her logged-in session that every tile works.

## Know these

| Object | Role |
| --- | --- |
| `QuickLink` | The tile definition |
| Granting population/DynamicScope | What makes a tile appear for a given identity |
| External QuickLink | Points at a raw URL (Mailpit, Gitea) instead of an internal IIQ screen |

**Wrong way:** Leaving a QuickLink pointed at a population or object that was renamed/removed in an earlier lesson — it silently hides or 404s instead of failing loudly.

## Intent

- Confirm which `QuickLink` objects currently render on Helen's Home page.
- Add an external QuickLink pointing at Mailpit and/or Gitea.
- Use Request Access and Certifications as Helen through the tiles, not the menu.
- Remove or fix any QuickLink referencing a DynamicScope or population that no longer resolves.

## Before you start

- [ ] Lesson 212 Portal/SSO proof done
- [ ] `helen.ross` / `LabUser1!` credentials on hand
- [ ] Mailpit (`:8025`) and Gitea (`:8093`) reachable
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/244`

## Do this

1. Log in as `helen.ross` / `LabUser1!` at `http://localhost:8080/identityiq/`. List every QuickLink tile on her Home page.  
   **Expect:** A concrete list you can cross-check.
2. As `spadmin`, **Setup → QuickLinks** (or **Global Settings → QuickLink Configuration**), cross-check that list.  
   **Expect:** Every tile Helen sees traces to a specific `QuickLink` object and its granting population/capability.
3. Add a new **External QuickLink** named `Mailpit` → `http://localhost:8025`, and `Gitea` → `http://localhost:8093`. Scope both to Helen's population (e.g. `MNB-Employees`).  
   **Expect:** Both save with correct URLs and scope.
4. Refresh Helen's Home page.  
   **Expect:** Both new tiles appear and open the correct services in a new tab.
5. Click **Request Access** and **Certifications** from the tiles.  
   **Expect:** Same working screens as Lessons 221–222 and 226 — a 404 or blank target is a broken reference, not something to work around.
6. Audit every QuickLink's population/DynamicScope binding for a still-existing object.  
   **Expect:** Remove or repoint anything that doesn't resolve.
7. Re-confirm Helen's Home page after cleanup.  
   **Expect:** Every tile she sees works; nothing that should be there is missing.
8. Save a screenshot of Helen's final Home page tile set under `~/iiq-lab-evidence/sandbox/244/`.

## If it fails

- **External QuickLink shows but does nothing on click** — confirm the URL is full `http://`, not relative, and the port is reachable from your Mac browser (8025, 8093), not just the Docker network.
- **New tile never appears for Helen** — check the granting population/DynamicScope actually includes her identity; a typo'd population name silently grants to nobody.
- **A previously-working tile now 404s** — likely a QuickLink referencing an object renamed/removed in Lesson 242/243 — repoint to the current object name.

## You are done when

Helen reaches Request Access, Certifications, Mailpit, and Gitea from Home page tiles, and no broken QuickLink remains for her population.

## Control note

- **Control:** Operator self-service usability (one-click access to daily tools).  
- **Owner:** IAM Engineering + Helpdesk Ops.  
- **SLA (lab):** No broken/mystery tiles on an active persona's Home page.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/244/` — Helen's final tile screenshot.

## Quick check

1. What makes a tile appear for a specific identity? → Its granting population/DynamicScope.  
2. What's the difference between an internal and external QuickLink? → External points at a raw URL, not an internal IIQ screen.  
3. Why audit stale references instead of assuming tiles still work? → A renamed/removed object silently hides or 404s a tile.

## Navigate

- Previous: Lesson 243
- Next: Lesson 245
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
