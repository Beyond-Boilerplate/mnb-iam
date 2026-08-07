#!/usr/bin/env python3
"""Backup live Meridian IIQ objects (extract plugin / MCP), then wipe for a clean seed.

Opt-in destructive path: export MNB-* XML → lab-data/backups/iiq-<ts>/ → wipe academy
leftovers (keeps spadmin + MNB-Rule-Hello-World) → caller re-seeds.

Default lab up/seed overlays without calling this. Use:
  ./tools/lab/docker/up.sh --wipe
  ./tools/lab/scripts/seed-mnb-lab-data.sh --wipe
  ./tools/lab/scripts/backup-and-reset-lab.sh

Uses the toolkit objects/export path via MCP tool export_sailpoint_object.

Examples:

  export MCP_API_KEY=mnb-lab-mcp-key
  ./tools/lab/scripts/backup-and-reset-lab.sh

  # Backup only (no wipe)
  python3 tools/lab/scripts/backup_and_reset_lab.py --backup-only

  # Explicit no-op (overlay callers)
  python3 tools/lab/scripts/backup_and_reset_lab.py --keep-existing
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
CHAT_ROOT = REPO / "tools" / "iiq-chat"
sys.path.insert(0, str(CHAT_ROOT))

from mcp_client import McpClient, McpError  # noqa: E402

WIPE_RULE = REPO / "tools" / "iiq-verify" / "MNB-Rule-E2E-WipeAcademy.xml"
BACKUP_ROOT = REPO / "lab-data" / "backups"
KEEP_RULES = frozenset({"MNB-Rule-Hello-World"})

# config/<Type>/MNB-*.xml → SailPoint class simple name
CONFIG_CLASS_DIRS = (
    "Application",
    "Bundle",
    "Rule",
    "Workflow",
    "TaskDefinition",
    "Policy",
    "QuickLink",
    "IdentityTrigger",
    "CertificationDefinition",
    "PasswordPolicy",
    "CorrelationConfig",
    "EmailTemplate",
)

NAME_ATTR = re.compile(
    r"<(Application|Bundle|Rule|Workflow|TaskDefinition|Policy|QuickLink|"
    r"IdentityTrigger|CertificationDefinition|PasswordPolicy|CorrelationConfig|"
    r"EmailTemplate)\b[^>]*\bname=\"([^\"]+)\"",
    re.I,
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
    return None


def _scrub_ids(xml: str) -> str:
    xml = re.sub(r'\s(id|created|modified|significantModified)="[^"]*"', "", xml)
    if not xml.lstrip().startswith("<?xml"):
        xml = "<?xml version='1.0' encoding='UTF-8'?>\n" + xml
    if not xml.endswith("\n"):
        xml += "\n"
    return xml


def iiq_name_from_config(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None
    m = NAME_ATTR.search(text)
    return m.group(2) if m else None


def discover_from_config() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for class_dir in CONFIG_CLASS_DIRS:
        d = REPO / "config" / class_dir
        if not d.is_dir():
            continue
        for path in sorted(d.glob("MNB-*.xml")):
            name = iiq_name_from_config(path)
            if not name:
                continue
            if class_dir == "Rule" and name in KEEP_RULES:
                continue
            key = (class_dir, name)
            if key in seen:
                continue
            seen.add(key)
            found.append(key)
    return found


def discover_live_apps(mcp: McpClient) -> list[tuple[str, str]]:
    result = mcp.call("list_applications", {"query": "MNB", "count": 200})
    data = result.get("data") if isinstance(result, dict) else {}
    items = (data or {}).get("items") or (data or {}).get("Resources") or []
    out: list[tuple[str, str]] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if name.startswith("MNB-"):
            out.append(("Application", name))
    return out


def count_live_mnb_apps(mcp: McpClient) -> int:
    return len(discover_live_apps(mcp))


def backup_objects(mcp: McpClient, dest: Path) -> dict[str, Any]:
    dest.mkdir(parents=True, exist_ok=True)
    targets: dict[tuple[str, str], None] = {}
    for pair in discover_from_config():
        targets[pair] = None
    for pair in discover_live_apps(mcp):
        targets[pair] = None

    exported: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []

    _log(f"Backing up up to {len(targets)} object(s) → {dest.relative_to(REPO)}")
    for class_name, name in sorted(targets.keys()):
        try:
            result = mcp.call(
                "export_sailpoint_object",
                {"class_name": class_name, "name": name},
            )
        except McpError as exc:
            failed.append({"className": class_name, "name": name, "error": str(exc)})
            _log(f"  FAIL {class_name}/{name}: {exc}")
            continue

        if isinstance(result, dict) and result.get("ok") is False:
            err = result.get("error") if isinstance(result.get("error"), dict) else {}
            code = str(err.get("code") or "")
            status = err.get("http_status")
            msg = str(err.get("message") or result)
            if code == "not_found" or status == 404 or "not found" in msg.lower():
                missing.append({"className": class_name, "name": name})
                continue
            failed.append({"className": class_name, "name": name, "error": msg[:300]})
            _log(f"  FAIL {class_name}/{name}: {msg[:200]}")
            continue

        xml = _extract_xml(result)
        if not xml:
            failed.append({"className": class_name, "name": name, "error": "no xml"})
            continue

        out_dir = dest / class_name
        out_dir.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w.\-]+", "_", name)
        out_path = out_dir / f"{safe}.xml"
        out_path.write_text(_scrub_ids(xml), encoding="utf-8")
        exported.append(
            {
                "className": class_name,
                "name": name,
                "path": str(out_path.relative_to(REPO)),
            }
        )
        _log(f"  OK   {class_name}/{name}")

    manifest = {
        "created": datetime.now(timezone.utc).isoformat(),
        "exportedCount": len(exported),
        "missingCount": len(missing),
        "failedCount": len(failed),
        "exported": exported,
        "missing": missing,
        "failed": failed,
    }
    (dest / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    _log(
        f"Backup summary: exported={len(exported)} missing={len(missing)} "
        f"failed={len(failed)}"
    )
    return manifest


def docker_iiq_running() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return "mnb-identityiq" in (proc.stdout or "").splitlines()


def wipe_via_docker(container: str = "mnb-identityiq") -> None:
    if not WIPE_RULE.is_file():
        raise SystemExit(f"Missing wipe rule: {WIPE_RULE}")
    if not docker_iiq_running():
        raise SystemExit(
            "Container mnb-identityiq is not running — cannot wipe. "
            "Start the stack first, or use tools/iiq-verify/wipe-mnb-leftovers.sh"
        )

    _log(f"Wiping Meridian leftovers via docker exec ({container})...")
    subprocess.run(
        ["docker", "cp", str(WIPE_RULE), f"{container}:/tmp/MNB-Rule-E2E-WipeAcademy.xml"],
        check=True,
    )
    proc = subprocess.run(
        [
            "docker",
            "exec",
            container,
            "sh",
            "-c",
            "cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin && "
            "./iiq console iiqBeans <<'EOF'\n"
            "import /tmp/MNB-Rule-E2E-WipeAcademy.xml\n"
            "rule MNB-Rule-E2E-WipeAcademy\n"
            "EOF",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise SystemExit(f"Wipe failed (exit {proc.returncode}):\n{out[-3000:]}")
    # Surface a short digest
    for line in out.splitlines():
        if "OK wiped" in line or line.startswith("DEL ") or line.startswith("SCAN "):
            _log(f"  {line}")
    if "OK wiped" not in out:
        _log(out[-1500:] if out else "(no console output)")
    _log("Wipe finished (kept spadmin + MNB-Rule-Hello-World).")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--keep-existing",
        action="store_true",
        help="No-op: skip backup and wipe (overlay seed on current objects)",
    )
    p.add_argument(
        "--backup-only",
        action="store_true",
        help="Export to lab-data/backups/ only; do not wipe",
    )
    p.add_argument(
        "--wipe-only",
        action="store_true",
        help="Skip backup; wipe Meridian leftovers only",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Backup+wipe even when no MNB applications are present",
    )
    p.add_argument(
        "--backup-dir",
        default="",
        help="Override backup directory (default lab-data/backups/iiq-<timestamp>)",
    )
    p.add_argument(
        "--container",
        default=os.environ.get("IIQ_DOCKER_CONTAINER", "mnb-identityiq"),
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

    if args.keep_existing or os.environ.get("MNB_LAB_KEEP_EXISTING", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        _log("Keeping existing IIQ objects (--keep-existing / MNB_LAB_KEEP_EXISTING)")
        return 0

    if args.backup_only and args.wipe_only:
        _log("FAIL: use only one of --backup-only / --wipe-only")
        return 2

    do_backup = not args.wipe_only
    do_wipe = not args.backup_only

    mcp = McpClient(url=args.mcp_url, api_key=args.mcp_api_key, timeout=120.0)
    try:
        mcp.init()
    except McpError as exc:
        _log(f"FAIL MCP init: {exc}")
        return 1

    app_count = 0
    try:
        app_count = count_live_mnb_apps(mcp)
    except McpError as exc:
        _log(f"WARN list_applications failed: {exc}")

    if app_count == 0 and not args.force and not args.wipe_only:
        _log("No MNB-* applications in live IIQ — skip backup/wipe (greenfield)")
        if do_wipe and args.force:
            pass
        else:
            return 0

    _log(f"Live MNB-* applications: {app_count}")

    if do_backup:
        if args.backup_dir:
            dest = Path(args.backup_dir)
            if not dest.is_absolute():
                dest = REPO / dest
        else:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            dest = BACKUP_ROOT / f"iiq-{stamp}"
        try:
            backup_objects(mcp, dest)
        except McpError as exc:
            _log(f"FAIL backup: {exc}")
            return 1
        _log(f"Backup written under {dest}")

    if do_wipe:
        try:
            wipe_via_docker(args.container)
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            _log(f"FAIL wipe: {exc}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
