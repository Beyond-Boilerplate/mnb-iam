#!/usr/bin/env python3
"""Mine JAX-RS endpoints from IIQ WAR jars + pluginsrc Java sources.

Outputs docs/api/inventory/mined-endpoints.json used by generate_openapi.py.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from classfile_jaxrs import (
    HTTP_VERBS,
    ClassFile,
    ClassFileError,
    annotation_simple_name,
    find_annotation,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WAR_LIB = ROOT / "build" / "extract" / "WEB-INF" / "lib"
DEFAULT_OUT = ROOT / "docs" / "api" / "inventory" / "mined-endpoints.json"
PLUGINSRC = ROOT / "pluginsrc"

MOUNT_BY_PACKAGE_PREFIX = [
    ("sailpoint.rest.scim.", "/scim/v2"),
    ("sailpoint.rest.ui.", "/ui/rest"),
    ("sailpoint.rest.oauth.", "/oauth2"),
    ("sailpoint.rest.external.", "/external/rest"),
    ("sailpoint.rest.plugin.", "/plugin/rest"),
    ("sailpoint.rest.", "/rest"),
]


@dataclass
class Endpoint:
    surface: str
    mount: str
    category: str
    subcategory: str
    http_method: str
    path: str
    full_path: str
    class_name: str
    method_name: str
    produces: list[str] = field(default_factory=list)
    consumes: list[str] = field(default_factory=list)
    path_params: list[str] = field(default_factory=list)
    query_params: list[str] = field(default_factory=list)
    auth_hints: list[str] = field(default_factory=list)
    source: str = ""
    gaps: list[str] = field(default_factory=list)
    deprecated: bool = False


def join_paths(*parts: str) -> str:
    segs: list[str] = []
    for p in parts:
        if not p:
            continue
        for s in str(p).split("/"):
            if s and s != ".":
                segs.append(s)
    return "/" + "/".join(segs)


def path_params_in(path: str) -> list[str]:
    return re.findall(r"\{([^}/]+)\}", path or "")


def infer_mount(class_name: str) -> tuple[str, str]:
    for prefix, mount in MOUNT_BY_PACKAGE_PREFIX:
        if class_name.startswith(prefix):
            surface = {
                "/rest": "ootb-rest",
                "/ui/rest": "ui-rest",
                "/scim/v2": "scim-v2",
                "/oauth2": "oauth2",
                "/external/rest": "external-rest",
                "/plugin/rest": "plugin-framework",
            }[mount]
            return surface, mount
    return "unknown", ""


def infer_category(class_name: str, path: str) -> tuple[str, str]:
    simple = class_name.rsplit(".", 1)[-1]
    blob = f"{simple} {path}".lower()
    rules = [
        (("identity", "identities", "user"), "identities", "identity-lifecycle"),
        (("certif",), "certifications", "access-review"),
        (("workitem", "approval", "work-item"), "work-items", "approvals"),
        (("workflow", "launchedworkflow"), "workflows", "orchestration"),
        (("application", "apponboard"), "applications", "connectors"),
        (("role", "bundle"), "roles", "role-model"),
        (("managedattribute", "entitlement", "accountgroup"), "entitlements", "managed-attributes"),
        (("account", "link"), "accounts", "account-links"),
        (("policy", "violation", "sod"), "policies", "governance"),
        (("task", "schedule", "request"), "tasks", "operations"),
        (("form",), "forms", "ui-forms"),
        (("alert",), "alerts", "monitoring"),
        (("plugin",), "plugins", "extensibility"),
        (("oauth", "token", "client"), "oauth", "authentication"),
        (("password", "mfa", "securityquestion", "electronic"), "security", "authn-authz"),
        (("report", "analyze", "mining", "statistic", "monitoring"), "reporting", "analytics"),
        (("suggest", "messagecatalog", "config", "uiconfig", "objectconfig", "feature"), "platform", "configuration"),
        (("debug", "host", "server", "module", "iiq"), "platform", "diagnostics"),
        (("attachment", "export", "image", "redirect"), "platform", "content"),
        (("schema", "resourcetype", "serviceprovider"), "scim-discovery", "meta"),
        (("quicklink", "dynamic scope", "dynamicscope", "right", "scope"), "authorization", "rights-scopes"),
        (("provision",), "provisioning", "transactions"),
        (("batch",), "batch-requests", "lcm"),
        (("accessrequest", "requestaccess", "ai/", "accesshistory", "historical"), "access-requests", "lcm"),
        (("cam", "fam", "dataextract"), "integrations", "modules"),
    ]
    for keys, cat, sub in rules:
        if any(k in blob for k in keys):
            return cat, sub
    return "uncategorized", "other"


def media_values(ann) -> list[str]:
    if not ann:
        return []
    raw = ann.elements.get("value")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return [str(raw)]


def auth_hints_from(annos) -> list[str]:
    hints = []
    for a in annos:
        name = annotation_simple_name(a.type_desc)
        if name in ("AllowAll", "AllowAllAuthorizer"):
            hints.append("AllowAll")
        elif name in ("RequiredRight",):
            val = a.elements.get("value")
            hints.append(f"RequiredRight:{val}")
        elif name in ("Deferred",):
            hints.append("Deferred")
    return hints


def mine_class_bytes(data: bytes, source_jar: str) -> list[Endpoint]:
    try:
        cf = ClassFile(data)
    except ClassFileError:
        return []
    info = cf.info
    cn = info.this_class
    if "Resource" not in cn.split(".")[-1] and not cn.endswith("Service"):
        # Still consider classes with HTTP verb annotations
        has_http = False
        for m in info.methods:
            if any(annotation_simple_name(a.type_desc) in HTTP_VERBS for a in m.annotations):
                has_http = True
                break
        if not has_http:
            return []

    surface, mount = infer_mount(cn)
    class_path_ann = find_annotation(info.annotations, "Path")
    class_path = ""
    if class_path_ann:
        class_path = str(class_path_ann.elements.get("value") or "")

    class_produces = media_values(find_annotation(info.annotations, "Produces"))
    class_consumes = media_values(find_annotation(info.annotations, "Consumes"))
    class_auth = auth_hints_from(info.annotations)

    endpoints: list[Endpoint] = []
    for m in info.methods:
        if m.name in ("<init>", "<clinit>"):
            continue
        verb = None
        for a in m.annotations:
            sn = annotation_simple_name(a.type_desc)
            if sn in HTTP_VERBS:
                verb = sn
                break
        if not verb:
            continue
        method_path_ann = find_annotation(m.annotations, "Path")
        method_path = str(method_path_ann.elements.get("value") or "") if method_path_ann else ""
        produces = media_values(find_annotation(m.annotations, "Produces")) or class_produces
        consumes = media_values(find_annotation(m.annotations, "Consumes")) or class_consumes
        auth = class_auth + auth_hints_from(m.annotations)

        qparams: list[str] = []
        pparams_extra: list[str] = []
        for group in m.param_annotations:
            for a in group:
                sn = annotation_simple_name(a.type_desc)
                val = a.elements.get("value")
                if sn == "QueryParam" and val:
                    qparams.append(str(val))
                elif sn == "PathParam" and val:
                    pparams_extra.append(str(val))

        rel = join_paths(class_path, method_path)
        full = join_paths(mount, rel) if mount else rel
        category, subcategory = infer_category(cn, full)
        gaps = []
        if not class_path and not method_path:
            gaps.append("missing-path-annotation")
            # Sub-resource locator leaf: no absolute @Path on class/method.
            # Emit a synthetic placeholder path so the operation remains catalogued.
            synthetic = f"{{locator:{cn.rsplit('.', 1)[-1]}}}"
            rel = join_paths(synthetic)
            full = join_paths(mount, rel) if mount else rel
            gaps.append("subresource-locator-path-synthetic")
        if not produces:
            gaps.append("produces-unspecified")
        if verb in ("POST", "PUT", "PATCH") and not consumes:
            gaps.append("consumes-unspecified")
        gaps.append("response-schema-unknown")
        if verb in ("POST", "PUT", "PATCH"):
            gaps.append("request-schema-unknown")
        endpoints.append(
            Endpoint(
                surface=surface,
                mount=mount,
                category=category,
                subcategory=subcategory,
                http_method=verb,
                path=rel,
                full_path=full,
                class_name=cn,
                method_name=m.name,
                produces=produces,
                consumes=consumes,
                path_params=sorted(set(path_params_in(full) + pparams_extra)),
                query_params=sorted(set(qparams)),
                auth_hints=auth,
                source=source_jar,
                gaps=gaps,
            )
        )
    return endpoints


def mine_jar(jar_path: Path, include_prefixes: list[str] | None = None) -> list[Endpoint]:
    out: list[Endpoint] = []
    with zipfile.ZipFile(jar_path) as zf:
        for name in zf.namelist():
            if not name.endswith(".class") or "$" in name:
                continue
            if "/rest/" not in name and "scim" not in name:
                # still allow oauth/external already under rest/
                if not name.startswith("sailpoint/rest/"):
                    continue
            if include_prefixes and not any(name.startswith(p) for p in include_prefixes):
                continue
            data = zf.read(name)
            out.extend(mine_class_bytes(data, jar_path.name))
    return out


# --- pluginsrc source mining -------------------------------------------------

JAVA_CLASS_PATH_RE = re.compile(r"@Path\s*\(\s*\"([^\"]+)\"\s*\)\s*(?:\n|\r\n)\s*public\s+class\s+(\w+)", re.M)
JAVA_CLASS_PATH_RE2 = re.compile(
    r"@Path\s*\(\s*\"([^\"]+)\"\s*\)\s*(?:\n|\r\n)(?:\s*@\w+.*(?:\n|\r\n))*\s*public\s+class\s+(\w+)",
    re.M,
)
METHOD_BLOCK_RE = re.compile(
    r"(@(?:GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\b[\s\S]*?)"
    r"public\s+[\w<>,\s\[\].?]+\s+(\w+)\s*\(([^;{}]*?)\)\s*(?:throws\s+[\w\s,.]+)?\s*\{",
    re.M,
)
PATH_RE = re.compile(r"@Path\s*\(\s*\"([^\"]*)\"\s*\)")
PRODUCES_RE = re.compile(r"@Produces\s*\(\s*\{?\s*\"([^\"]+)\"")
CONSUMES_RE = re.compile(r"@Consumes\s*\(\s*\{?\s*\"([^\"]+)\"")
QUERY_RE = re.compile(r"@QueryParam\s*\(\s*\"([^\"]+)\"\s*\)")
PATHPARAM_RE = re.compile(r"@PathParam\s*\(\s*\"([^\"]+)\"\s*\)")
ALLOWALL_RE = re.compile(r"@AllowAll\b")
REQUIREDRIGHT_RE = re.compile(r"@RequiredRight\s*\(\s*\"([^\"]+)\"\s*\)")
PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)


def mine_java_source(path: Path) -> list[Endpoint]:
    text = path.read_text(encoding="utf-8", errors="replace")
    pkg_m = PACKAGE_RE.search(text)
    pkg = pkg_m.group(1) if pkg_m else ""
    class_path = ""
    class_name = path.stem
    m = JAVA_CLASS_PATH_RE2.search(text) or JAVA_CLASS_PATH_RE.search(text)
    if m:
        class_path, class_name = m.group(1), m.group(2)
    else:
        # fallback: first @Path before class
        cm = re.search(r"@Path\s*\(\s*\"([^\"]+)\"\s*\)", text)
        if cm:
            class_path = cm.group(1)
        cm2 = re.search(r"public\s+class\s+(\w+)", text)
        if cm2:
            class_name = cm2.group(1)

    fqcn = f"{pkg}.{class_name}" if pkg else class_name
    plugin = path.parts[path.parts.index("pluginsrc") + 1] if "pluginsrc" in path.parts else "plugin"
    endpoints: list[Endpoint] = []

    for block in METHOD_BLOCK_RE.finditer(text):
        header, method_name, params = block.group(1), block.group(2), block.group(3)
        verb_m = re.search(r"@(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\b", header)
        if not verb_m:
            continue
        verb = verb_m.group(1)
        pm = PATH_RE.search(header)
        method_path = pm.group(1) if pm else ""
        produces = PRODUCES_RE.findall(header)
        consumes = CONSUMES_RE.findall(header)
        qparams = QUERY_RE.findall(header + params)
        pparams = PATHPARAM_RE.findall(header + params)
        auth = []
        if ALLOWALL_RE.search(header):
            auth.append("AllowAll")
        for rr in REQUIREDRIGHT_RE.findall(header):
            auth.append(f"RequiredRight:{rr}")

        rel = join_paths(class_path, method_path)
        full = join_paths("/plugin/rest", rel)
        cat, sub = infer_category(fqcn, full)
        # Meridian toolkit special-case
        if "mnb" in plugin.lower() or "meridian" in fqcn.lower():
            cat, sub = "meridian-toolkit", "custom-plugin"

        gaps = ["response-schema-partial"]
        if verb in ("POST", "PUT", "PATCH"):
            gaps.append("request-schema-partial")
        endpoints.append(
            Endpoint(
                surface="plugins",
                mount="/plugin/rest",
                category=cat if plugin.startswith("mnb") else f"plugin:{plugin}",
                subcategory=sub,
                http_method=verb,
                path=rel,
                full_path=full,
                class_name=fqcn,
                method_name=method_name,
                produces=produces or ["application/json"],
                consumes=consumes,
                path_params=sorted(set(path_params_in(full) + pparams)),
                query_params=sorted(set(qparams)),
                auth_hints=auth,
                source=str(path.relative_to(ROOT)),
                gaps=gaps,
            )
        )
    return endpoints


def mine_pluginsrc(root: Path) -> list[Endpoint]:
    out: list[Endpoint] = []
    if not root.exists():
        return out
    for java in root.rglob("*.java"):
        if "/rest/" not in str(java).replace("\\", "/") and "Rest" not in java.name:
            # still try files under plugin rest packages
            if "plugin" not in str(java).lower():
                continue
        out.extend(mine_java_source(java))
    return out


def summarize(endpoints: list[Endpoint]) -> dict[str, Any]:
    by_surface = Counter(e.surface for e in endpoints)
    by_category = Counter(e.category for e in endpoints)
    by_method = Counter(e.http_method for e in endpoints)
    gap_counts = Counter(g for e in endpoints for g in e.gaps)
    return {
        "endpoint_count": len(endpoints),
        "by_surface": dict(sorted(by_surface.items())),
        "by_category": dict(sorted(by_category.items(), key=lambda x: (-x[1], x[0]))),
        "by_http_method": dict(sorted(by_method.items())),
        "gap_counts": dict(sorted(gap_counts.items(), key=lambda x: (-x[1], x[0]))),
        "unique_full_paths": len({(e.http_method, e.full_path) for e in endpoints}),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--war-lib", type=Path, default=DEFAULT_WAR_LIB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    jars = {
        "ootb+ui+oauth+external+plugin-fw": args.war_lib / "identityiq.jar",
        "scim": args.war_lib / "scim-server.jar",
    }
    endpoints: list[Endpoint] = []
    sources_used: list[str] = []
    errors: list[str] = []

    for label, jar in jars.items():
        if not jar.exists():
            errors.append(f"missing jar: {jar}")
            continue
        sources_used.append(str(jar.relative_to(ROOT)) if jar.is_relative_to(ROOT) else str(jar))
        print(f"Mining {jar.name} ({label})…")
        endpoints.extend(mine_jar(jar))

    print("Mining pluginsrc…")
    plugin_eps = mine_pluginsrc(PLUGINSRC)
    endpoints.extend(plugin_eps)
    sources_used.append("pluginsrc/")

    # Deduplicate exact duplicates (same method/path/class)
    dedup: dict[tuple, Endpoint] = {}
    for e in endpoints:
        key = (e.http_method, e.full_path, e.class_name, e.method_name)
        dedup[key] = e
    endpoints = list(dedup.values())
    endpoints.sort(key=lambda e: (e.surface, e.category, e.full_path, e.http_method))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "iiq_version_hint": "8.5",
        "technique": [
            "java-classfile-constant-pool",
            "RuntimeVisibleAnnotations",
            "RuntimeVisibleParameterAnnotations",
            "pluginsrc-java-source-ast-lite",
            "web.xml-mount-map",
        ],
        "sources": sources_used,
        "errors": errors,
        "summary": summarize(endpoints),
        "endpoints": [asdict(e) for e in endpoints],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} ({len(endpoints)} endpoints)")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
