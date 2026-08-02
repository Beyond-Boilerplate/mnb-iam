# Meridian JDBC lab backend (`jdbc-pg`)

Postgres sample app DB for Lessons **63–64** (`MNB-CoreBanking-JDBC`).

## Start

Included with the main Meridian Docker stack (`./tools/lab/docker/up.sh`) as service **`jdbc-pg`**.

Standalone:

```bash
docker compose -f docker-compose.connectors.yml up -d jdbc-pg
```

## Connection sheet

| From | Host | Port | Database | User / password |
| --- | --- | --- | --- | --- |
| Host tools / Tomcat on laptop | `localhost` | **5435** | `mnb_apps` | `mnb` / `mnb` |
| IIQ container (main stack) | `jdbc-pg` | `5432` | `mnb_apps` | `mnb` / `mnb` |

```text
jdbc:postgresql://localhost:5435/mnb_apps          # host IIQ / psql from Mac
jdbc:postgresql://jdbc-pg:5432/mnb_apps            # IIQ inside docker-compose.iiq.yml
jdbc:postgresql://host.docker.internal:5435/mnb_apps  # IIQ container → host-published port
```

**Do not** use host port **5433** — that is the IdentityIQ database (`postgres` service), not `mnb_apps`.

Default host port is **5435** (avoids IIQ `:5433` and a common second Postgres on `:5434`). Override with `JDBC_PG_PORT=…` if needed.

## Seed

`mnb_core_accounts.sql` creates tables and seeds 4 accounts (Priya, Marcus, Jordan, Samir DISABLED) + entitlement dictionary. Applied only on **first** volume init.

```bash
psql "postgresql://mnb:mnb@localhost:5435/mnb_apps" -c \
  'SELECT account_id, username, status, entitlement FROM mnb_app_accounts ORDER BY 1;'
```

Reload seed after wipe:

```bash
docker compose -f docker-compose.iiq.yml rm -sf jdbc-pg
docker volume rm "$(basename "$(pwd)")_mnb-jdbc-pg" 2>/dev/null || true
# or connectors compose volume mnb-connectors-jdbc-pg
docker compose -f docker-compose.iiq.yml up -d jdbc-pg
```

Truth CSV (same rows): [`sample-rows.csv`](sample-rows.csv).
