# Homelab CD — Meridian IdentityIQ (`mnb-iam`)

Public URL: **https://sailpoint.lmsapp.us/identityiq/login.jsf**  
Namespace: **`sailpoint`** (isolated from `platform`)  
Pattern: same Tailscale + Helm + GHCR flow as [nepaledu-platform](https://github.com/Beyond-Boilerplate/nepaledu-platform).

## Pipeline

```text
push main
  → oras pull  ghcr.io/beyond-boilerplate/mnb-iam-ga:8.5  → base/ga/
  → docker build (SSB clean war, SPTARGET=homelab)
  → push        ghcr.io/beyond-boilerplate/identityiq:{VERSION,sha7,latest}
  → Tailscale + Helm -n sailpoint
  → smoke       https://sailpoint.lmsapp.us/identityiq/login.jsf
```

| Workflow | Purpose |
|----------|---------|
| `publish-ga-oci.yml` | One-time / rare: GA zip → OCI artifact |
| `publish-ghcr.yml` | Build & push IdentityIQ app image |
| `deploy-homelab.yml` | Helm upgrade + public smoke |
| `ssb-ci.yml` | PR/CI war build (pulls GA from OCI when zip absent) |

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

2. **GitHub Environments / secrets** on `mnb-iam` (same values as `nepaledu-platform` repo secrets):
   - Create Environment **`homelab`** (already present)
   - Copy from nepaledu-platform → mnb-iam (Settings → Secrets and variables → Actions):
     - `TS_OAUTH_CLIENT_ID`
     - `TS_OAUTH_SECRET`
     - `HOMELAB_KUBECONFIG`
   - Already set for GA pulls: `GHCR_READ_TOKEN`, `GHCR_USERNAME`
   - Optional: `GHCR_PULL_TOKEN` for cluster pulls if images stay private

   After secrets are in place: **Actions → Deploy homelab → Run workflow** (or re-run the failed `workflow_run`).


3. **Cluster**
   - CNPG operator already installed (same as LMS)
   - `kubectl create ns sailpoint` (install script also creates it)
   - `ghcr-pull` docker-registry secret in `sailpoint` (deploy workflow can create it)

4. **Cloudflare Tunnel** public hostname (no Access for now):

   | Field | Value |
   |-------|--------|
   | Subdomain | `sailpoint` |
   | Domain | `lmsapp.us` |
   | Type | HTTP |
   | URL | `identityiq.sailpoint.svc.cluster.local:8080` |

5. **Helm install (manual)**

   ```bash
   export KUBECONFIG=…   # or Tailscale path to cluster
   export IMAGE_TAG=0.1.0
   ./deploy/helm/scripts/install-sailpoint.sh deploy/helm/values/local-homelab.yaml
   ```

## Runtime shape

- **2 IdentityIQ replicas**, Service `sessionAffinity: ClientIP`
- **CNPG PostgreSQL** cluster `sailpoint-pg` (2 instances), DBs: `identityiq`, `identityiqPlugin`, `identityiqah`
- Schema Job applies SailPoint `create_identityiq_tables-8.5.postgresql` once
- DB credentials: Secret `sailpoint-iiq-db` (override via `local-homelab.secrets.yaml`)

## Notes

- IIQ 8.5 supports PostgreSQL; CNPG is the in-cluster choice (not MySQL).
- Shared IIQ filesystem (uploads/plugins) is not PVC-shared on typical k3s RWO — keep plugins in the image or accept single-writer limits.
- Default login after first successful schema + boot: `spadmin` / `admin` (change immediately in any shared lab).
