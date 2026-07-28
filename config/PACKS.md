# Meridian academy — what CD ships vs what learners build

CD / SSB image ships **only** a smoke Rule so homelab import stays healthy:

| In git (CD) | IIQ name | Purpose |
| --- | --- | --- |
| `Rule/MNB-Rule-HelloWorld.xml` | `MNB-Rule-Hello-World` | Deploy smoke / Lesson 03 SSB awareness |

**Everything else** (`MNB-HR`, IT Access, target apps, refresh tasks, roles, LCM, SoD, correlation) is **built by the learner in the lessons**, then optionally exported into the matching `config/<Type>/` folder for promotion practice (Lesson 101+).

## Lab CSV truth (not IIQ objects)

Fixtures stay in [`lab-data/`](../lab-data/). Copy to `~/iiq-lab-data/` before Lesson 04. HR uses a **production-style bank header** — see [`lab-data/reference/hr-column-map.md`](../lab-data/reference/hr-column-map.md).

| Concept | Bank column |
| --- | --- |
| Native ID | `userId` |
| Login | `name` |
| Manager | `managersAssociateID` → manager `userId` |
| Leaver | `inactive=true`, `status=Terminated` |
| LOA | `exceptions=LOA` (still Active) |
| Type | `employeeType` / `userType` |
| Org / job | `departmentName`, `division`, `JobCode`, `costCenter` |

IT dumps still use `employeeId` (= HR `userId` for correlation).

## Learner export targets (after the lesson that creates them)

| Lesson creates | Suggested git path when exporting |
| --- | --- |
| 04 `MNB-HR` | `config/Application/MNB-Application-HR.xml` |
| 05–06 refresh / maps | TaskDefinitions + ObjectConfig notes |
| 09 `MNB-IT-Access` | `config/Application/MNB-Application-IT-Access.xml` |
| 11–14 target apps | `config/Application/MNB-Application-*.xml` |
| 23–24 roles | `config/Bundle/MNB-Bundle-*.xml` |
| 29–31 LCM | `config/Workflow/…`, EmailTemplate |
| 39–40 SoD | `config/Policy/…` |

Env file paths use `%%MNB_*_FILE%%` tokens in `*.target.properties` once you export Applications.

## Verify CD smoke only

```bash
./tools/iiq-verify/assert-mnb-objects.sh local   # HelloWorld only
```
