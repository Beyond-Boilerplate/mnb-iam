# Meridian IIQ verify tools

## CD smoke

```bash
./tools/iiq-verify/assert-mnb-objects.sh local   # or k8s
```

Asserts **`MNB-Rule-Hello-World` only**. Academy apps (`MNB-HR`, …) are **learner-built** in lessons — not pre-seeded by CD.

## Optional local E2E (after you complete Lessons 04–06)

`e2e-hr-slice.sh` assumes **you already created** `MNB-HR`, `Aggregate MNB-HR`, and the Refresh MNB Attributes/Managers tasks in IIQ (or imported your own exports). It is a facilitator/regression aid, not day-1 CD.

```bash
export IIQ_HOME=~/iiq-lab/tomcat/webapps/identityiq SPTARGET=sandbox
# After Lesson 06 objects exist:
SKIP_BUILD=1 ./tools/iiq-verify/e2e-hr-slice.sh
```

Helper Rules under this folder run tasks via `TaskManager.runSync` (console `run` is unreliable when the console process exits).

## Homelab wipe (clean “build it yourself”)

```bash
# Via Actions: Deploy homelab → Run workflow → wipe_mnb_leftovers=true
# Or against a pod:
./tools/iiq-verify/wipe-mnb-leftovers.sh k8s
```

Deletes leftover `MNB-*` apps/tasks/roles/workflows and all identities except `spadmin`. Keeps HelloWorld.
