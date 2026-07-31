"""Generate ``op_index.json`` from mined IIQ OpenAPI YAML specs."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# tools/iiq-mcp/src/iiq_mcp/client/generate_index.py → Sailpoint repo root is parents[5]
REPO_ROOT = Path(__file__).resolve().parents[5]
OPENAPI_DIR = REPO_ROOT / "docs" / "api" / "openapi"
OUT_PATH = Path(__file__).with_name("op_index.json")

SPECS: list[tuple[str, str, str]] = [
    # (filename, surface, mount_prefix under IIQ)
    ("openapi-scim-v2.yaml", "scim", "/scim/v2"),
    ("openapi-ootb-rest.yaml", "ootb-rest", "/rest"),
    ("openapi-plugins.yaml", "plugins", "/plugin/rest"),
]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _collect(spec_path: Path, surface: str, mount: str) -> list[dict[str, Any]]:
    doc = _load_yaml(spec_path)
    paths = doc.get("paths") or {}
    ops: list[dict[str, Any]] = []
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.startswith("x-") or method in ("parameters", "summary", "description", "servers"):
                continue
            if not isinstance(op, dict):
                continue
            operation_id = op.get("operationId") or f"{method}_{surface}_{path}"
            ops.append(
                {
                    "operationId": operation_id,
                    "method": method.lower(),
                    "path": path if path.startswith("/") else f"/{path}",
                    "mount": mount,
                    "surface": surface,
                    "tags": list(op.get("tags") or []),
                    "summary": op.get("summary"),
                }
            )
    return ops


def generate(out: Path = OUT_PATH, openapi_dir: Path = OPENAPI_DIR) -> dict[str, Any]:
    operations: list[dict[str, Any]] = []
    surfaces: dict[str, int] = {}
    for filename, surface, mount in SPECS:
        path = openapi_dir / filename
        if not path.exists():
            print(f"warning: missing {path}", file=sys.stderr)
            continue
        batch = _collect(path, surface, mount)
        operations.extend(batch)
        surfaces[surface] = len(batch)

    by_id = {o["operationId"]: o for o in operations}
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(openapi_dir),
        "surfaces": surfaces,
        "operation_count": len(operations),
        "operations": operations,
        "by_operation_id": by_id,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    payload = generate()
    print(
        f"Wrote {OUT_PATH} — {payload['operation_count']} operations "
        f"across {payload['surfaces']}"
    )


if __name__ == "__main__":
    main()
