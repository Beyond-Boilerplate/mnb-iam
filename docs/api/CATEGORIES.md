# API categories (mined)

Cross-cut of endpoints by **category** (business domain) and **surface** (API type).
OpenAPI tags inside each `openapi-*.yaml` mirror these category names.

Total endpoints: **670**

| Category | ootb-rest | ui-rest | scim-v2 | oauth2 | external-rest | plugins | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| identities | 30 | 73 | 5 | 1 |  |  | 109 |
| certifications | 31 | 35 |  |  |  |  | 66 |
| platform | 37 | 23 | 3 |  |  |  | 63 |
| uncategorized | 16 | 35 |  |  |  |  | 51 |
| applications | 32 | 16 | 2 |  |  |  | 50 |
| work-items | 6 | 38 |  |  |  |  | 44 |
| meridian-toolkit |  |  |  |  |  | 38 | 38 |
| plugin:SWECertificationsAddins |  |  |  |  |  | 34 | 34 |
| accounts | 6 | 21 | 5 |  |  |  | 32 |
| tasks | 25 | 4 | 2 |  |  |  | 31 |
| roles | 12 | 5 | 2 |  |  |  | 19 |
| forms | 8 | 8 |  |  |  |  | 16 |
| entitlements | 6 | 7 | 2 |  |  |  | 15 |
| security | 7 | 7 |  |  | 1 |  | 15 |
| policies | 4 | 6 | 3 |  |  |  | 13 |
| reporting | 12 | 1 |  |  |  |  | 13 |
| workflows | 7 |  | 5 |  |  |  | 12 |
| alerts | 8 |  | 3 |  |  |  | 11 |
| oauth |  |  |  | 10 |  |  | 10 |
| plugins | 8 |  |  |  |  |  | 8 |
| authorization | 6 |  |  |  |  |  | 6 |
| provisioning | 5 |  |  |  |  |  | 5 |
| scim-discovery |  |  | 4 |  |  |  | 4 |
| integrations |  | 3 |  |  |  |  | 3 |
| plugin:AccessRequestApprovalAddins |  |  |  |  |  | 2 | 2 |

Regenerate via `./tools/iiq-api-mine/run.sh`.
