# Meridian IAM Academy — learn site + Verify API

Markdown lessons in `docs/lessons/` compile to static HTML under `learn/dist/`, then the academy image serves them with **`POST /api/verify/<lesson>`** against IdentityIQ.

## Local preview (with Verify now)

```bash
./tools/lab/up.sh
# or: ./tools/lab/docker/up.sh
# Academy http://localhost:4173/   IIQ http://localhost:8080/identityiq
```

Static HTML only (no Verify API):

```bash
python3 learn/build.py
cd learn/dist && python3 -m http.server 4173
```

## Production image

```bash
docker build -f learn/Dockerfile -t mnb-learn .
docker run --rm -p 4173:8080 \
  -e IIQ_BASE_URL=http://host.docker.internal:8080/identityiq \
  -e IIQ_VERIFY_MODE=local \
  mnb-learn
```

## Production URLs

| Surface | URL |
| --- | --- |
| Academy + Verify | https://sailpoint.lmsapp.us/ |
| IdentityIQ | https://sailpoint.lmsapp.us/identityiq/login.jsf |

```text
docs/lessons/*.md  →  learn/build.py  →  learn/dist/*.html
                                              ↓
                         mnb-learn (serve.py + /api/verify)
                                              ↓
                         sailpoint-edge (path router)
                                              ↓
                    Cloudflare → sailpoint.lmsapp.us
```

On the public site, Verify now checks the **homelab IIQ** in-cluster (`identityiq` Service). Laptop labs should use `./tools/lab/up.sh` so Verify targets your local IIQ.

## Deploy

```bash
# CI: Actions → Publish learn site
# or:
./learn/k8s/install-public-surface.sh
```

**Cloudflare Tunnel** must target `sailpoint-edge.sailpoint.svc.cluster.local:8080` (not IdentityIQ). Details: [docs/LEARN-SITE.md](../docs/LEARN-SITE.md).

## Regenerating

```bash
python3 tools/generate-mnb-curriculum.py   # lab-data only
# Optional: Meridian IAM Audio (multi-agent conversational podcasts)
# cd tools/podcast-studio && source .venv/bin/activate && ./run.py E01
python3 learn/build.py                     # HTML (+ copies learn/media/audio when present)
```

**Audio hub:** [`audio.html`](./dist/audio.html) after build — thematic two-host episodes
(not per-lesson TTS). Pipeline: [`tools/podcast-studio/README.md`](../tools/podcast-studio/README.md).
