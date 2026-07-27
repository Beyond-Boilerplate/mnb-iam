# Homelab CD — Meridian IdentityIQ (`mnb-iam`)

Public URLs:

| Surface | URL |
| --- | --- |
| **Academy (home)** | **https://sailpoint.lmsapp.us/** |
| IdentityIQ | **https://sailpoint.lmsapp.us/identityiq/login.jsf** |

Namespace: **`sailpoint`** (isolated from `platform`)  
Pattern: same Tailscale + Helm + GHCR flow as [nepaledu-platform](https://github.com/Beyond-Boilerplate/nepaledu-platform).

Path split is handled in-cluster by **`sailpoint-edge`** (nginx). Cloudflare Tunnel must target the edge, not IdentityIQ directly.

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
| `publish-ghcr.yml` | Frequent: thin app image FROM base; calls deploy with the exact SHA tag |
| `deploy-homelab.yml` | Helm upgrade + in-cluster and public smoke |
| `ci-quality.yml` | Workflow, shell, Helm, Python, and academy validation |

### When Deploy runs (automatic)

| Trigger | `IMAGE_TAG` |
|---------|-------------|
| Push to `main` touching `deploy/**` or this workflow | Live tag on cluster (else `VERSION`) |
| Successful **Publish GHCR images** on `main` (reusable workflow call) | Exact short SHA emitted by the publisher |
| Manual **Run workflow** | Optional input; empty → live / `VERSION` |

Helm-only fixes (probes, values, install scripts) no longer require a manual dispatch.

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
   - Recommended: `GHCR_PULL_TOKEN` for cluster pulls if images stay private

   Cluster pulls must use a long-lived `read:packages` token. CI never stores its
   short-lived `GITHUB_TOKEN` in Kubernetes. If no token is supplied, deployment
   preserves an existing `ghcr-pull` secret and fails clearly when none exists.

   Then first deploy: **Actions → Deploy homelab → Run workflow** (or push any change under `deploy/`).

4. **Cluster**
   - CNPG operator already installed (same as LMS)
   - `ghcr-pull` docker-registry secret in `sailpoint` (deploy workflow can create it)

5. **Cloudflare Tunnel** public hostname (no Access for now):

   | Field | Value |
   |-------|--------|
   | Subdomain | `sailpoint` |
   | Domain | `lmsapp.us` |
   | Type | HTTP |
   | URL | `sailpoint-edge.sailpoint.svc.cluster.local:8080` |

   Routes: `/` → academy (`mnb-learn`), `/identityiq` → IdentityIQ. See [LEARN-SITE.md](LEARN-SITE.md).

6. **Public surface (academy + edge)**

   ```bash
   ./learn/k8s/install-public-surface.sh
   # or: Actions → Publish learn site
   ```

7. **Helm install (manual)**

   ```bash
   export KUBECONFIG=…
   export IMAGE_TAG=0.1.0
   ./deploy/helm/scripts/install-sailpoint.sh deploy/helm/values/local-homelab.yaml
   ```

## Runtime shape

- **Phased Helm install**: data (CNPG + schema) then app
- **Public edge**: `sailpoint-edge` path-routes academy (`/`) and IIQ (`/identityiq`)
- **CNPG**: 1 instance in lab values (no hard anti-affinity); storage stays at provisioned size (cannot shrink)
- **1 IdentityIQ replica** (lab speed; set `replicaCount: 2` for HA demos), Service `sessionAffinity: ClientIP`; startup/readiness check the real `/identityiq/login.jsf` route
- Schema Job applies SailPoint Postgres DDL once (skip if `spt_identity` exists)
- DB credentials: Secret `sailpoint-iiq-db`

## Notes

- IIQ 8.5 supports PostgreSQL; JDBC jar is baked into `identityiq-base` (`web/WEB-INF/lib/postgresql-42.7.4.jar`).
- Shared IIQ filesystem is not PVC-shared on typical k3s RWO.
- Default login after first successful schema + boot: `spadmin` / `admin` (change immediately in any shared lab).
- Image publishing cancels superseded builds. Cluster-mutating workflows share one
  non-cancelling concurrency lock, so Helm and academy rollouts cannot race.
- Public smoke is bounded to roughly 90 seconds per route and reports tunnel
  misrouting separately from an unavailable IdentityIQ upstream.
- Release tags are immutable; the pipeline refuses to force-update an existing tag.
