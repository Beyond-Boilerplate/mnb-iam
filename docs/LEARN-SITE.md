# Host Meridian IAM Academy on sailpoint.lmsapp.us

Companion to [HOMELAB-CD.md](HOMELAB-CD.md) and [learn/README.md](../learn/README.md).

## Public URLs

| Surface | URL |
| --- | --- |
| **Academy (home)** | https://sailpoint.lmsapp.us/ |
| IdentityIQ lab | https://sailpoint.lmsapp.us/identityiq/login.jsf |

Lessons are static HTML built from `docs/lessons/*.md`. No IdentityIQ dependency to *read* the curriculum.

## Architecture

```text
Browser
  │
  ▼
Cloudflare Tunnel  sailpoint.lmsapp.us
  │
  ▼
sailpoint-edge :8080   (nginx path router)
  ├── /identityiq/*  →  identityiq:8080
  └── /*             →  mnb-learn:8080   (academy at /)
```

## One-time Cloudflare Tunnel change

In Cloudflare Zero Trust → Networks → Tunnels → Public Hostnames → edit `sailpoint.lmsapp.us`:

| Field | Value |
| --- | --- |
| Subdomain | `sailpoint` |
| Domain | `lmsapp.us` |
| Type | HTTP |
| URL | `sailpoint-edge.sailpoint.svc.cluster.local:8080` |

Previously this pointed at `identityiq.sailpoint.svc.cluster.local:8080`. Update it or `/` will still be IIQ.

## Deploy

```bash
# after image is in GHCR (or CI Publish learn site)
export KUBECONFIG=…
./learn/k8s/install-public-surface.sh
```

CI: **Actions → Publish learn site** builds `mnb-iam-learn`, applies manifests, smokes `/` and `/identityiq`.

Homelab Helm deploys also re-apply the public surface so the edge stays present.

## Content update loop

1. Edit `docs/lessons/*.md`
2. Push to `main` (paths under `docs/lessons/**` or `learn/**`) → Publish learn workflow
3. Or locally: `python3 learn/build.py` then `docker build -f learn/Dockerfile …`

## Verify

```bash
curl -sSI https://sailpoint.lmsapp.us/ | head
curl -sS https://sailpoint.lmsapp.us/ | grep -i Meridian
curl -sSI https://sailpoint.lmsapp.us/identityiq/login.jsf | head
```
