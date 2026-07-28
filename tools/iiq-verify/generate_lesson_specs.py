#!/usr/bin/env python3
"""Generate lesson-specs for Meridian academy lessons missing JSON specs.

Derives object.exists / task / identity checks from acceptance criteria and a
curated map. Paper-heavy lessons still require IIQ reachable + prerequisite
Meridian objects so Verify now cannot be skipped with empty checks.

Usage:
  python3 tools/iiq-verify/generate_lesson_specs.py
  python3 tools/iiq-verify/generate_lesson_specs.py --overwrite
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "docs" / "lessons"
SPECS = Path(__file__).resolve().parent / "lesson-specs"

# Curated primary Application / Bundle / Rule / etc. per lesson (authoritative names).
CURATED: dict[int, list[dict]] = {
    11: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-CoreBanking"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Aggregate MNB-CoreBanking"},
    ],
    12: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-SAP-Finance"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Aggregate MNB-SAP-Finance"},
        {"type": "identity.exists", "name": "jordan.reed"},
    ],
    13: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Aggregate MNB-AWS-Cloud"},
        {"type": "identity.exists", "name": "jordan.reed"},
    ],
    14: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Aggregate MNB-WirePortal"},
        {"type": "identity.exists", "name": "priya.wire"},
        {"type": "identity.exists", "name": "marcus.approve"},
    ],
    15: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-Salesforce-CRM"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-InternetBanking"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-Ecommerce-Ops"},
    ],
    16: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-CoreBanking"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Refresh MNB Attributes"},
        {"type": "identity.countMin", "min": 50},
    ],
    17: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "identity.exists", "name": "priya.wire"},
    ],
    18: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
    ],
    19: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
    ],
    20: [
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Terminated-With-Access",
         "alternateClasses": ["Population", "GroupFactory"]},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
    ],
    21: [
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Refresh MNB Managers"},
        {"type": "identity.exists", "name": "priya.wire"},
    ],
    22: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Refresh MNB Attributes"},
        {"type": "identity.attr", "name": "helen.ross", "attr": "email", "contains": "@"},
    ],
    23: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-Birthright-Employee"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-IT-Directory-User"},
    ],
    24: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "identity.exists", "name": "helen.ross"},
    ],
    25: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Finance",
         "alternateClasses": ["Population"]},
    ],
    26: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-IT-Directory-User"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
    ],
    27: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Refresh MNB Attributes"},
    ],
    28: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-CloudAdmin"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-BreakGlass"},
    ],
    29: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
    ],
    30: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Refresh MNB Attributes"},
    ],
    31: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Terminated",
         "alternateClasses": ["Population"]},
    ],
    32: [
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Contractors",
         "alternateClasses": ["Population"]},
        {"type": "identity.exists", "name": "raj.external"},
    ],
    33: [
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-On-Leave",
         "alternateClasses": ["Population"]},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
    ],
    34: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-BreakGlass"},
    ],
    35: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
    ],
    36: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "identity.exists", "name": "rachel.evans"},
    ],
    37: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-BreakGlass"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
    ],
    38: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "http.ok", "path": "/login.jsf"},
    ],
    39: [
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Finance-Cloud"},
    ],
    40: [
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
    ],
    41: [
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Finance-Cloud"},
    ],
    42: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
        {"type": "identity.exists", "name": "jordan.reed"},
    ],
    43: [
        {"type": "object.exists", "objectClass": "CertificationDefinition", "name": "MNB-Q-Lab-Manager-Cert",
         "alternateClasses": ["TaskDefinition"]},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
    ],
    44: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
    ],
    45: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Finance",
         "alternateClasses": ["Population"]},
    ],
    46: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "host.file.exists", "path": "lab-data/reference/hr-column-map.md"},
    ],
    47: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"},
    ],
    48: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "identity.countMin", "min": 50},
    ],
    49: [
        {"type": "http.ok", "path": "/login.jsf"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {
            "type": "object.exists",
            "objectClass": "EmailTemplate",
            "name": "MNB-Email-AccessRequest",
            "softFail": True,
            "hint": "Name may vary — create the email template from Lesson 49; soft if renamed.",
        },
    ],
    50: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "identity.countMin", "min": 50},
    ],
    # Part II connectors — application objects (lab CSV or live)
    51: [{"type": "host.file.exists", "path": "lab-data/connectors/connector-selection-matrix.csv"},
         {"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"}],
    52: [{"type": "host.file.exists", "path": "lab-data/connectors/connector-selection-matrix.csv"},
         {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"}],
    53: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"},
         {"type": "http.ok", "path": "/login.jsf"}],
    54: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
         {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Aggregate MNB-HR"}],
    55: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
         {"type": "http.ok", "path": "/login.jsf"}],
    56: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"},
         {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Aggregate MNB-ActiveDirectory"}],
    57: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"}],
    58: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-OpenLDAP"}],
    59: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-EntraID"},
         {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Aggregate MNB-EntraID"}],
    60: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-LDIF-DirectoryDump"}],
    61: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"},
         {"type": "http.ok", "path": "/login.jsf"}],
    62: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
         {"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"}],
    63: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-CoreBanking-JDBC"}],
    64: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-CoreBanking-JDBC"}],
    65: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-MSSQL-Reporting"}],
    66: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Oracle-GL"}],
    67: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-SQLLoader-Bulk"}],
    68: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Wire-Portal-WS"}],
    69: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-SCIM-SaaS"}],
    70: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-SCIM-SaaS"}],
    71: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Salesforce"}],
    72: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-ServiceNow"}],
    73: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Okta"}],
    74: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Google-Workspace"}],
    75: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-M365"},
         {"type": "object.exists", "objectClass": "Application", "name": "MNB-SharePoint-Online"}],
    76: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-IAM"}],
    77: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Workday-HCM"}],
    78: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-SAP-HR"}],
    79: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-SAP-Direct"}],
    80: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-PeopleSoft-HCM"}],
    81: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Oracle-EBS"}],
    82: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-RACF-Core"}],
    83: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Linux-Hosts"}],
    84: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Windows-Local"}],
    85: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Logical-Payments-Rail"}],
    86: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-PAM-CyberArk"}],
    87: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-Duo"}],
    88: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
         {"type": "http.ok", "path": "/login.jsf"}],
    89: [{"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"},
         {"type": "http.ok", "path": "/login.jsf"}],
    90: [{"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"}],
    91: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"},
         {"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"}],
    92: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
         {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Refresh MNB Attributes"}],
    93: [
        {
            "type": "object.exists",
            "objectClass": "Workflow",
            "name": "MNB-WF-LCM-AccessRequest",
            "softFail": True,
            "hint": "Custom LCM workflow name may differ; soft if you customized an OOTB copy under another MNB-WF-* name.",
        },
        {"type": "http.ok", "path": "/login.jsf"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
    ],
    94: [{"type": "object.exists", "objectClass": "Form", "name": "MNB-Form-AccessRequest-Extras"}],
    95: [{"type": "object.exists", "objectClass": "QuickLink", "name": "MNB-QL-Request-Payments"},
         {"type": "object.exists", "objectClass": "QuickLink", "name": "MNB-QL-BreakGlass-Info"}],
    96: [{"type": "object.exists", "objectClass": "Identity", "name": "MNB-WG-IAM-Ops"},
         {"type": "http.ok", "path": "/login.jsf"}],
    97: [{"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"},
         {"type": "http.ok", "path": "/login.jsf"}],
    98: [{"type": "object.exists", "objectClass": "QuickLink", "name": "MNB-QL-Toolkit-Ping"},
         {"type": "object.exists", "objectClass": "Identity", "name": "MNB-WG-IAM-Ops"}],
    99: [{"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"},
         {"type": "http.ok", "path": "/login.jsf"}],
    100: [{"type": "object.exists", "objectClass": "Identity", "name": "MNB-WG-IAM-Ops"},
          {"type": "http.ok", "path": "/login.jsf"}],
    101: [{"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"},
          {"type": "host.file.exists", "path": "config/Rule/MNB-Rule-HelloWorld.xml"}],
    102: [{"type": "object.exists", "objectClass": "Identity", "name": "MNB-WG-IAM-Ops"},
          {"type": "http.ok", "path": "/login.jsf"}],
    103: [{"type": "http.ok", "path": "/login.jsf"},
          {"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"}],
    104: [{"type": "http.ok", "path": "/login.jsf"},
          {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"}],
    105: [{"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
          {"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"}],
    106: [{"type": "object.exists", "objectClass": "Identity", "name": "MNB-WG-IAM-Ops"},
          {"type": "http.ok", "path": "/login.jsf"}],
    107: [{"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
          {"type": "object.exists", "objectClass": "Identity", "name": "MNB-WG-IAM-Ops"}],
    108: [{"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"},
          {"type": "host.file.exists", "path": "config/PACKS.md"}],
    109: [{"type": "object.exists", "objectClass": "Identity", "name": "MNB-WG-IAM-Ops"},
          {"type": "http.ok", "path": "/login.jsf"}],
    110: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-CoreBanking"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"},
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "identity.countMin", "min": 50},
    ],
}


def lesson_title(text: str, stem: str) -> str:
    m = re.search(r"^#\s+Lesson\s+\d+\s+[—\-]\s+(.+)$", text, re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        return re.sub(r"^Lesson\s+\d+\s+[—\-]\s*", "", m.group(1)).strip()
    return stem


def default_message(check: dict) -> str:
    t = check["type"]
    if t == "http.ok":
        return "IIQ login page reachable"
    if t == "host.file.exists":
        return f"Repo/lab file present: {check['path']}"
    if t == "object.exists":
        return f"{check['objectClass']} '{check['name']}' exists"
    if t == "identity.exists":
        return f"Identity '{check['name']}' exists"
    if t == "identity.countMin":
        return f"At least {check['min']} identities"
    if t == "identity.attr":
        return f"Identity '{check['name']}' has attribute {check['attr']}"
    return t


def enrich(checks: list[dict]) -> list[dict]:
    out = []
    seen = set()
    # Always lead with UI reachable unless already present
    has_http = any(c.get("type") == "http.ok" for c in checks)
    if not has_http:
        checks = [{"type": "http.ok", "path": "/login.jsf"}] + list(checks)
    for i, c in enumerate(checks):
        key = (c.get("type"), c.get("name"), c.get("path"), c.get("objectClass"), c.get("attr"))
        if key in seen:
            continue
        seen.add(key)
        item = dict(c)
        item.setdefault("id", f"{item['type'].replace('.', '-')}-{i+1}")
        item.setdefault("message", default_message(item))
        out.append(item)
    return out


def build_spec(path: Path) -> dict | None:
    stem = path.stem
    num_s = stem.split("-", 1)[0]
    try:
        num = int(num_s)
    except ValueError:
        return None
    text = path.read_text(encoding="utf-8")
    title = lesson_title(text, stem)
    raw = CURATED.get(num, [
        {"type": "http.ok", "path": "/login.jsf"},
        {"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
    ])
    checks = enrich(raw)
    lesson_id = f"{num:02d}" if num < 100 else str(num)
    return {
        "$schema": "mnb-lesson-spec/v1",
        "lesson": lesson_id,
        "stem": stem,
        "title": title,
        "description": f"Auto-generated verify checks for Lesson {lesson_id}. Live IIQ only — no JSON paste.",
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true", help="Replace existing specs (keeps 01–10 unless --all)")
    ap.add_argument("--all", action="store_true", help="Also regenerate 01–10 (dangerous)")
    ap.add_argument("--min", type=int, default=11)
    ap.add_argument("--max", type=int, default=110)
    args = ap.parse_args()

    SPECS.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    for path in sorted(LESSONS.glob("[0-9]*.md")):
        num = int(path.stem.split("-", 1)[0])
        if num < args.min or num > args.max:
            continue
        if num <= 10 and not args.all:
            continue
        spec = build_spec(path)
        if not spec:
            continue
        out = SPECS / f"{spec['stem']}.json"
        if out.exists() and not args.overwrite:
            skipped += 1
            continue
        out.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        written += 1
        print(f"wrote {out.name} ({len(spec['checks'])} checks)")

    print(f"done: written={written} skipped={skipped} specs_dir={SPECS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
