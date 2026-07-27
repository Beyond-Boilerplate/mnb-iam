# Meridian HR E2E verification (local)

## What it proves

1. SSB `importdynamic` lands academy packs from `config/`
2. `assert-mnb-objects.sh` allowlist passes
3. `Aggregate MNB-HR` creates cubes from the **bank-style** `HRApplications.txt` (52 columns)
4. `Refresh MNB Attributes` / `Refresh MNB Managers` complete successfully
5. Personas exist with `MNB-HR` links (`helen.ross`, `priya.wire`, `samir.hassan` terminated, `sofia.torres` `exceptions=LOA`)

## Run

```bash
# One-time: point sandbox tokens at your machine (already set for this workstation)
# %%MNB_HR_FILE%%=/Users/<you>/iiq-lab-data/HRApplications.txt

export IIQ_HOME=~/iiq-lab/tomcat/webapps/identityiq
export SPTARGET=sandbox
./tools/iiq-verify/e2e-hr-slice.sh

# Faster re-run after objects already imported:
SKIP_BUILD=1 ./tools/iiq-verify/e2e-hr-slice.sh
```

## Live result (2026-07-27, local Tomcat)

| Step | Result |
| --- | --- |
| `./build.sh importdynamic` | All 25 MNB objects imported |
| Assert allowlist | **PASS** (21 named objects) |
| Aggregate MNB-HR | **PASS** — 80 HR identities + `spadmin` (count Identity = 81) |
| File path on app | `/Users/alishaghatane/iiq-lab-data/HRApplications.txt` |
| Native identity | `userId` / cube name from `name` (`priya.wire`, …) |
| Link attrs | Full bank header present (`JobCode`, `departmentName`, `managersAssociateID`, `exceptions=LOA`, `inactive=true` for Samir) |
| Refresh attrs/managers | **PASS** (`OK … Success` via sync helper rules) |

### Known follow-up (not a Phase-1 blocker)

Identity **Attributes** map still shows mostly `displayName` until Lesson 05 identity attribute maps / ObjectConfig promote Link → Identity. Cube **creation** and Link truth already validate the HR vertical slice.

Console `run "Task"` is unreliable here (Quartz shuts down when the console process exits). E2E uses sync `TaskManager.runSync` via helper Rules under `tools/iiq-verify/`.
