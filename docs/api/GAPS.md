# IdentityIQ API documentation gaps

_Generated: `2026-07-29T18:48:38.658570+00:00` · Endpoints mined: **670**_

This file is produced by `tools/iiq-api-mine/generate_gaps.py` after bytecode mining.
It separates **catalog gaps** (what we could not recover) from **product/lab gaps** (what Meridian still needs).

## Executive summary

| Metric | Value |
| --- | --- |
| Endpoints mined | 670 |
| Unique method+path | 646 |
| Surfaces | external-rest, oauth2, ootb-rest, plugins, scim-v2, ui-rest |
| Endpoints with `@AllowAll` | 2 |
| Missing path annotation | 119 |

### Mined gap tag frequencies

| Gap tag | Count |
| --- | ---: |
| `response-schema-unknown` | 596 |
| `produces-unspecified` | 552 |
| `request-schema-unknown` | 202 |
| `consumes-unspecified` | 185 |
| `missing-path-annotation` | 119 |
| `subresource-locator-path-synthetic` | 119 |
| `response-schema-partial` | 74 |
| `request-schema-partial` | 51 |

### Gap tags by surface

**external-rest**

| Tag | Count |
| --- | ---: |
| `produces-unspecified` | 1 |
| `response-schema-unknown` | 1 |

**oauth2**

| Tag | Count |
| --- | ---: |
| `response-schema-unknown` | 11 |
| `request-schema-unknown` | 6 |
| `produces-unspecified` | 5 |
| `missing-path-annotation` | 3 |
| `subresource-locator-path-synthetic` | 3 |
| `consumes-unspecified` | 2 |

**ootb-rest**

| Tag | Count |
| --- | ---: |
| `response-schema-unknown` | 266 |
| `produces-unspecified` | 264 |
| `request-schema-unknown` | 99 |
| `consumes-unspecified` | 93 |
| `missing-path-annotation` | 31 |
| `subresource-locator-path-synthetic` | 31 |

**plugins**

| Tag | Count |
| --- | ---: |
| `response-schema-partial` | 74 |
| `request-schema-partial` | 51 |

**scim-v2**

| Tag | Count |
| --- | ---: |
| `response-schema-unknown` | 36 |
| `missing-path-annotation` | 17 |
| `subresource-locator-path-synthetic` | 17 |
| `request-schema-unknown` | 7 |

**ui-rest**

| Tag | Count |
| --- | ---: |
| `produces-unspecified` | 282 |
| `response-schema-unknown` | 282 |
| `consumes-unspecified` | 90 |
| `request-schema-unknown` | 90 |
| `missing-path-annotation` | 68 |
| `subresource-locator-path-synthetic` | 68 |

## Tracked gap register

### GAP-PLUGIN-001 — No first-party Meridian plugin REST contract

- **Severity:** critical
- **Status:** `addressed`
- **Detail:** Study plugins exist (AccessRequestApprovalAddins, SWECertificationsAddins) but Meridian lacked a versioned, rights-gated toolkit health endpoint for monitors/ITSM smoke.
- **Remediation:** Created `pluginsrc/mnb-iam-toolkit` with `GET /plugin/rest/mnbToolkit/ping` returning `{status,bank,plugin,version}` and right `MNBToolkitAccess`. Documented in `openapi-plugins.yaml`.

### GAP-SCHEMA-001 — Request/response JSON schemas not recoverable from bytecode

- **Severity:** high
- **Status:** `open`
- **Detail:** JAX-RS annotations do not embed OpenAPI schemas. Return types are Java Map/DTO classes without JSON Schema metadata. All OOTB/UI/SCIM endpoints use UnknownJson placeholders.
- **Remediation:** Live capture (WireMock/HAR), SailPoint Compass docs, or decompile + manual schema curation per high-value operation. Prefer SCIM (RFC schemas) for identity sync.

### GAP-WADL-001 — WADL disabled in product web.xml

- **Severity:** medium
- **Status:** `accepted`
- **Detail:** `jersey.config.server.wadl.disableWadl=true` for all SailPoint Jersey applications. No runtime `/application.wadl` discovery.
- **Remediation:** Keep docs/api generated inventory as the lab source of truth; re-mine after upgrades.

### GAP-SUBRESOURCE-001 — Sub-resource locators incompletely represented

- **Severity:** high
- **Status:** `open`
- **Detail:** Methods returning another Resource class (sub-resource locators) may not expose a combined path in annotations the same way as leaf methods. Colliding HTTP verbs on the same path are recorded under `x-iiq-collisions`.
- **Remediation:** Enhance miner to follow return types assignable to Resource; manual review of Identity*/Certification* trees.

### GAP-UI-001 — UI REST is not an integration contract

- **Severity:** medium
- **Status:** `accepted`
- **Detail:** `/ui/rest` is large and session/CSRF oriented. Documenting it is for completeness; Meridian integrations must not depend on unstable UI routes.
- **Remediation:** Use SCIM + selective OOTB REST + Meridian plugin APIs for external systems.

### GAP-AUTHZ-001 — Capability requirements rarely present as annotations

- **Severity:** high
- **Status:** `open`
- **Detail:** Many OOTB methods authorize via imperative `authorize(RightAuthorizer…)` rather than `@RequiredRight`. Mined `auth_hints` therefore under-report required SPRights.
- **Remediation:** Bytecode scan for SPRight$WebServiceRights field refs per method; cross-check Compass.

### GAP-SCIM-ENABLE-001 — SCIM module may be disabled in some lab WARs

- **Severity:** medium
- **Status:** `open`
- **Detail:** Curriculum records SCIM as optional; probes may 404 even when jars are present.
- **Remediation:** Verify live GET /scim/v2/ServiceProviderConfig; track Lab risk RR-MNB-110-04.

### GAP-STUDY-ALLOWALL-001 — Study plugins use @AllowAll

- **Severity:** high
- **Status:** `accepted`
- **Detail:** AccessRequestApprovalAddins / SWECertificationsAddins annotate REST with @AllowAll (teaching anti-pattern).
- **Remediation:** Meridian toolkit uses RequiredRight/MNBToolkitAccess; do not promote study plugins to prod unchanged.

## Completeness matrix

| Concern | OOTB `/rest` | UI `/ui/rest` | SCIM | OAuth | External | Plugins |
| --- | --- | --- | --- | --- | --- | --- |
| Path inventory | high | high | high | high | high | high |
| HTTP verbs | high | high | high | high | high | high |
| Query/path params | medium | medium | medium | medium | medium | high |
| Authz rights | low | low | low | medium | low | medium |
| JSON schemas | low | low | medium (RFC) | low | low | high (toolkit) |
| Examples | low | low | medium | low | low | high (ping) |

## Sample API closing GAP-PLUGIN-001

```http
GET /identityiq/plugin/rest/mnbToolkit/ping HTTP/1.1
Host: localhost:8080
Authorization: Basic …
Accept: application/json
```

```json
{
  "status": "ok",
  "bank": "MNB",
  "plugin": "mnb-iam-toolkit",
  "version": "1.0.0"
}
```

Source: `pluginsrc/mnb-iam-toolkit/`. Spec: `docs/api/openapi/openapi-plugins.yaml`.

## Regeneration

```bash
./tools/iiq-api-mine/run.sh
```

_Writer timestamp: 2026-07-29T18:48:38.956536+00:00_
