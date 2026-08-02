#!/usr/bin/env python3
"""Generate lesson-specs for Meridian academy lessons missing JSON specs.

Derives object.exists / task / identity checks from acceptance criteria and a
curated map. Lessons that only produce binder/design artifacts use
``verifyMode: paperwork`` (live IIQ checks disabled). Lab-mutation lessons get
real object / identity checks matching what the learner builds.

Identity checks may keep persona logins (``helen.ross``); ``verify_lesson.py``
adaptively resolves HR ``userId`` / displayName / email aliases at runtime, so
generated specs do not need a full ``alternateNames`` list.

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

# Lessons that are binder/design only — no durable IIQ lab mutation required.
# Letter stems (16b, 29b, …) are handled in LETTERED_PAPERWORK below.
PAPERWORK: set[int] = {
    22,  # attribute sync hygiene — SoT table + disagreement notes
    23,  # role model catalog sketch (implement in 24–28)
    27,  # detection vs assignment — inspect + write policy
    38,  # IdentityRequest evidence pack
    46,  # cert remediation evidence binder
    49,  # email template copy / recipient matrix
    51,  # connector landscape worksheet
    52,  # connector selection matrix worksheets
    53,  # IQService architecture worksheets
    55,  # provisioning feature matrix worksheets
}

LETTERED_PAPERWORK: set[str] = {
    "16b",  # reading Task Results
    "29b",  # optional LCM design (paper or disabled draft)
    "50b",  # choose-your-stack bridge card
}

PAPERWORK_NOTES: dict[str, str] = {
    "22": "Source-of-truth table and hygiene notes — no new IIQ objects required.",
    "23": "Role catalog sketch only — bundles are built in Lessons 24–28.",
    "27": "Assigned vs detected analysis and cert policy notes — no new roles to create.",
    "38": "IdentityRequest evidence pack from prior requests — no new lab objects.",
    "46": "Certification evidence binder assembly — no new campaign objects required.",
    "49": "Email template review and Meridian copy drafts — binder evidence.",
    "51": "Connector registry literacy + worksheets — no new Application required.",
    "52": "Connector selection matrix and decision records — binder evidence.",
    "53": "IQService placement/worksheets — no live IQService install required.",
    "55": "Provisioning feature matrix worksheets — binder evidence.",
    "16b": "Task Result reading literacy — no lab mutation.",
    "29b": "Optional LCM event design (paper or disabled draft) — not required for Core Path.",
    "50b": "Stack choice card after Capstone 50 — binder bridge, not an IIQ build.",
}

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
        {"type": "identity.exists", "name": "jordan.reed", "softFail": True,
         "hint": "Jordan should exist from HR; correlate IT Access after Lesson 17 config."},
    ],
    18: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
        {"type": "identity.exists", "name": "raj.external", "softFail": True,
         "hint": "Raj is the employeeId edge-case persona for Lesson 18."},
        {"type": "identity.exists", "name": "jordan.reed"},
    ],
    19: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
        {"type": "host.file.exists", "path": "lab-data/apps/MNB-AWS-Cloud.csv"},
    ],
    20: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "identity.exists", "name": "samir.hassan"},
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Terminated-With-Access",
         "alternateClasses": ["Population", "GroupFactory"],
         "softFail": True,
         "hint": "Create population/search MNB-Terminated-With-Access (or MNB-Terminated) from Lesson 20."},
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Terminated",
         "alternateClasses": ["Population"],
         "softFail": True,
         "hint": "Optional broader terminated population from Lesson 07/20."},
    ],
    21: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "identity.exists", "name": "priya.wire"},
        {"type": "identity.exists", "name": "rachel.evans"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Refresh MNB Attributes",
         "softFail": True,
         "hint": "Manager reassignment uses Aggregate MNB-HR + identity refresh (Refresh MNB Attributes / Identities)."},
    ],
    # 22 paperwork
    # 23 paperwork
    24: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-IT-ELDAP"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "identity.exists", "name": "amelia.brooks"},
    ],
    25: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-IT-Developer"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-Developer"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-IT-CRM"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-RelationshipManager"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-IT-WireInit"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-WireInitiator"},
        {"type": "identity.exists", "name": "priya.wire"},
        {"type": "identity.exists", "name": "marcus.approve"},
    ],
    26: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-IT-ELDAP"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-IT-Developer"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-IT-WireInit"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-Developer"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
    ],
    # 27 paperwork
    28: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-CloudAdmin"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-BreakGlass"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-IT-CloudAdmin",
         "softFail": True,
         "hint": "Preferred two-tier model: IT pack MNB-IT-CloudAdmin required by MNB-Role-CloudAdmin."},
    ],
    29: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {
            "type": "identity.exists",
            "name": "nina.joiner",
            "softFail": True,
            "hint": "Run ./tools/lab/scripts/scenarios/apply-joiner.sh then Aggregate MNB-HR + Refresh.",
        },
        {"type": "host.file.exists", "path": "lab-data/scenarios/joiner/hr-delta-new-hire.csv"},
    ],
    30: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Refresh MNB Attributes"},
        {"type": "host.file.exists", "path": "lab-data/scenarios/mover/hr-delta-priya-to-commercial.csv"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-WireInitiator",
         "softFail": True,
         "hint": "Mover residual review assumes Lesson 25 WireInitiator role exists."},
    ],
    31: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "identity.exists", "name": "samir.hassan"},
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Terminated",
         "alternateClasses": ["Population"],
         "softFail": True,
         "hint": "Create or reuse MNB-Terminated population for leaver residual hunting."},
    ],
    32: [
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Contractors",
         "alternateClasses": ["Population"]},
        {"type": "identity.exists", "name": "raj.external"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee",
         "softFail": True},
    ],
    33: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "identity.exists", "name": "sofia.torres"},
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-On-Leave",
         "alternateClasses": ["Population"]},
        {"type": "host.file.exists", "path": "lab-data/scenarios/on-leave/hr-delta-sofia-loa.csv"},
    ],
    34: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "identity.exists", "name": "priya.wire"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-BreakGlass",
         "softFail": True,
         "hint": "Break-glass role from Lesson 28; drill still valid if you document disable path without it."},
    ],
    35: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-CloudAdmin"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-RelationshipManager",
         "softFail": True},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
    ],
    36: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "identity.exists", "name": "rachel.evans"},
        {"type": "identity.exists", "name": "christopher.hayes", "softFail": True,
         "hint": "Technology / cloud owner persona for privileged second approval."},
    ],
    37: [
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Role-BreakGlass"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
    ],
    # 38 paperwork
    39: [
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Finance-Cloud"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
    ],
    40: [
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "identity.exists", "name": "priya.wire"},
        {"type": "identity.exists", "name": "marcus.approve"},
    ],
    41: [
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Finance-Cloud"},
    ],
    42: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
        {"type": "identity.exists", "name": "jordan.reed"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal",
         "softFail": True},
    ],
    43: [
        {"type": "object.exists", "objectClass": "CertificationDefinition", "name": "MNB-Q-Lab-Manager-Cert",
         "alternateClasses": ["TaskDefinition"]},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "identity.exists", "name": "rachel.evans", "softFail": True},
    ],
    44: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "object.exists", "objectClass": "CertificationDefinition", "name": "MNB-Q-Lab-Owner-Cert-Wire",
         "alternateClasses": ["TaskDefinition"],
         "softFail": True,
         "hint": "Create app-owner cert MNB-Q-Lab-Owner-Cert-Wire (or AWS variant) from Lesson 44."},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud",
         "softFail": True},
    ],
    45: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-AWS-Cloud"},
        {"type": "object.exists", "objectClass": "CertificationDefinition", "name": "MNB-Q-Lab-Manager-Cert",
         "alternateClasses": ["TaskDefinition"],
         "softFail": True,
         "hint": "Micro-cert may reuse or fork the manager cert definition from Lesson 43."},
        {"type": "object.exists", "objectClass": "GroupDefinition", "name": "MNB-Finance",
         "alternateClasses": ["Population"],
         "softFail": True},
    ],
    # 46 paperwork
    47: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-ActiveDirectory"},
    ],
    48: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl",
         "softFail": True},
        {"type": "identity.countMin", "min": 50},
    ],
    # 49 paperwork
    50: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-WirePortal"},
        {"type": "object.exists", "objectClass": "Policy", "name": "MNB-SOD-Wire-DualControl"},
        {"type": "object.exists", "objectClass": "Bundle", "name": "MNB-Birthright-Employee"},
        {"type": "object.exists", "objectClass": "CertificationDefinition", "name": "MNB-Q-Lab-Manager-Cert",
         "alternateClasses": ["TaskDefinition"],
         "softFail": True},
        {"type": "identity.countMin", "min": 50},
    ],
    # 51–53, 55 paperwork — connector worksheets
    54: [
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
        {"type": "object.exists", "objectClass": "TaskDefinition", "name": "Aggregate MNB-HR"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-IT-Access",
         "softFail": True},
    ],
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


def _lesson_num_token(stem: str) -> tuple[int | None, str]:
    """Return (int_num or None, lesson_id token like '17' or '16b')."""
    m = re.match(r"^(\d{2,3})([a-z])?-", stem)
    if not m:
        return None, stem.split("-", 1)[0]
    n = int(m.group(1))
    letter = m.group(2) or ""
    token = f"{n:02d}{letter}" if n < 100 else f"{n}{letter}"
    return n, token


def is_paperwork(stem: str, num: int | None) -> bool:
    token = stem.split("-", 1)[0]
    if token in LETTERED_PAPERWORK:
        return True
    return num is not None and num in PAPERWORK


def build_spec(path: Path) -> dict | None:
    stem = path.stem
    num, lesson_id = _lesson_num_token(stem)
    if num is None and not re.match(r"^\d", stem):
        return None
    text = path.read_text(encoding="utf-8")
    title = lesson_title(text, stem)
    if is_paperwork(stem, num):
        note = PAPERWORK_NOTES.get(lesson_id) or PAPERWORK_NOTES.get(str(num) if num else "") or (
            "Paperwork / design lesson — no IIQ lab mutation required."
        )
        return {
            "$schema": "mnb-lesson-spec/v1",
            "lesson": lesson_id,
            "stem": stem,
            "title": title,
            "verifyMode": "paperwork",
            "disabled": True,
            "paperworkNote": note,
            "description": (
                f"Paperwork / design only for Lesson {lesson_id}. "
                "Live IIQ Verify is disabled — binder acceptance criteria only."
            ),
            "checks": [],
        }
    if num is None:
        return None
    raw = CURATED.get(num, [
        {"type": "http.ok", "path": "/login.jsf"},
        {"type": "object.exists", "objectClass": "Rule", "name": "MNB-Rule-Hello-World"},
        {"type": "object.exists", "objectClass": "Application", "name": "MNB-HR"},
    ])
    checks = enrich(raw)
    return {
        "$schema": "mnb-lesson-spec/v1",
        "lesson": lesson_id if num >= 100 else f"{num:02d}",
        "stem": stem,
        "title": title,
        "verifyMode": "lab",
        "description": f"Live IIQ verify checks for Lesson {lesson_id}. Lab mutation required — no JSON paste.",
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true", help="Replace existing specs (keeps 01–10 unless --all)")
    ap.add_argument("--all", action="store_true", help="Also regenerate 01–10 (dangerous)")
    ap.add_argument("--min", type=int, default=11)
    ap.add_argument("--max", type=int, default=110)
    ap.add_argument("--lettered", action="store_true", help="Also regenerate NNb lettered Core Path inserts")
    args = ap.parse_args()

    SPECS.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    paths = sorted(LESSONS.glob("[0-9]*.md"))
    for path in paths:
        num, token = _lesson_num_token(path.stem)
        if num is None:
            continue
        lettered = bool(re.match(r"^\d{2,3}[a-z]-", path.stem))
        if lettered and not args.lettered and token not in LETTERED_PAPERWORK:
            continue
        # Lettered paperwork stems always refresh with --overwrite even if outside --min/--max.
        in_range = args.min <= num <= args.max or token in LETTERED_PAPERWORK
        if not in_range:
            continue
        if num <= 10 and not args.all and not lettered:
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
        mode = spec.get("verifyMode", "lab")
        nchecks = len(spec.get("checks") or [])
        print(f"wrote {out.name} (mode={mode}, {nchecks} checks)")

    print(f"done: written={written} skipped={skipped} specs_dir={SPECS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
