# Enterprise Lab data

| Path | Purpose |
| --- | --- |
| `identity-master.json` | Single source of truth for lab identities |
| `generated/` | Outputs from `tools/lab/enterprise/generate-identity-artifacts.py` |
| `keycloak/meridian-realm.json` | Keycloak realm import (Okta-shaped IdP) |
| `samba/` | Samba AD notes + seed instructions |

Do not edit `generated/` by hand — regenerate from the master.
