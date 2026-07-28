# Local Meridian stack (Docker)

**One command** starts Postgres + IdentityIQ + Academy (lessons + **Verify now**):

```bash
./tools/lab/docker/up.sh
```

| URL | What |
| --- | --- |
| http://localhost:4173/ | Academy lessons + progress + Verify now |
| http://localhost:8080/identityiq | IIQ UI (`spadmin` / `admin`) |

Lab CSV files are mounted at `/opt/iiq-lab-data` inside IIQ (from repo `lab-data/`).

## Stop / wipe

```bash
./tools/lab/docker/down.sh          # keep DB volume
./tools/lab/docker/down.sh -v       # wipe Postgres too
```

## Image notes

- IIQ defaults to `ghcr.io/beyond-boilerplate/identityiq:0.1.0` (or `IIQ_IMAGE=mnb-identityiq:local` if you built it).
- Academy builds from `docker/Dockerfile.academy` on first `up`.
- Verify uses HTTP/SCIM when available and `docker exec` into `mnb-identityiq` for object checks (docker.sock mounted on academy).

## Alternative: Tomcat on the host

```bash
./tools/lab/setup-local.sh
./tools/lab/start-academy.sh    # Academy only; uses host IIQ
```

See [`docs/LOCAL_SETUP.md`](../../../docs/LOCAL_SETUP.md) and [`docs/LESSON_VERIFY.md`](../../../docs/LESSON_VERIFY.md).
