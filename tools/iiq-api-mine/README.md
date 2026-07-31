# IIQ API miner

Continuous bytecode mining for IdentityIQ JAX-RS surfaces → `docs/api/`.

```bash
# Requires build/extract WAR libs
./tools/iiq-api-mine/run.sh
```

| Script | Role |
| --- | --- |
| `classfile_jaxrs.py` | Java class-file + annotation reader |
| `mine_jaxrs.py` | Mine jars + `pluginsrc` → `mined-endpoints.json` |
| `generate_openapi.py` | Categorized OpenAPI 3 YAML |
| `generate_gaps.py` | `docs/api/GAPS.md` |
| `run.sh` | Full pipeline |

After IIQ upgrades, re-extract WAR and re-run.
