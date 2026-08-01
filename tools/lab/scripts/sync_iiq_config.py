#!/usr/bin/env python3
"""Sync live IIQ UI objects → durable config/ XML (export → scrub → diff → write).

IIQ does not push UI edits into git. This is the pull path:

  live IIQ  --MCP export-->  scrubbed XML  --diff-->  config/
                                                  --write-->  update repo files

Examples:

  export MCP_API_KEY=mnb-lab-mcp-key
  export IIQ_MCP_URL=http://127.0.0.1:8766/mcp

  # Preview diffs only (default; exit 1 if drift)
  ./tools/lab/scripts/sync-iiq-config.sh

  # Apply UI changes into config/
  ./tools/lab/scripts/sync-iiq-config.sh --write

  # Also discover other MNB-* Applications not in the manifest
  ./tools/lab/scripts/sync-iiq-config.sh --discover --write

  # One object
  ./tools/lab/scripts/sync-iiq-config.sh --only MNB-OpenLDAP --write
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
CHAT_ROOT = REPO / "tools" / "iiq-chat"
sys.path.insert(0, str(CHAT_ROOT))

from mcp_client import McpClient, McpError  # noqa: E402

DEFAULT_LDAP_PASSWORD = os.environ.get("MNB_LDAP_PASSWORD", "Provision1!")


@dataclass(frozen=True)
class TrackedObject:
    class_name: str
    iiq_name: str
    rel_path: str  # under config/

    @property
    def path(self) -> Path:
        return REPO / "config" / self.rel_path


# Known Meridian lab objects (UI craft that seed re-imports).
MANIFEST: tuple[TrackedObject, ...] = (
    TrackedObject("Application", "MNB-HR", "Application/MNB-Application-HR.xml"),
    TrackedObject(
        "Application", "MNB-OpenLDAP", "Application/MNB-Application-OpenLDAP.xml"
    ),
    TrackedObject(
        "TaskDefinition",
        "MNB-Acct-Aggregation",
        "TaskDefinition/MNB-TaskDefinition-Acct-Aggregation.xml",
    ),
    TrackedObject(
        "TaskDefinition",
        "MNB-Daily-Aggr",
        "TaskDefinition/MNB-TaskDefinition-Daily-Aggr.xml",
    ),
    TrackedObject(
        "TaskDefinition",
        "MNB-OpenLDAP-Group-Aggregation",
        "TaskDefinition/MNB-TaskDefinition-OpenLDAP-Group-Aggregation.xml",
    ),
)


def _log(msg: str) -> None:
    print(msg, flush=True)


def _extract_xml(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        return None
    for key in ("xml", "objectXml", "serialized"):
        val = data.get(key)
        if isinstance(val, str) and "<" in val:
            return val
    for val in data.values():
        if isinstance(val, str) and val.lstrip().startswith("<?xml"):
            return val
        if isinstance(val, str) and re.search(r"<(Application|TaskDefinition|Rule)\b", val):
            return val
    return None


def scrub_xml(xml: str) -> str:
    """Normalize for durable config/ (no instance ids / run stats)."""
    xml = re.sub(r'\s(id|created|modified|significantModified)="[^"]*"', "", xml)
    xml = re.sub(
        r'(<Reference\s+class="[^"]+")\s+id="[^"]+"(\s+name="[^"]+"\s*/>)',
        r"\1\2",
        xml,
    )
    xml = re.sub(
        r'(<Reference\s+class="[^"]+")\s+id="[^"]+"(\s+name="[^"]+")',
        r"\1\2",
        xml,
    )
    xml = re.sub(
        r'\s*<entry key="acctAggregation(Start|End)"[^/]*/>\n?',
        "",
        xml,
    )
    xml = re.sub(
        r'\s*<entry key="acctAggregation(Start|End)">.*?</entry>\n?',
        "",
        xml,
        flags=re.S,
    )
    for key in (
        "TaskDefinition.runLengthAverage",
        "TaskDefinition.runLengthTotal",
        "TaskDefinition.runs",
    ):
        xml = re.sub(rf'\s*<entry key="{re.escape(key)}"[^/]*/>\n?', "", xml)
    # Keep Map/entry layout stable across exports (avoid false diffs).
    xml = re.sub(r"(<Map>)\s*(<entry)", r"\1\n      \2", xml)
    xml = re.sub(r"(/>)\s*(<entry key=)", r"\1\n      \2", xml)
    if not xml.lstrip().startswith("<?xml"):
        xml = "<?xml version='1.0' encoding='UTF-8'?>\n" + xml
    if not xml.endswith("\n"):
        xml += "\n"
    return xml


class ExportNotFound(RuntimeError):
    pass


def export_object(mcp: McpClient, obj: TrackedObject) -> str:
    result = mcp.call(
        "export_sailpoint_object",
        {"class_name": obj.class_name, "name": obj.iiq_name},
    )
    if isinstance(result, dict) and result.get("ok") is False:
        err = result.get("error") if isinstance(result.get("error"), dict) else {}
        code = str(err.get("code") or "")
        status = err.get("http_status")
        msg = str(err.get("message") or result)
        if code == "not_found" or status == 404 or "not found" in msg.lower():
            raise ExportNotFound(msg)
        raise SystemExit(
            f"FAIL export {obj.class_name}/{obj.iiq_name}: "
            f"{json.dumps(result, default=str)[:600]}"
        )
    xml = _extract_xml(result)
    if not xml:
        raise SystemExit(
            f"FAIL no XML in export for {obj.class_name}/{obj.iiq_name}: "
            f"{json.dumps(result, default=str)[:600]}"
        )
    return xml


def hygiene_openldap(xml: str, *, existing: str | None) -> str:
    """Lab-specific fixes so exports stay importable after volume wipe."""
    # Prefer existing plaintext password over instance-bound 1:ACP: ciphertext.
    existing_pw = None
    if existing:
        m = re.search(r'<entry key="password" value="([^"]*)"/>', existing)
        if m and not m.group(1).startswith("1:ACP:"):
            existing_pw = m.group(1)
    pw = existing_pw or DEFAULT_LDAP_PASSWORD
    xml = re.sub(
        r'<entry key="password" value="[^"]*"/>',
        f'<entry key="password" value="{pw}"/>',
        xml,
        count=1,
    )

    # Schema objectType is "group"; connector reads group.searchDNs (not groupOfNames.*).
    if "groupOfNames.searchDNs" in xml:
        xml = xml.replace("groupOfNames.searchDNs", "group.searchDNs")
        xml = xml.replace('objectType" value="groupOfNames"', 'objectType" value="group"')
        xml = re.sub(
            r'(<entry key="group\.searchDNs">[\s\S]*?<entry key="iterateSearchFilter")\s*/>',
            r'\1 value="(objectClass=groupOfUniqueNames)"/>',
            xml,
            count=1,
        )
    return xml


def post_process(obj: TrackedObject, xml: str, *, existing: str | None) -> str:
    xml = scrub_xml(xml)
    if obj.iiq_name == "MNB-OpenLDAP" or "OpenLDAP" in obj.rel_path:
        xml = hygiene_openldap(xml, existing=existing)
    return xml


def unified_diff(path: Path, old: str, new: str) -> str:
    a = old.splitlines(keepends=True)
    b = new.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            a,
            b,
            fromfile=f"a/{path.relative_to(REPO)}",
            tofile=f"b/{path.relative_to(REPO)}",
        )
    )


def discover_applications(mcp: McpClient, known: set[str]) -> list[TrackedObject]:
    result = mcp.call("list_applications", {"query": "MNB", "count": 100})
    data = result.get("data") if isinstance(result, dict) else {}
    items = (data or {}).get("items") or (data or {}).get("Resources") or []
    found: list[TrackedObject] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name.startswith("MNB-") or name in known:
            continue
        suffix = name[4:]  # strip MNB-
        rel = f"Application/MNB-Application-{suffix}.xml"
        found.append(TrackedObject("Application", name, rel))
    return found


def select_objects(
    mcp: McpClient | None,
    *,
    discover: bool,
    only: set[str] | None,
) -> list[TrackedObject]:
    objs = list(MANIFEST)
    known = {o.iiq_name for o in objs}
    if discover:
        if mcp is None:
            raise SystemExit("--discover requires MCP")
        extra = discover_applications(mcp, known)
        if extra:
            _log(f"Discovered {len(extra)} extra Application(s):")
            for o in extra:
                _log(f"  + {o.iiq_name} → config/{o.rel_path}")
            objs.extend(extra)
    if only:
        objs = [
            o
            for o in objs
            if o.iiq_name in only or o.rel_path in only or Path(o.rel_path).name in only
        ]
        if not objs:
            raise SystemExit(f"No manifest entries matched --only {sorted(only)}")
    return objs


def sync_one(
    mcp: McpClient,
    obj: TrackedObject,
    *,
    write: bool,
    show_diff: bool,
) -> str:
    """Return status: unchanged | created | updated | missing_live."""
    try:
        raw = export_object(mcp, obj)
    except ExportNotFound:
        _log(f"  SKIP {obj.iiq_name} (not in live IIQ)")
        return "missing_live"

    existing = obj.path.read_text(encoding="utf-8") if obj.path.is_file() else None
    # Normalize on-disk copy the same way so layout-only churn does not look like drift.
    old_xml = scrub_xml(existing) if existing is not None else ""
    new_xml = post_process(obj, raw, existing=existing)

    if old_xml == new_xml:
        _log(f"  OK   {obj.rel_path} (unchanged)")
        return "unchanged"

    status = "created" if existing is None else "updated"
    _log(f"  DIFF {obj.rel_path} ({status})")
    diff = unified_diff(obj.path, existing or "", new_xml)
    if show_diff and diff:
        print(diff)

    if write:
        obj.path.parent.mkdir(parents=True, exist_ok=True)
        obj.path.write_text(new_xml, encoding="utf-8")
        _log(f"  WRITE config/{obj.rel_path}")
    return status


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--check",
        action="store_true",
        default=True,
        help="Diff only; exit 1 if drift (default)",
    )
    p.add_argument(
        "--write",
        action="store_true",
        help="Write scrubbed exports into config/",
    )
    p.add_argument(
        "--discover",
        action="store_true",
        help="Also track MNB-* Applications not in the built-in manifest",
    )
    p.add_argument(
        "--only",
        action="append",
        default=[],
        help="Limit to IIQ name or config basename (repeatable)",
    )
    p.add_argument(
        "--no-diff",
        action="store_true",
        help="Do not print unified diffs (summary only)",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="Print tracked objects and exit",
    )
    p.add_argument(
        "--mcp-url",
        default=os.environ.get("IIQ_MCP_URL", "http://127.0.0.1:8766/mcp"),
    )
    p.add_argument(
        "--mcp-api-key",
        default=os.environ.get("MCP_API_KEY")
        or os.environ.get("IIQ_MCP_API_KEY")
        or "mnb-lab-mcp-key",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    only = set(args.only) if args.only else None

    if args.list:
        for o in select_objects(None, discover=False, only=only):
            exists = "yes" if o.path.is_file() else "no"
            _log(f"{o.class_name:16} {o.iiq_name:40} config/{o.rel_path}  (on disk: {exists})")
        return 0

    mcp = McpClient(url=args.mcp_url, api_key=args.mcp_api_key, timeout=120.0)
    try:
        mcp.init()
    except McpError as exc:
        _log(f"FAIL MCP init: {exc}")
        return 1

    objs = select_objects(mcp, discover=args.discover, only=only)
    _log(f"Syncing {len(objs)} object(s) from live IIQ → config/")
    if args.write:
        _log("Mode: WRITE (will update config/)")
    else:
        _log("Mode: CHECK (diff only; pass --write to update config/)")

    counts = {"unchanged": 0, "updated": 0, "created": 0, "missing_live": 0}
    for obj in objs:
        try:
            status = sync_one(
                mcp,
                obj,
                write=args.write,
                show_diff=not args.no_diff,
            )
        except McpError as exc:
            _log(f"FAIL {obj.iiq_name}: {exc}")
            return 1
        counts[status] = counts.get(status, 0) + 1

    drifted = counts["updated"] + counts["created"]
    _log(
        f"\nSummary: unchanged={counts['unchanged']} updated={counts['updated']} "
        f"created={counts['created']} missing_live={counts['missing_live']}"
    )
    if args.write:
        _log("config/ updated. Review with: git diff -- config/")
        return 0
    if drifted:
        _log("Drift detected. Re-run with --write to import UI changes into config/.")
        return 1
    _log("config/ matches live IIQ (for tracked objects).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
