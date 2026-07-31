# Local Meridian stack (Docker)

**One command** starts Postgres + OpenLDAP + IdentityIQ + Academy + MCP + OpenAPI + Teller,
installs/enables the Meridian plugin, and seeds **MNB-HR** + **MNB-OpenLDAP**:

```bash
./tools/lab/docker/up.sh
# preflight only (fail-fast on occupied ports):
./tools/lab/docker/up.sh --check
# force rebuild images (slower):
./tools/lab/docker/up.sh --rebuild
# start without HR/LDAP IIQ seeding:
./tools/lab/docker/up.sh --skip-seed
# if host MCP/OpenAPI leftovers hold 8765/8766:
./tools/lab/docker/up.sh --kill-host-sidecars
```

By default `up.sh` skips Docker image rebuilds when local images already exist (big speed win), packages the plugin in the background while containers start, and probes IIQ/MCP/Teller/Academy/LDAP in parallel. Use `--rebuild` after Dockerfile or MCP source changes.

Startup **fails fast** if required host ports are taken by something other than this Compose project (`mnb-iiq-lab`). It also verifies `mnb-identityiq` is running and that MCP can resolve `http://identityiq:8080` (avoids the “Name or service not known” seed failure when only host Tomcat is on `:8080`).

| URL | What |
| --- | --- |
| http://localhost:4173/ | Academy lessons + progress + Verify now |
| http://localhost:8080/identityiq | IIQ UI (`spadmin` / `admin`) |
| http://localhost:8765/swagger/ | OpenAPI / Swagger (CORS-safe IIQ proxy) |
| http://127.0.0.1:8766/mcp | IdentityIQ MCP (Bearer `mnb-lab-mcp-key`) |
| http://127.0.0.1:8766/healthz | MCP health |
| http://localhost:4180/ | **Teller** chatbot (pre-baked MCP + OpenRouter) |
| http://localhost:8090/ | **phpLDAPadmin** (browse OpenLDAP; `cn=admin,dc=meridiannb,dc=com` / `admin`) |
| ldap://localhost:389 | **OpenLDAP** (`cn=admin,dc=meridiannb,dc=com` / `admin`) |

Lab CSV files are mounted at `/opt/iiq-lab-data` inside IIQ (from repo `lab-data/`).

From the IIQ container, LDAP host is **`openldap`** (not `localhost`). Connection sheet: [`lab-data/connectors/ldap/README.md`](../../../lab-data/connectors/ldap/README.md).

Override the MCP key with `MCP_API_KEY=…` when running `up.sh` / Compose.

## Stop / wipe

```bash
./tools/lab/docker/down.sh                 # FULL wipe (containers + volumes)
./tools/lab/docker/down.sh --keep-volumes  # stop but keep Postgres / LDAP / MCP data
```

Reload LDAP seed after editing `lab-data/connectors/ldap/mnb-openldap.ldif`:

```bash
./tools/lab/docker/down.sh
./tools/lab/docker/up.sh --rebuild
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
