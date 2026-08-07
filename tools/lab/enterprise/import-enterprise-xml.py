#!/usr/bin/env python3
"""Import Enterprise Lab durable XML via MCP (same client as seed_mnb_lab_data)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPTS = REPO / "tools" / "lab" / "scripts"
CHAT = REPO / "tools" / "iiq-chat"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(CHAT))

from mcp_client import McpClient, McpError  # noqa: E402

FILES = [
    "config/Application/MNB-Application-Workday.xml",
    "config/Application/MNB-Application-ActiveDirectory-Live.xml",
    "config/Application/MNB-Application-Okta.xml",
    "config/Application/MNB-Application-Keycloak-IdP.xml",
    "config/Application/MNB-Application-CoreBanking.xml",
    "config/Application/MNB-Application-Salesforce-CRM-Live.xml",
    "config/Application/MNB-Application-ServiceNow.xml",
    "config/Application/MNB-Application-EntraID.xml",
    "config/Application/MNB-Application-PAM-CyberArk.xml",
    "config/IdentityTrigger/MNB-IdentityTrigger-Joiner.xml",
    "config/IdentityTrigger/MNB-IdentityTrigger-Leaver.xml",
    "config/Workflow/MNB-Workflow-Joiner.xml",
    "config/Workflow/MNB-Workflow-Leaver.xml",
    "config/Workflow/MNB-Workflow-Access-Approval.xml",
    "config/Bundle/MNB-Bundle-Birthright-Employee.xml",
    "config/Bundle/MNB-Bundle-Wire-Initiator.xml",
    "config/Bundle/MNB-Bundle-Workstation-Access.xml",
    "config/Bundle/MNB-Bundle-HR-Intranet.xml",
    "config/Bundle/MNB-Bundle-Finance-Portal.xml",
    "config/Bundle/MNB-Bundle-BreakGlass-Cloud.xml",
    "config/PasswordPolicy/MNB-PasswordPolicy-Lab.xml",
    "config/QuickLink/MNB-QuickLink-Request-Access.xml",
    "config/QuickLink/MNB-QuickLink-Work-Items.xml",
    "config/QuickLink/MNB-QuickLink-Certifications.xml",
    "config/QuickLink/MNB-QuickLink-Employee-Portal.xml",
    "config/QuickLink/MNB-QuickLink-Toolkit-Console.xml",
    "config/CertificationDefinition/MNB-CertificationDefinition-Manager.xml",
    "config/CertificationDefinition/MNB-CertificationDefinition-AppOwner-Wire.xml",
]


SOFT_FAIL_PREFIXES = (
    "config/IdentityTrigger/",
    "config/CertificationDefinition/",
)


def main() -> int:
    url = os.environ.get("IIQ_MCP_URL") or os.environ.get("MCP_URL") or "http://127.0.0.1:8766/mcp"
    key = os.environ.get("MCP_API_KEY", "mnb-lab-mcp-key")
    mcp = McpClient(url, api_key=key)
    ok = 0
    fail = 0
    soft = 0
    for rel in FILES:
        path = REPO / rel
        if not path.is_file():
            print(f"  skip missing {rel}")
            continue
        try:
            result = mcp.call(
                "import_sailpoint_object",
                {
                    "xml": path.read_text(encoding="utf-8"),
                    "scrub_ids": True,
                    "justification": f"enterprise seed {path.name}",
                },
            )
            if isinstance(result, dict) and result.get("ok") is False:
                if rel.startswith(SOFT_FAIL_PREFIXES):
                    print(f"  soft-fail {rel} (use importdynamic): {json.dumps(result, default=str)[:200]}")
                    soft += 1
                else:
                    print(f"  FAIL {rel}: {json.dumps(result, default=str)[:300]}")
                    fail += 1
            else:
                print(f"  imported {rel}: {json.dumps(result, default=str)[:200]}")
                ok += 1
        except (McpError, Exception) as e:  # noqa: BLE001
            if rel.startswith(SOFT_FAIL_PREFIXES):
                print(f"  soft-fail {rel}: {e}")
                soft += 1
            else:
                print(f"  FAIL {rel}: {e}")
                fail += 1
    print(f"enterprise import finished ({ok} ok, {fail} fail, {soft} soft)")
    if soft:
        print(
            "Note: IdentityTrigger/CertificationDefinition XML is durable in config/; "
            "import via SSD importdynamic — docs/enterprise/RUNBOOK.md"
        )
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
