# Meridian IIQ verify tools

## Lesson pass/fail (learners)

```bash
./tools/iiq-verify/verify-lesson.sh 04
```

- Specs: [`lesson-specs/`](lesson-specs/) — **all 110 lessons**
- Report: `~/iiq-lab-evidence/verify/lesson-NN.json` (evidence only)
- Docs: [`docs/LESSON_VERIFY.md`](../../docs/LESSON_VERIFY.md)
- Prefer **SCIM/REST** when enabled; **iiq console** fallback for Applications/Tasks
- Modes: `local` (default), `docker`, `k8s`

Track progress in the Academy UI with **Verify now** (live IIQ) for lab lessons. Pasting JSON cannot mark a lesson PASS.

**Paperwork / design lessons** (`verifyMode: paperwork` in the spec) disable live checks — use **Mark binder complete** in the Academy (or CLI, which returns PASS with a paperwork note).

```bash
./tools/lab/up.sh            # Tomcat + Academy
# or
./tools/lab/docker/up.sh     # Docker IIQ + Academy
```

## CD smoke

```bash
./tools/iiq-verify/assert-mnb-objects.sh local   # or k8s
```

Asserts **`MNB-Rule-Hello-World` only**. Academy apps are learner-built.

## Optional E2E / wipe

See `e2e-hr-slice.sh` (after Lessons 04–06 objects exist) and `wipe-mnb-leftovers.sh` for clean UI-first labs.

## Regenerating specs

```bash
python3 tools/iiq-verify/generate_lesson_specs.py --overwrite
```
