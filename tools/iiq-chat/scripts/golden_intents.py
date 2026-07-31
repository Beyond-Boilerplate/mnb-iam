#!/usr/bin/env python3
"""Golden IAM intents — MCP tool traces (and optional Teller agent mocks).

Run against a live lab MCP:

  IIQ_MCP_URL=http://127.0.0.1:8766/mcp MCP_API_KEY=mnb-lab-mcp-key \\
    python3 tools/iiq-chat/scripts/golden_intents.py

Unit mode (no MCP): 

  python3 -m pytest tools/iiq-chat/tests/test_golden_intents.py -q
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp_client import McpClient, McpError  # noqa: E402

# Utterance → preferred first tool(s) for documentation / eval harness.
GOLDEN_INTENTS: list[dict[str, Any]] = [
    {
        "id": "nl-who-anita",
        "utterance": "Who is Anita Rao?",
        "tools": ["search_identities", "get_identity"],
        "mcp_probe": ("search_identities", {"query": "Anita Rao", "count": 10}),
    },
    {
        "id": "nl-anyone-anita",
        "utterance": "Do I have anyone named Anita?",
        "tools": ["search_identities"],
        "mcp_probe": ("search_identities", {"query": "Anita", "count": 15}),
    },
    {
        "id": "nl-paris",
        "utterance": "Find me all employees in Paris",
        "tools": ["search_profiles", "search_identities"],
        "mcp_probe": ("search_profiles", {"query": "Paris", "count": 25}),
    },
    {
        "id": "ldap-onboard",
        "utterance": "Onboard OpenLDAP app MNB-OpenLDAP with provision bind",
        "tools": ["onboard_application", "create_application"],
        "mcp_probe": None,  # write — dry-run docs only unless --write
        "write_args": {
            "tool": "onboard_application",
            "arguments": {
                "name": "MNB-OpenLDAP",
                "type": "OpenLDAP - Direct",
                "overwrite": True,
                "run_aggregate": True,
                "attributes": {
                    "host": "openldap",
                    "port": "389",
                    "user": "cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com",
                    "password": "Provision1!",
                    "searchDN": "dc=meridiannb,dc=com",
                },
                "justification": "golden_intents pilot",
            },
        },
    },
    {
        "id": "grant-access",
        "utterance": "Give anita.rao access to a requestable role",
        "tools": ["grant_access", "get_requestable_items", "create_access_request"],
        "mcp_probe": ("get_requestable_items", {"identity": "anita.rao"}),
        "write_args": {
            "tool": "grant_access",
            "arguments": {
                "identity": "anita.rao",
                "access_name": "Wire Initiator",
                "access_type": "role",
                "justification": "golden_intents pilot",
            },
        },
    },
    {
        "id": "unlock",
        "utterance": "Unlock anita.rao",
        "tools": ["unlock_iiq_identity"],
        "mcp_probe": None,
        "write_args": {
            "tool": "unlock_iiq_identity",
            "arguments": {"identity_name": "anita.rao", "justification": "golden_intents"},
        },
    },
    {
        "id": "cert-list",
        "utterance": "List certifications I can decide",
        "tools": ["list_certifications"],
        "mcp_probe": ("list_certifications", {"count": 10}),
    },
    {
        "id": "sod-count",
        "utterance": "How many open SoD violations are there?",
        "tools": ["count_open_sod_violations"],
        "mcp_probe": ("count_open_sod_violations", {}),
    },
]


def run_probes(
    call: Callable[[str, dict[str, Any]], Any],
    *,
    do_writes: bool = False,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for intent in GOLDEN_INTENTS:
        row: dict[str, Any] = {
            "id": intent["id"],
            "utterance": intent["utterance"],
            "expected_tools": intent["tools"],
        }
        probe = intent.get("mcp_probe")
        if do_writes and intent.get("write_args"):
            wa = intent["write_args"]
            try:
                row["result"] = call(wa["tool"], wa["arguments"])
                row["ok"] = True
                row["wrote"] = True
            except Exception as exc:  # noqa: BLE001
                row["ok"] = False
                row["error"] = str(exc)
                row["wrote"] = True
        elif probe:
            name, args = probe
            try:
                row["result"] = call(name, args)
                row["ok"] = True
            except Exception as exc:  # noqa: BLE001
                row["ok"] = False
                row["error"] = str(exc)
        else:
            row["ok"] = True
            row["skipped"] = "write/no-probe (pass --write to execute)"
        results.append(row)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden IAM MCP intent probes")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Execute write intents (onboard, unlock)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    client = McpClient()
    try:
        tools = {t["name"] for t in client.list_tools()}
    except McpError as exc:
        print(f"MCP unavailable: {exc}", file=sys.stderr)
        return 2

    for intent in GOLDEN_INTENTS:
        if not any(t in tools for t in intent["tools"]):
            print(
                f"WARN: none of {intent['tools']} registered on MCP for {intent['id']}",
                file=sys.stderr,
            )

    rows = run_probes(client.call, do_writes=args.write)
    if args.json:
        print(json.dumps({"toolCount": len(tools), "intents": rows}, indent=2, default=str))
    else:
        print(f"MCP tools: {len(tools)}")
        for row in rows:
            status = "OK" if row.get("ok") else "FAIL"
            skip = row.get("skipped")
            err = row.get("error")
            extra = f" skip={skip}" if skip else ""
            if err:
                extra = f" error={err[:120]}"
            print(f"  [{status}] {row['id']}: {row['utterance']}{extra}")
        failed = [r for r in rows if not r.get("ok")]
        if failed:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
