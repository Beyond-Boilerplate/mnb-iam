# Meridian lesson verify

After each lesson, learners prove the lab matches expected outcomes. The CLI talks to the **live IIQ** (local by default, or Docker / homelab CD), emits a **PASS/FAIL** report with **gap analysis**, and the learn site can store progress in the browser (no submission server required).

## Streamlined local (learn UI + Verify now)

```bash
# IIQ must already be up (Tomcat lab or Docker)
./tools/lab/start-academy.sh
# → http://localhost:4173/  (lessons + progress + Verify now button)
```

Open a lesson → scroll to **Lesson verify** → **Verify now**. Gaps appear immediately; TOC turns green/red.

## Quick start (CLI)


```bash
# Local Tomcat lab (default)
export IIQ_BASE_URL=http://localhost:8080/identityiq
export IIQ_USER=spadmin IIQ_PASSWORD=admin
./tools/iiq-verify/verify-lesson.sh 04

# Docker lab
export IIQ_VERIFY_MODE=docker
./tools/iiq-verify/verify-lesson.sh 04

# Homelab / CD (when Tailscale + kubectl available)
export IIQ_BASE_URL=https://sailpoint.lmsapp.us/identityiq
export IIQ_VERIFY_MODE=k8s
./tools/iiq-verify/verify-lesson.sh 04
```

Exit code `0` = PASS, `1` = FAIL. JSON report:

`~/iiq-lab-evidence/verify/lesson-04.json`

Paste that JSON into the **Lesson verify** panel on the learn site page to mark progress (localStorage only).

## How checks run

| Layer | Use |
| --- | --- |
| HTTP | Login page / health |
| **SCIM** `/scim/v2/Users` | Identity exists / attrs when module enabled |
| **REST** `/rest/identities/…` | Probe when present |
| **iiq console** | Authoritative fallback for Applications, TaskDefinitions, Populations, counts |

Transports used are listed in the report (`transport: ["scim","console-local",…]`).

## Specs

Per-lesson JSON under [`tools/iiq-verify/lesson-specs/`](../tools/iiq-verify/lesson-specs/). Foundations **01–10** ship first; add `{NN}-{stem}.json` for later lessons using the same schema.

Check types: `http.ok`, `host.file.exists`, `object.exists`, `object.absent`, `identity.exists`, `identity.countMin`, `identity.attr`.

## Local lab paths

| Runtime | Setup | Verify mode |
| --- | --- | --- |
| Tomcat + MySQL | [`docs/LOCAL_SETUP.md`](LOCAL_SETUP.md) / `./tools/lab/setup-local.sh` | `local` (auto) |
| Docker + Postgres | [`tools/lab/docker/README.md`](../tools/lab/docker/README.md) | `docker` |
| Homelab k8s | [`docs/HOMELAB-CD.md`](HOMELAB-CD.md) | `k8s` |

Both local options stay supported. Curriculum objects are **learner-built**; CD only ships HelloWorld smoke.
