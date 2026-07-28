# Meridian lesson verify

After each lesson, learners prove the lab matches expected outcomes. **Verify now** talks to the **live IIQ** (local, Docker, or homelab), emits a PASS/FAIL report with gap analysis, and the learn site stores progress only from that live result.

JSON paste / manual report import is **disabled** — you cannot mark a lesson PASS without a successful live check.

## Streamlined public academy (homelab)

https://sailpoint.lmsapp.us/ — **Verify now** calls `/api/verify` on the academy pod, which checks the **in-cluster** IdentityIQ. Lesson 01 only needs the login page; later lessons need objects you built in that shared lab (or use a laptop stack below).

## Streamlined local (IIQ + Academy in Docker)

```bash
./tools/lab/docker/up.sh
# → Academy http://localhost:4173/  |  IIQ http://localhost:8080/identityiq
```

Open a lesson → **Lesson verify** → **Verify now**. Gaps appear immediately; TOC turns green/red.

## Streamlined (Tomcat host — IIQ + Academy)

```bash
./tools/lab/up.sh
# → Academy http://localhost:4173/  |  IIQ http://localhost:8080/identityiq
```

Academy only (IIQ already up): `./tools/lab/up.sh --academy-only`

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

Exit code `0` = PASS, `1` = FAIL. JSON report (for your evidence folder only):

`~/iiq-lab-evidence/verify/lesson-04.json`

Progress on the learn site updates only via **Verify now** against a running Academy server.

## How checks run

| Layer | Use |
| --- | --- |
| HTTP | Login page / health |
| **SCIM** `/scim/v2/Users` | Identity exists / attrs when module enabled |
| **REST** `/rest/identities/…` | Probe when present |
| **iiq console** | Authoritative fallback for Applications, TaskDefinitions, Populations, counts |
| Host files | Repo / `~/iiq-lab-data` fixtures when the lesson is paper + lab-data |

Transports used are listed in the report (`transport: ["scim","console-local",…]`).

## Specs

Per-lesson JSON under [`tools/iiq-verify/lesson-specs/`](../tools/iiq-verify/lesson-specs/) for **all 110 lessons**.

Check types: `http.ok`, `host.file.exists`, `object.exists` (optional `softFail`), `object.absent`, `identity.exists`, `identity.countMin`, `identity.attr`.

Regenerate curated specs (does not overwrite 01–10 unless `--all`):

```bash
python3 tools/iiq-verify/generate_lesson_specs.py --overwrite
```

## Local lab paths

| Runtime | Setup | Verify mode |
| --- | --- | --- |
| Tomcat + MySQL | [`docs/LOCAL_SETUP.md`](LOCAL_SETUP.md) / `./tools/lab/up.sh` | `local` (auto) |
| Docker + Postgres | [`tools/lab/docker/README.md`](../tools/lab/docker/README.md) | `docker` |
| Homelab k8s | [`docs/HOMELAB-CD.md`](HOMELAB-CD.md) | `k8s` |

Curriculum objects are **learner-built**; CD only ships HelloWorld.
