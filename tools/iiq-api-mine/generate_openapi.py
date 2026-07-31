#!/usr/bin/env python3
"""Generate categorized OpenAPI 3.0 YAML files from mined-endpoints.json."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / "docs" / "api" / "inventory" / "mined-endpoints.json"
DEFAULT_OUT_DIR = ROOT / "docs" / "api" / "openapi"

SURFACE_META = {
    "ootb-rest": {
        "file": "openapi-ootb-rest.yaml",
        "title": "IdentityIQ OOTB REST API",
        "description": (
            "Product REST surface mounted at `/identityiq/rest/*` "
            "(sailpoint.rest.SailPointRestApplication). "
            "Mined from identityiq.jar bytecode. Request/response schemas are largely unknown "
            "(proprietary); see docs/api/GAPS.md."
        ),
        "base_path": "/identityiq/rest",
    },
    "ui-rest": {
        "file": "openapi-ui-rest.yaml",
        "title": "IdentityIQ UI REST API",
        "description": (
            "UI backend mounted at `/identityiq/ui/rest/*`. Intended for the product SPA, "
            "not third-party integrations. Prefer SCIM or documented OOTB REST for ITSM."
        ),
        "base_path": "/identityiq/ui/rest",
    },
    "scim-v2": {
        "file": "openapi-scim-v2.yaml",
        "title": "IdentityIQ SCIM 2.0 Server API",
        "description": (
            "SCIM 2.0 server mounted at `/identityiq/scim/v2/*` (scim-server.jar). "
            "Schemas map via Configuration-SCIMConfiguration. RFC 7643/7644 shaped."
        ),
        "base_path": "/identityiq/scim/v2",
    },
    "oauth2": {
        "file": "openapi-oauth2.yaml",
        "title": "IdentityIQ OAuth2 API",
        "description": "OAuth2 client and token endpoints at `/identityiq/oauth2/*`.",
        "base_path": "/identityiq/oauth2",
    },
    "external-rest": {
        "file": "openapi-external-rest.yaml",
        "title": "IdentityIQ External REST API",
        "description": "Limited external surface at `/identityiq/external/rest/*` (forms, MFA helpers).",
        "base_path": "/identityiq/external/rest",
    },
    "plugins": {
        "file": "openapi-plugins.yaml",
        "title": "IdentityIQ Plugin REST APIs (Meridian + study)",
        "description": (
            "Custom plugin endpoints at `/identityiq/plugin/rest/*`, mined from pluginsrc. "
            "Includes Meridian IAM Toolkit ping (sample closing GAP-PLUGIN-001)."
        ),
        "base_path": "/identityiq/plugin/rest",
    },
    "plugin-framework": {
        "file": "openapi-plugin-framework.yaml",
        "title": "IdentityIQ Plugin REST Framework",
        "description": "Product plugin framework resources under `/identityiq/plugin/rest/*` from identityiq.jar.",
        "base_path": "/identityiq/plugin/rest",
    },
}


def dump_yaml(obj: Any) -> str:
    if yaml is not None:
        return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
    # Minimal fallback YAML emitter for our constrained shapes
    return _emit(obj, 0)


def _format_key(key: Any) -> str:
    s = str(key)
    if s.isdigit() or s in ("true", "false", "null") or any(c in s for c in ":#{}[],&*?|>!%@`'\""):
        return json.dumps(s)
    return s


def _emit(obj: Any, indent: int) -> str:
    sp = "  " * indent
    if isinstance(obj, dict):
        if not obj:
            return f"{sp}{{}}\n"
        lines: list[str] = []
        for k, v in obj.items():
            key = _format_key(k)
            if isinstance(v, dict):
                if not v:
                    lines.append(f"{sp}{key}: {{}}")
                else:
                    lines.append(f"{sp}{key}:")
                    lines.append(_emit(v, indent + 1).rstrip("\n"))
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{sp}{key}: []")
                else:
                    lines.append(f"{sp}{key}:")
                    lines.append(_emit(v, indent + 1).rstrip("\n"))
            else:
                lines.append(f"{sp}{key}: {_scalar(v)}")
        return "\n".join(lines) + "\n"
    if isinstance(obj, list):
        if not obj:
            return f"{sp}[]\n"
        lines = []
        for item in obj:
            if isinstance(item, dict):
                items = list(item.items())
                if not items:
                    lines.append(f"{sp}- {{}}")
                    continue
                k0, v0 = items[0]
                fk0 = _format_key(k0)
                if isinstance(v0, dict):
                    if not v0:
                        lines.append(f"{sp}- {fk0}: {{}}")
                    else:
                        lines.append(f"{sp}- {fk0}:")
                        lines.append(_emit(v0, indent + 2).rstrip("\n"))
                elif isinstance(v0, list):
                    if not v0:
                        lines.append(f"{sp}- {fk0}: []")
                    else:
                        lines.append(f"{sp}- {fk0}:")
                        lines.append(_emit(v0, indent + 2).rstrip("\n"))
                else:
                    lines.append(f"{sp}- {fk0}: {_scalar(v0)}")
                for k, v in items[1:]:
                    fk = _format_key(k)
                    if isinstance(v, dict):
                        if not v:
                            lines.append(f"{sp}  {fk}: {{}}")
                        else:
                            lines.append(f"{sp}  {fk}:")
                            lines.append(_emit(v, indent + 2).rstrip("\n"))
                    elif isinstance(v, list):
                        if not v:
                            lines.append(f"{sp}  {fk}: []")
                        else:
                            lines.append(f"{sp}  {fk}:")
                            lines.append(_emit(v, indent + 2).rstrip("\n"))
                    else:
                        lines.append(f"{sp}  {fk}: {_scalar(v)}")
            elif isinstance(item, list):
                lines.append(f"{sp}-")
                lines.append(_emit(item, indent + 1).rstrip("\n"))
            else:
                lines.append(f"{sp}- {_scalar(item)}")
        return "\n".join(lines) + "\n"
    return f"{sp}{_scalar(obj)}\n"


def _scalar(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or any(c in s for c in ":#{}[],&*?|>!%@`'\"\n") or s.strip() != s:
        return json.dumps(s)
    return s

def relative_to_mount(full_path: str, mount: str) -> str:
    fp = full_path or "/"
    m = mount or ""
    if m and fp.startswith(m):
        rem = fp[len(m) :] or "/"
        return rem if rem.startswith("/") else "/" + rem
    return fp if fp.startswith("/") else "/" + fp


def op_id(method: str, full_path: str, class_name: str, method_name: str) -> str:
    base = f"{method}_{full_path}_{method_name}".lower()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    # include short class to avoid collisions
    short = class_name.rsplit(".", 1)[-1]
    short = re.sub(r"[^a-zA-Z0-9]", "", short)
    oid = f"{base}_{short}"[:100]
    return oid or f"{method}_{method_name}"


def build_operation(ep: dict[str, Any]) -> dict[str, Any]:
    params = []
    for p in ep.get("path_params") or []:
        params.append(
            {
                "name": p,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": f"Path parameter `{p}` (mined).",
            }
        )
    for q in ep.get("query_params") or []:
        params.append(
            {
                "name": q,
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": f"Query parameter `{q}` (mined).",
            }
        )

    produces = ep.get("produces") or ["application/json"]
    content = {media: {"schema": {"$ref": "#/components/schemas/UnknownJson"}} for media in produces}
    responses: dict[str, Any] = {
        "200": {
            "description": "Success (schema not fully recoverable from bytecode).",
            "content": content,
        },
        "401": {"description": "Unauthenticated"},
        "403": {"description": "Authenticated but not authorized (capability/right)."},
        "404": {"description": "Resource not found"},
    }

    op: dict[str, Any] = {
        "tags": [ep.get("category") or "uncategorized", ep.get("subcategory") or "other"],
        "summary": f"{ep['http_method']} {ep['path']} ({ep['method_name']})",
        "description": (
            f"Class `{ep['class_name']}` method `{ep['method_name']}`.\n\n"
            f"Source: `{ep.get('source')}`.\n"
            f"Auth hints: {', '.join(ep.get('auth_hints') or []) or 'none mined'}.\n"
            f"Gaps: {', '.join(ep.get('gaps') or []) or 'none'}."
        ),
        "operationId": op_id(ep["http_method"], ep["full_path"], ep["class_name"], ep["method_name"]),
        "parameters": params,
        "responses": responses,
        "x-iiq-class": ep["class_name"],
        "x-iiq-method": ep["method_name"],
        "x-iiq-surface": ep["surface"],
        "x-iiq-gaps": ep.get("gaps") or [],
        "x-iiq-auth-hints": ep.get("auth_hints") or [],
    }

    if ep["http_method"] in ("POST", "PUT", "PATCH"):
        consumes = ep.get("consumes") or ["application/json"]
        op["requestBody"] = {
            "required": False,
            "content": {
                media: {
                    "schema": {"$ref": "#/components/schemas/UnknownJson"},
                    "description": "Request body schema not recoverable from bytecode (see GAPS.md).",
                }
                for media in consumes
            },
        }
    if ep.get("deprecated"):
        op["deprecated"] = True
    return op


def build_spec(surface: str, endpoints: list[dict[str, Any]], meta: dict[str, Any], generated_at: str) -> dict[str, Any]:
    mount = meta["base_path"].replace("/identityiq", "")  # /rest etc matching mined mount
    # group path -> methods
    paths: dict[str, dict[str, Any]] = defaultdict(dict)
    tags_set = {}
    for ep in endpoints:
        rel = relative_to_mount(ep["full_path"], ep.get("mount") or mount)
        # OpenAPI paths should be relative to servers.url which includes /identityiq + mount
        # Use path relative to mount only
        path_key = rel if rel.startswith("/") else "/" + rel
        method = ep["http_method"].lower()
        # avoid overwrite: if collision, suffix via operationId uniqueness already; keep first + note
        if method in paths[path_key]:
            # collide — append unique path query surrogate via x- extension on existing
            alt = f"{path_key}#{ep['method_name']}"
            # OpenAPI forbids # in paths; encode collision as separate path extension undocumented —
            # instead attach as related op under same path with distinct operationId (can't have two GETs)
            # Store under x-iiq-collisions
            paths[path_key].setdefault("x-iiq-collisions", []).append(
                {
                    "method": method,
                    "class": ep["class_name"],
                    "javaMethod": ep["method_name"],
                    "operation": build_operation(ep),
                }
            )
            continue
        paths[path_key][method] = build_operation(ep)
        cat = ep.get("category") or "uncategorized"
        tags_set[cat] = {
            "name": cat,
            "description": f"Category `{cat}` / subcategory `{ep.get('subcategory')}`.",
        }

    servers = [
        {
            "url": meta["base_path"],
            "description": "Via docs/api/serve.py proxy (same origin — use in Swagger)",
        },
        {"url": f"http://localhost:8080{meta['base_path']}", "description": "Direct local IIQ (curl; browser CORS from other origins)"},
        {"url": f"https://sailpoint.lmsapp.us{meta['base_path']}", "description": "Homelab academy IIQ"},
    ]

    return {
        "openapi": "3.0.3",
        "info": {
            "title": meta["title"],
            "version": "8.5-mined",
            "description": meta["description"]
            + f"\n\nGenerated at `{generated_at}` by `tools/iiq-api-mine`. "
            + "Regenerate with `./tools/iiq-api-mine/run.sh`.",
            "x-iiq-surface": surface,
            "x-generated-by": "tools/iiq-api-mine",
        },
        "servers": servers,
        "tags": sorted(tags_set.values(), key=lambda t: t["name"]),
        "paths": {k: dict(v) for k, v in sorted(paths.items())},
        "components": {
            "securitySchemes": {
                "basicAuth": {"type": "http", "scheme": "basic"},
                "sessionCookie": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "JSESSIONID",
                    "description": "Browser session cookie after UI login.",
                },
                "oAuth2ClientCredentials": {
                    "type": "oauth2",
                    "flows": {
                        "clientCredentials": {
                            "tokenUrl": "http://localhost:8080/identityiq/oauth2/token",
                            "scopes": {},
                        }
                    },
                },
            },
            "schemas": {
                "UnknownJson": {
                    "type": "object",
                    "additionalProperties": True,
                    "description": (
                        "Placeholder. Exact schema not present in bytecode annotations. "
                        "Capture via live probing / SailPoint product docs. Tracked in GAPS.md."
                    ),
                },
                "Problemish": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
                "MnbToolkitPingResponse": {
                    "type": "object",
                    "required": ["status", "bank"],
                    "properties": {
                        "status": {"type": "string", "example": "ok"},
                        "bank": {"type": "string", "example": "MNB"},
                        "plugin": {"type": "string", "example": "mnb-iam-toolkit"},
                        "version": {"type": "string", "example": "1.1.0"},
                    },
                },
                "MnbTaskRunRequest": {
                    "type": "object",
                    "required": ["taskName"],
                    "properties": {
                        "taskName": {
                            "type": "string",
                            "description": "Exact TaskDefinition name (must match allowedTaskNames).",
                            "example": "Refresh Identity Cube",
                        },
                        "sync": {
                            "type": "boolean",
                            "default": False,
                            "description": "Prefer false for aggregations; true blocks HTTP until complete.",
                        },
                        "args": {
                            "type": "object",
                            "additionalProperties": True,
                            "description": "Task arguments (e.g. applications filter).",
                        },
                    },
                },
                "MnbTaskRunResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["accepted", "running", "success", "failed"]},
                        "taskName": {"type": "string"},
                        "taskResultId": {"type": "string"},
                        "taskResultName": {"type": "string"},
                        "sync": {"type": "boolean"},
                        "complete": {"type": "boolean"},
                        "success": {"type": "boolean"},
                        "percentComplete": {"type": "integer"},
                        "bank": {"type": "string", "example": "MNB"},
                    },
                },
            },
        },
        "security": [{"basicAuth": []}, {"sessionCookie": []}],
    }


def enhance_plugins_spec(spec: dict[str, Any]) -> None:
    """Attach concrete schemas for Meridian toolkit endpoints."""
    paths = spec.get("paths") or {}
    for path, item in paths.items():
        for method, op in list(item.items()):
            if method.startswith("x-") or not isinstance(op, dict):
                continue
            cls = str(op.get("x-iiq-class", ""))
            if "MnbToolkitPing" in cls or path.rstrip("/").endswith("/mnbToolkit/ping"):
                op.setdefault("responses", {}).setdefault("200", {})["content"] = {
                    "application/json": {"schema": {"$ref": "#/components/schemas/MnbToolkitPingResponse"}}
                }
                op["responses"]["200"]["description"] = "Toolkit ping OK."
                op["x-iiq-gaps"] = [g for g in (op.get("x-iiq-gaps") or []) if "schema" not in g]
            if "MnbToolkitTask" in cls or "/mnbToolkit/tasks/" in path:
                if method == "post" and path.endswith("/run"):
                    op["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/MnbTaskRunRequest"}}
                        },
                    }
                op.setdefault("responses", {}).setdefault("200", {})["content"] = {
                    "application/json": {"schema": {"$ref": "#/components/schemas/MnbTaskRunResponse"}}
                }
                op["responses"]["200"]["description"] = "Task launch or status (Meridian schema)."
                op["x-iiq-gaps"] = [g for g in (op.get("x-iiq-gaps") or []) if "schema" not in g]

def write_categories_md(out_path: Path, endpoints: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    by_cat: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for e in endpoints:
        by_cat[e.get("category") or "uncategorized"][e.get("surface") or "?"] += 1
    lines = [
        "# API categories (mined)",
        "",
        "Cross-cut of endpoints by **category** (business domain) and **surface** (API type).",
        "OpenAPI tags inside each `openapi-*.yaml` mirror these category names.",
        "",
        f"Total endpoints: **{summary.get('endpoint_count', len(endpoints))}**",
        "",
        "| Category | ootb-rest | ui-rest | scim-v2 | oauth2 | external-rest | plugins | Total |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    surfaces = ["ootb-rest", "ui-rest", "scim-v2", "oauth2", "external-rest", "plugins"]
    for cat in sorted(by_cat.keys(), key=lambda c: (-sum(by_cat[c].values()), c)):
        counts = by_cat[cat]
        row = [cat] + [str(counts.get(s, 0) or "") for s in surfaces] + [str(sum(counts.values()))]
        # blank zeros as empty for readability
        row = [row[0]] + [c if c != "0" else "" for c in row[1:-1]] + [row[-1]]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("Regenerate via `./tools/iiq-api-mine/run.sh`.")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_bundle_index(out_dir: Path, surfaces: list[str], summary: dict[str, Any], generated_at: str) -> None:
    bundle = {
        "openapi": "3.0.3",
        "info": {
            "title": "IdentityIQ 8.5 API Bundle Index",
            "version": "8.5-mined",
            "description": (
                "Index of categorized OpenAPI documents for this SSD lab. "
                "Open individual YAML files in Swagger UI. See docs/api/README.md."
            ),
            "x-generated-at": generated_at,
            "x-summary": summary,
        },
        "servers": [{"url": "http://localhost:8080/identityiq"}],
        "paths": {},
        "x-iiq-openapi-files": [
            {
                "surface": s,
                "file": SURFACE_META[s]["file"],
                "title": SURFACE_META[s]["title"],
                "basePath": SURFACE_META[s]["base_path"],
            }
            for s in surfaces
            if s in SURFACE_META
        ],
        "components": {"schemas": {}},
    }
    (out_dir / "openapi-iiq-bundle.yaml").write_text(dump_yaml(bundle), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args()

    data = json.loads(args.inventory.read_text(encoding="utf-8"))
    endpoints: list[dict[str, Any]] = data["endpoints"]
    generated_at = data.get("generated_at", "")
    by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ep in endpoints:
        by_surface[ep["surface"]].append(ep)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for surface, eps in sorted(by_surface.items()):
        meta = SURFACE_META.get(
            surface,
            {
                "file": f"openapi-{surface}.yaml",
                "title": f"IdentityIQ {surface}",
                "description": f"Auto-mined surface `{surface}`.",
                "base_path": "/identityiq",
            },
        )
        spec = build_spec(surface, eps, meta, generated_at)
        if surface == "plugins":
            enhance_plugins_spec(spec)
        out = args.out_dir / meta["file"]
        out.write_text(dump_yaml(spec), encoding="utf-8")
        written.append(out.name)
        print(f"Wrote {out} ({len(eps)} endpoints, {len(spec['paths'])} paths)")

    write_bundle_index(args.out_dir, list(by_surface.keys()), data.get("summary", {}), generated_at)
    write_categories_md(ROOT / "docs" / "api" / "CATEGORIES.md", endpoints, data.get("summary", {}))
    print("Wrote openapi-iiq-bundle.yaml + CATEGORIES.md")
    print("Files:", ", ".join(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
