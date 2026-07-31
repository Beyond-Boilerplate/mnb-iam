# Local Meridian stack (Docker)

**One command** starts Postgres + OpenLDAP + IdentityIQ + Academy + MCP + OpenAPI docs:

```bash
./tools/lab/docker/up.sh
```

| URL | What |
| --- | --- |
| http://localhost:4173/ | Academy lessons + progress + Verify now |
| http://localhost:8080/identityiq | IIQ UI (`spadmin` / `admin`) |
| http://localhost:8765/swagger/ | OpenAPI / Swagger (CORS-safe IIQ proxy) |
| http://127.0.0.1:8766/mcp | IdentityIQ MCP (Bearer `mnb-lab-mcp-key`) |
| http://127.0.0.1:8766/healthz | MCP health |
| http://localhost:4180/ | **Teller** chatbot (pre-baked MCP + OpenRouter) |
| ldap://localhost:389 | **OpenLDAP** (`cn=admin,dc=meridiannb,dc=com` / `admin`) |

Lab CSV files are mounted at `/opt/iiq-lab-data` inside IIQ (from repo `lab-data/`).

From the IIQ container, LDAP host is **`openldap`** (not `localhost`). Connection sheet: [`lab-data/connectors/ldap/README.md`](../../../lab-data/connectors/ldap/README.md).

Override the MCP key with `MCP_API_KEY=…` when running `up.sh` / Compose.

## Stop / wipe

```bash
./tools/lab/docker/down.sh          # keep DB + LDAP volumes
./tools/lab/docker/down.sh -v       # wipe Postgres + MCP audit + OpenLDAP volumes
```

Reload LDAP seed after editing `lab-data/connectors/ldap/mnb-openldap.ldif`:

```bash
docker compose -f docker-compose.iiq.yml build openldap
docker compose -f docker-compose.iiq.yml stop openldap
docker volume rm mnb-iiq-lab_mnb-openldap-data mnb-iiq-lab_mnb-openldap-config
docker compose -f docker-compose.iiq.yml up -d openldap
```

## Image notes

- IIQ defaults to `ghcr.io/beyond-boilerplate/identityiq:0.1.0` (or `IIQ_IMAGE=mnb-identityiq:local` if you built it).
- Academy builds from `docker/Dockerfile.academy` on first `up`.
- MCP builds from `docker/Dockerfile.mcp`; OpenAPI from `docker/Dockerfile.api-docs`; Teller from `docker/Dockerfile.chat`.
- Free-text chat needs `OPENROUTER_API_KEY` in the environment (pre-baked teller buttons work without it).
- Verify uses HTTP/SCIM when available and `docker exec` into `mnb-identityiq` for object checks (docker.sock mounted on academy).

## Cursor / Claude MCP

```bash
# after ./tools/lab/docker/up.sh
claude mcp add --scope user --transport http identityiq http://127.0.0.1:8766/mcp \
  --header "Authorization: Bearer mnb-lab-mcp-key"
```

## Optional JDBC sample

Sample JDBC Postgres (host port **5434**, avoids clashing with lab Postgres on 5433):

```bash
docker compose -f docker-compose.connectors.yml up -d jdbc-pg
```

## Alternative: Tomcat on the host

```bash
./tools/lab/up.sh               # Tomcat IIQ + OpenAPI + MCP + Academy
docker compose -f docker-compose.connectors.yml up -d openldap   # LDAP for host IIQ
```

See [`docs/LOCAL_SETUP.md`](../../../docs/LOCAL_SETUP.md) and [`docs/LESSON_VERIFY.md`](../../../docs/LESSON_VERIFY.md).
