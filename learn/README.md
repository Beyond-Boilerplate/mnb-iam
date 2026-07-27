# Meridian IAM Academy — static learn site

Markdown lessons in `docs/lessons/` compile to static HTML under `learn/dist/`.

## Local preview

```bash
python3 learn/build.py
cd learn/dist && python3 -m http.server 4173
# open http://127.0.0.1:4173/
```

Docker (root path, production shape):

```bash
docker build -f learn/Dockerfile -t mnb-learn .
docker run --rm -p 4173:8080 mnb-learn
# open http://127.0.0.1:4173/
```

## Production URLs

| Surface | URL |
| --- | --- |
| Academy | https://sailpoint.lmsapp.us/ |
| IdentityIQ | https://sailpoint.lmsapp.us/identityiq/login.jsf |

```text
docs/lessons/*.md  →  learn/build.py  →  learn/dist/*.html
                                              ↓
                                    mnb-learn (nginx)
                                              ↓
                         sailpoint-edge (path router)
                                              ↓
                    Cloudflare → sailpoint.lmsapp.us
```

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
python3 learn/build.py                     # HTML
```
