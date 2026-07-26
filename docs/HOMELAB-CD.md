# Homelab CD — Meridian IdentityIQ (`mnb-iam`)

Public URL: **https://sailpoint.lmsapp.us/identityiq/login.jsf**  
Namespace: **`sailpoint`** (isolated from `platform`)  
Pattern: same Tailscale + Helm + GHCR flow as [nepaledu-platform](https://github.com/Beyond-Boilerplate/nepaledu-platform).

## What is CNPG?

**CloudNativePG** runs PostgreSQL in-cluster (`sailpoint-pg`). It is deploy-time only — it does **not** make GitHub Actions image builds slow.

## Fast image pipeline

Routine publishes no longer expand the ~708MB GA zip. Two images:

| Image | When to rebuild | Target time |
|-------|-----------------|-------------|
| `identityiq-base:8.5` | Rare — GA / `Dockerfile.base` / JDBC jar | ~10–15 min OK |
| `identityiq:{VERSION,sha}` | Every `config/` `src/` `web/` change | **≤ 3 min** |

```text
rare:   oras pull mnb-iam-ga:8.5 → docker build Dockerfile.base → identityiq-base:8.5
often:  FROM identityiq-base → SSB overlay (no GA expand) → identityiq:{tag}
        → Tailscale + Helm -n sailpoint
        → smoke https://sailpoint.lmsapp.us/identityiq/login.jsf
```

Nodes keep the large **base** layers cached; app deploys pull thin overlay layers.

| Workflow | Purpose |
|----------|---------|
| `publish-ga-oci.yml` | One-time / rare: GA zip → OCI artifact |
| `publish-base.yml` | Rare: GA expand + JDBC → `identityiq-base:8.5` |
| `publish-ghcr.yml` | Frequent: thin app image FROM base |
| `deploy-homelab.yml` | Helm upgrade + public smoke |
| `ssb-ci.yml` | PR/develop full war; **skipped on main** when Publish covers same paths |

### Rebuild rules

- Change **GA or JDBC or `docker/Dockerfile.base`** → run **Publish IIQ base image**, then Publish GHCR (or push app files).
- Change **config / src / web / entrypoint** only → Publish GHCR only (thin).
- Do **not** expect a full GA expand on every app commit.

## One-time setup

1. **Publish GA** (do not commit the zip if avoidable):

   ```bash
   docker login ghcr.io -u sardul3
   ./.github/scripts/publish-ga-oci.sh 8.5
   ```

   Already published: `ghcr.io/beyond-boilerplate/mnb-iam-ga:8.5` (private).

   CI pulls via repo secrets `GHCR_READ_TOKEN` + `GHCR_USERNAME` (PAT with `read:packages`).
   Longer-term: Package settings → **Manage Actions access** → add `Beyond-Boilerplate/mnb-iam` (Read),
   then CI can use `GITHUB_TOKEN` alone.

2. **Publish base image once** (Actions → **Publish IIQ base image** → Run), or:

   ```bash
   # after GA is in GHCR and Dockerfile.base is on main
   gh workflow run "Publish IIQ base image" --repo Beyond-Boilerplate/mnb-iam
   ```

3. **GitHub Environments / secrets** on `mnb-iam` (same values as `nepaledu-platform` repo secrets):
   - Environment **`homelab`**
   - `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET`, `HOMELAB_KUBECONFIG`
   - `GHCR_READ_TOKEN`, `GHCR_USERNAME`
   - Optional: `GHCR_PULL_TOKEN` for cluster pulls if images stay private

   Then: **Actions → Deploy homelab → Run workflow**.

4. **Cluster**
   - CNPG operator already installed (same as LMS)
   - `ghcr-pull` docker-registry secret in `sailpoint` (deploy workflow can create it)

5. **Cloudflare Tunnel** public hostname (no Access for now):

   | Field | Value |
   |-------|--------|
   | Subdomain | `sailpoint` |
   | Domain | `lmsapp.us` |
   | Type | HTTP |
   | URL | `identityiq.sailpoint.svc.cluster.local:8080` |

6. **Helm install (manual)**

   ```bash
   export KUBECONFIG=…
   export IMAGE_TAG=0.1.0
   ./deploy/helm/scripts/install-sailpoint.sh deploy/helm/values/local-homelab.yaml
   ```

## Runtime shape

- **Phased Helm install**: data (CNPG + schema) then app
- **CNPG**: 1 instance in lab values (no hard anti-affinity); storage stays at provisioned size (cannot shrink)
- **2 IdentityIQ replicas**, Service `sessionAffinity: ClientIP`; readiness **TCP:8080** (smoke still hits login.jsf)
- Schema Job applies SailPoint Postgres DDL once (skip if `spt_identity` exists)
- DB credentials: Secret `sailpoint-iiq-db`

## Notes

- IIQ 8.5 supports PostgreSQL; JDBC jar is baked into `identityiq-base` (`web/WEB-INF/lib/postgresql-42.7.4.jar`).
- Shared IIQ filesystem is not PVC-shared on typical k3s RWO.
- Default login after first successful schema + boot: `spadmin` / `admin` (change immediately in any shared lab).
- Routine Publish uses `cancel-in-progress: true`; provenance/SBOM only on SemVer bumps via workflow_dispatch.
