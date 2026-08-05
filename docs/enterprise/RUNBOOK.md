# Enterprise Lab ops runbook

Companion to [`docs/ENTERPRISE-LAB-V2.md`](../ENTERPRISE-LAB-V2.md).

## Start / stop

```bash
./tools/lab/docker/up.sh --enterprise          # full estate
./tools/lab/docker/up.sh                       # Core only
./tools/lab/docker/down.sh                     # stop
./tools/lab/docker/down.sh -v                  # wipe volumes (IIQ DB, LDAP, Samba, Keycloak)
```

Health URLs:

- IIQ `http://localhost:8080/identityiq` — spadmin / admin
- Keycloak `http://localhost:8085/admin/` — admin / admin (lab only; HTTP allowed via `keycloak-http-relax`)
- Employee Portal `http://localhost:8092/`
- HCM mock `http://localhost:8091/hcm/v1/workers`
- Samba LDAP `ldap://localhost:3890` (see `lab-data/enterprise/samba/README.md`)

If admin console shows **HTTPS required**, run:

```bash
docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise run --rm keycloak-http-relax
# or:
docker exec mnb-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://127.0.0.1:8080 --realm master --user admin --password admin
docker exec mnb-keycloak /opt/keycloak/bin/kcadm.sh update realms/master -s sslRequired=NONE
```

## Backup IIQ Postgres

```bash
docker exec mnb-iiq-lab-postgres-1 pg_dump -U identityiq identityiq \
  > "/tmp/iiq-$(date +%Y%m%d).sql"
```

(Container name may vary; `docker compose -f docker-compose.iiq.yml ps` to confirm.)

## Re-seed directories without wiping IIQ

```bash
./tools/lab/enterprise/generate-identity-artifacts.py
# Rebuild OpenLDAP image if LDIF changed, or apply delta LDIFs
./tools/lab/enterprise/seed-enterprise.sh
```

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Samba unhealthy on Apple Silicon | amd64 emulation / DC bootstrap | Wait start_period; check `docker logs mnb-samba-ad`; fall back to OpenLDAP-only login (still meets partial DoD) |
| Keycloak realm empty | Import path / first-boot race | `docker compose … up -d --force-recreate keycloak` with realm volume |
| Portal 503 IdP | Keycloak not ready | Wait health; portal retries discovery |
| HCM workers empty | Mock image stale | `./tools/lab/docker/up.sh --enterprise --rebuild` |
| Seed import fails | IIQ/MCP down | Ensure Core healthy before `seed-enterprise.sh` |

## Import objects that MCP rejects (405)

Some object types (IdentityTrigger, CertificationDefinition) may return HTTP 405 via
`import_sailpoint_object`. Durable XML still lives under `config/`. Import via console:

```bash
# From IIQ container (paths may vary by image)
docker exec -it mnb-identityiq bash -lc 'cd /opt/sailpoint/identityiq && ./iiq console'
# then:
# > import /opt/iiq-lab-data/../config/... 
# Prefer mounting or copying XML, or use SSD ./build.sh + importdynamic (Lesson 101).
```

Preferred promotion path for those objects: export into `config/`, run `./build.sh`, importdynamic
in the target env — same as Lesson 101/108.

## Homelab (optional)

Public Academy/IIQ ([`docs/HOMELAB-CD.md`](../HOMELAB-CD.md)) remains Core-sized. Enterprise profile is **local-first**; do not enable Samba/Keycloak on the thin public Helm chart without a dedicated node pool and secrets plan.
