# Meridian IIQ verify tools

## Lesson pass/fail (learners)

```bash
./tools/iiq-verify/verify-lesson.sh 04
```

- Specs: [`lesson-specs/`](lesson-specs/) (01–10 today)
- Report: `~/iiq-lab-evidence/verify/lesson-NN.json`
- Docs: [`docs/LESSON_VERIFY.md`](../../docs/LESSON_VERIFY.md)
- Prefer **SCIM/REST** when enabled; **iiq console** fallback for Applications/Tasks
- Modes: `local` (default), `docker`, `k8s`

Paste the JSON into the learn site **Lesson verify** panel to track progress (browser localStorage only — no submission upload).

## CD smoke

```bash
./tools/iiq-verify/assert-mnb-objects.sh local   # or k8s
```

Asserts **`MNB-Rule-Hello-World` only**. Academy apps are learner-built.

## Optional E2E / wipe

See `e2e-hr-slice.sh` (after Lessons 04–06 objects exist) and `wipe-mnb-leftovers.sh` for clean UI-first labs.
