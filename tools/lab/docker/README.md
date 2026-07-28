# Local IIQ via Docker

Alternative to the host Tomcat + MySQL path in [`tools/lab/README.md`](../README.md).

| Path | When to use |
| --- | --- |
| **Docker** (`docker-compose.iiq.yml`) | Prefer containers; Postgres; matches homelab image shape |
| **Tomcat lab** (`./tools/lab/setup-local.sh`) | Prefer native macOS/Windows tools; MySQL on :3307 |

Both use the same curriculum, `lab-data/`, and `./tools/iiq-verify/verify-lesson.sh`.

## Quick start

```bash
# Optional: build from this repo (needs GHCR base pull or local base)
# docker build -f docker/Dockerfile -t mnb-identityiq:local .
# export IIQ_IMAGE=mnb-identityiq:local

./tools/lab/docker/up.sh
./tools/lab/docker/bootstrap.sh
open http://localhost:8080/identityiq   # spadmin / admin

# Point file paths in UI at /opt/iiq-lab-data/... (volume-mounted from repo lab-data/)
```

Tear down:

```bash
./tools/lab/docker/down.sh          # keep DB volume
./tools/lab/docker/down.sh -v       # wipe Postgres volume too
```

## Verify lessons

```bash
export IIQ_BASE_URL=http://localhost:8080/identityiq
export IIQ_USER=spadmin IIQ_PASSWORD=admin
./tools/iiq-verify/verify-lesson.sh 04
```

See [`docs/LESSON_VERIFY.md`](../../../docs/LESSON_VERIFY.md).
