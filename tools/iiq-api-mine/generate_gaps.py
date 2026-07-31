#!/usr/bin/env python3
"""Generate docs/api/GAPS.md from mined inventory + known product gaps."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


KNOWN_GAPS = [
    {
        "id": "GAP-PLUGIN-001",
        "severity": "critical",
        "title": "No first-party Meridian plugin REST contract",
        "detail": (
            "Study plugins exist (AccessRequestApprovalAddins, SWECertificationsAddins) but "
            "Meridian lacked a versioned, rights-gated toolkit health endpoint for monitors/ITSM smoke."
        ),
        "status": "addressed",
        "remediation": (
            "Created `pluginsrc/mnb-iam-toolkit` with `GET /plugin/rest/mnbToolkit/ping` "
            "returning `{status,bank,plugin,version}` and right `MNBToolkitAccess`. "
            "Documented in `openapi-plugins.yaml`."
        ),
    },
    {
        "id": "GAP-SCHEMA-001",
        "severity": "high",
        "title": "Request/response JSON schemas not recoverable from bytecode",
        "detail": (
            "JAX-RS annotations do not embed OpenAPI schemas. Return types are Java Map/DTO classes "
            "without JSON Schema metadata. All OOTB/UI/SCIM endpoints use UnknownJson placeholders."
        ),
        "status": "open",
        "remediation": (
            "Live capture (WireMock/HAR), SailPoint Compass docs, or decompile + manual schema "
            "curation per high-value operation. Prefer SCIM (RFC schemas) for identity sync."
        ),
    },
    {
        "id": "GAP-WADL-001",
        "severity": "medium",
        "title": "WADL disabled in product web.xml",
        "detail": (
            "`jersey.config.server.wadl.disableWadl=true` for all SailPoint Jersey applications. "
            "No runtime `/application.wadl` discovery."
        ),
        "status": "accepted",
        "remediation": "Keep docs/api generated inventory as the lab source of truth; re-mine after upgrades.",
    },
    {
        "id": "GAP-SUBRESOURCE-001",
        "severity": "high",
        "title": "Sub-resource locators incompletely represented",
        "detail": (
            "Methods returning another Resource class (sub-resource locators) may not expose a "
            "combined path in annotations the same way as leaf methods. Colliding HTTP verbs on "
            "the same path are recorded under `x-iiq-collisions`."
        ),
        "status": "open",
        "remediation": "Enhance miner to follow return types assignable to Resource; manual review of Identity*/Certification* trees.",
    },
    {
        "id": "GAP-UI-001",
        "severity": "medium",
        "title": "UI REST is not an integration contract",
        "detail": (
            "`/ui/rest` is large and session/CSRF oriented. Documenting it is for completeness; "
            "Meridian integrations must not depend on unstable UI routes."
        ),
        "status": "accepted",
        "remediation": "Use SCIM + selective OOTB REST + Meridian plugin APIs for external systems.",
    },
    {
        "id": "GAP-AUTHZ-001",
        "severity": "high",
        "title": "Capability requirements rarely present as annotations",
        "detail": (
            "Many OOTB methods authorize via imperative `authorize(RightAuthorizer…)` rather than "
            "`@RequiredRight`. Mined `auth_hints` therefore under-report required SPRights."
        ),
        "status": "open",
        "remediation": "Bytecode scan for SPRight$WebServiceRights field refs per method; cross-check Compass.",
    },
    {
        "id": "GAP-SCIM-ENABLE-001",
        "severity": "medium",
        "title": "SCIM module may be disabled in some lab WARs",
        "detail": "Curriculum records SCIM as optional; probes may 404 even when jars are present.",
        "status": "open",
        "remediation": "Verify live GET /scim/v2/ServiceProviderConfig; track Lab risk RR-MNB-110-04.",
    },
    {
        "id": "GAP-STUDY-ALLOWALL-001",
        "severity": "high",
        "title": "Study plugins use @AllowAll",
        "detail": "AccessRequestApprovalAddins / SWECertificationsAddins annotate REST with @AllowAll (teaching anti-pattern).",
        "status": "accepted",
        "remediation": "Meridian toolkit uses RequiredRight/MNBToolkitAccess; do not promote study plugins to prod unchanged.",
    },
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.inventory.read_text(encoding="utf-8"))
    eps = data["endpoints"]
    summary = data.get("summary", {})
    gap_counter = Counter(g for e in eps for g in e.get("gaps") or [])
    by_surface_gaps = defaultdict(Counter)
    for e in eps:
        for g in e.get("gaps") or []:
            by_surface_gaps[e["surface"]][g] += 1

    missing_path = [e for e in eps if "missing-path-annotation" in (e.get("gaps") or [])]
    allow_all = [e for e in eps if "AllowAll" in (e.get("auth_hints") or [])]

    lines = []
    lines.append("# IdentityIQ API documentation gaps")
    lines.append("")
    lines.append(f"_Generated: `{data.get('generated_at')}` · Endpoints mined: **{summary.get('endpoint_count', len(eps))}**_")
    lines.append("")
    lines.append("This file is produced by `tools/iiq-api-mine/generate_gaps.py` after bytecode mining.")
    lines.append("It separates **catalog gaps** (what we could not recover) from **product/lab gaps** (what Meridian still needs).")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Endpoints mined | {summary.get('endpoint_count')} |")
    lines.append(f"| Unique method+path | {summary.get('unique_full_paths')} |")
    lines.append(f"| Surfaces | {', '.join(sorted((summary.get('by_surface') or {}).keys()))} |")
    lines.append(f"| Endpoints with `@AllowAll` | {len(allow_all)} |")
    lines.append(f"| Missing path annotation | {len(missing_path)} |")
    lines.append("")
    lines.append("### Mined gap tag frequencies")
    lines.append("")
    lines.append("| Gap tag | Count |")
    lines.append("| --- | ---: |")
    for g, c in gap_counter.most_common():
        lines.append(f"| `{g}` | {c} |")
    lines.append("")
    lines.append("### Gap tags by surface")
    lines.append("")
    for surface, ctr in sorted(by_surface_gaps.items()):
        lines.append(f"**{surface}**")
        lines.append("")
        lines.append("| Tag | Count |")
        lines.append("| --- | ---: |")
        for g, c in ctr.most_common(12):
            lines.append(f"| `{g}` | {c} |")
        lines.append("")

    lines.append("## Tracked gap register")
    lines.append("")
    for g in KNOWN_GAPS:
        lines.append(f"### {g['id']} — {g['title']}")
        lines.append("")
        lines.append(f"- **Severity:** {g['severity']}")
        lines.append(f"- **Status:** `{g['status']}`")
        lines.append(f"- **Detail:** {g['detail']}")
        lines.append(f"- **Remediation:** {g['remediation']}")
        lines.append("")

    lines.append("## Completeness matrix")
    lines.append("")
    lines.append("| Concern | OOTB `/rest` | UI `/ui/rest` | SCIM | OAuth | External | Plugins |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    lines.append("| Path inventory | high | high | high | high | high | high |")
    lines.append("| HTTP verbs | high | high | high | high | high | high |")
    lines.append("| Query/path params | medium | medium | medium | medium | medium | high |")
    lines.append("| Authz rights | low | low | low | medium | low | medium |")
    lines.append("| JSON schemas | low | low | medium (RFC) | low | low | high (toolkit) |")
    lines.append("| Examples | low | low | medium | low | low | high (ping) |")
    lines.append("")
    lines.append("## Sample API closing GAP-PLUGIN-001")
    lines.append("")
    lines.append("```http")
    lines.append("GET /identityiq/plugin/rest/mnbToolkit/ping HTTP/1.1")
    lines.append("Host: localhost:8080")
    lines.append("Authorization: Basic …")
    lines.append("Accept: application/json")
    lines.append("```")
    lines.append("")
    lines.append("```json")
    lines.append('{')
    lines.append('  "status": "ok",')
    lines.append('  "bank": "MNB",')
    lines.append('  "plugin": "mnb-iam-toolkit",')
    lines.append('  "version": "1.0.0"')
    lines.append("}")
    lines.append("```")
    lines.append("")
    lines.append("Source: `pluginsrc/mnb-iam-toolkit/`. Spec: `docs/api/openapi/openapi-plugins.yaml`.")
    lines.append("")
    lines.append("## Regeneration")
    lines.append("")
    lines.append("```bash")
    lines.append("./tools/iiq-api-mine/run.sh")
    lines.append("```")
    lines.append("")
    lines.append(f"_Writer timestamp: {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")

    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
