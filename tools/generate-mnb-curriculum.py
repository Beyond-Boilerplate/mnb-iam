#!/usr/bin/env python3
"""Generate Meridian National Bank lab-data + 50 IdentityIQ lessons."""

from __future__ import annotations

import csv
import json
import random
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "lab-data"
LESSONS = ROOT / "docs" / "lessons"
random.seed(85)  # stable lab fixtures


# ---------------------------------------------------------------------------
# Org model
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    ("RET", "Retail Banking", "Branch & consumer deposits"),
    ("CML", "Commercial Lending", "Business credit & RM desks"),
    ("TRS", "Treasury & Payments", "Wire, ACH, liquidity"),
    ("FIN", "Finance & Accounting", "GL, SOX, financial close"),
    ("RSK", "Risk & Compliance", "AML, BSA, model risk"),
    ("OPS", "Bank Operations", "Back-office processing"),
    ("DIG", "Digital Banking", "Online/mobile channels"),
    ("ITP", "Technology & Platforms", "Apps, cloud, directory"),
    ("HRP", "People & Culture", "HRIS & workforce"),
    ("SEC", "Information Security", "Cyber, IAM, SOC"),
]

JOBS = [
    ("TEL01", "Teller", "RET", "Branch frontline"),
    ("CSR01", "Customer Service Rep", "RET", "Contact center"),
    ("RM01", "Relationship Manager", "CML", "Commercial portfolio"),
    ("LO01", "Loan Officer", "CML", "Credit underwriting"),
    ("WIR01", "Wire Specialist", "TRS", "Wire initiation"),
    ("WIR02", "Wire Approver", "TRS", "Wire dual control"),
    ("ACH01", "ACH Operator", "TRS", "ACH processing"),
    ("GL01", "Staff Accountant", "FIN", "General ledger"),
    ("SOX01", "SOX Controls Analyst", "FIN", "Financial controls"),
    ("AML01", "AML Investigator", "RSK", "SAR / KYC casework"),
    ("CMP01", "Compliance Officer", "RSK", "Policy & exams"),
    ("OPS01", "Operations Analyst", "OPS", "Item processing"),
    ("DIG01", "Digital Product Analyst", "DIG", "Channel change mgmt"),
    ("SRE01", "Site Reliability Engineer", "ITP", "Platform reliability"),
    ("DEV01", "Application Developer", "ITP", "Internal apps"),
    ("CLD01", "Cloud Platform Engineer", "ITP", "AWS landing zone"),
    ("AD01", "Directory Administrator", "ITP", "Active Directory"),
    ("DBA01", "Database Administrator", "ITP", "Core ODS / DB"),
    ("IAM01", "IAM Engineer", "SEC", "Identity governance"),
    ("SOC01", "SOC Analyst", "SEC", "Security operations"),
    ("HR01", "HR Business Partner", "HRP", "Workforce support"),
    ("MGR01", "People Manager", "RET", "Line management"),
    ("CTO01", "Technology Director", "ITP", "IT leadership"),
    ("CFO01", "Finance Director", "FIN", "Finance leadership"),
    ("CRO01", "Chief Risk Officer", "RSK", "Risk leadership"),
]

ENTITLEMENTS = [
    ("ELDAP", "Enterprise Directory", "Login / AD group backbone", "medium"),
    ("ODS", "Operational Data Store", "Analytics & reporting DB", "medium"),
    ("IBSI", "Internet Banking Support", "Digital banking ops console", "high"),
    ("ECOM", "E-Commerce Channel Ops", "Digital change promotion", "high"),
    ("CRM", "Salesforce CRM", "Relationship management CRM", "medium"),
    ("CORE", "Core Banking (AS400)", "Midrange core operations", "critical"),
    ("SAP_FI", "SAP Finance", "ERP finance modules", "critical"),
    ("AWS_ADMIN", "AWS Admin", "Cloud account administration", "critical"),
    ("DWRP", "Dev Workstation / Repo", "Source control & build", "medium"),
    ("WIRE_INIT", "Wire Portal — Initiate", "Create wire instructions", "critical"),
    ("WIRE_APPR", "Wire Portal — Approve", "Approve wire instructions", "critical"),
    ("ACH_OPS", "ACH Operations", "ACH file create/release", "critical"),
    ("AML_CASE", "AML Case System", "Investigations workspace", "high"),
    ("GL_POST", "GL Posting", "Journal entry posting", "high"),
    ("SOX_VIEW", "SOX Evidence Portal", "Control evidence viewer", "medium"),
    ("PRIV_BREAK", "Break-Glass Admin", "Emergency privileged access", "critical"),
]

SOD_PAIRS = [
    ("WIRE_INIT", "WIRE_APPR", "Payment dual control — initiate vs approve"),
    ("SAP_FI", "AWS_ADMIN", "Finance system of record + cloud bypass"),
    ("IBSI", "ECOM", "Digital banking support + channel promotion"),
    ("GL_POST", "SOX_VIEW", "Post journals and attest own controls"),
    ("CORE", "AWS_ADMIN", "Core ops + infrastructure escape hatch"),
    ("ACH_OPS", "WIRE_INIT", "Cross-rail payment initiation concentration"),
]


FIRST = [
    "Avery", "Jordan", "Priya", "Marcus", "Elena", "Noah", "Sofia", "Liam",
    "Maya", "Ethan", "Aisha", "Owen", "Chloe", "Diego", "Hannah", "Kai",
    "Amelia", "Rohan", "Grace", "Theo", "Nina", "Samir", "Olivia", "Leo",
    "Fatima", "Isaac", "Zoe", "Arjun", "Claire", "Mateo", "Isla", "Dev",
    "Sarah", "James", "Anita", "Raj", "Meera", "Benjamin", "Laura", "Vikram",
    "Helen", "Christopher", "Deepa", "Anthony", "Rachel", "Sanjay", "Emily",
    "Daniel", "Leela", "Michael",
]
LAST = [
    "Chen", "Patel", "Nguyen", "Garcia", "Brooks", "Okoro", "Singh", "Walsh",
    "Kim", "Torres", "Andersson", "Murphy", "Hassan", "Coleman", "Diaz",
    "Shah", "Reed", "Ibrahim", "Foster", "Khatri", "Bailey", "Joshi", "Cruz",
    "Powell", "Mehta", "Sullivan", "Ali", "Bennett", "Rao", "Hughes",
    "Shrestha", "Park", "Morris", "Gupta", "Ross", "Chaudhary", "Evans",
    "Fernandez", "Kapoor", "Hayes", "Thapa", "Price", "Nair", "Griffin",
    "Adhikari", "Watson", "Desai", "Lambert", "Basnet", "Howard",
]

LOCATIONS = [
    ("US-NY", "New York", "USA", "Americas HQ"),
    ("US-CLT", "Charlotte", "USA", "Retail ops hub"),
    ("US-CHI", "Chicago", "USA", "Commercial lending"),
    ("NP-KTM", "Kathmandu", "NPL", "Shared services / digital"),
    ("IN-BLR", "Bengaluru", "IND", "Technology delivery"),
    ("GB-LON", "London", "GBR", "Correspondent banking"),
]


@dataclass
class Person:
    employee_id: str
    user_name: str
    first: str
    last: str
    email: str
    manager_id: str
    status: str  # 1 active, 0 terminated
    dept: str
    job: str
    title: str
    location: str
    country: str
    worker_type: str  # Employee, Contractor
    on_leave: str
    cost_center: str
    hire_date: str
    term_date: str
    entitlements: list[str] = field(default_factory=list)


def slug(first: str, last: str, n: int) -> str:
    base = f"{first}.{last}".lower().replace(" ", "")
    return f"{base}{n}" if n else base


def build_workforce(n: int = 72) -> list[Person]:
    people: list[Person] = []
    # Leadership first (stable IDs for lessons)
    leaders = [
        ("MNB00001", "helen.ross", "Helen", "Ross", "SEC", "IAM01", "Head of Identity & Access"),
        ("MNB00002", "christopher.hayes", "Christopher", "Hayes", "ITP", "CTO01", "Director of Technology"),
        ("MNB00003", "deepa.nair", "Deepa", "Nair", "FIN", "CFO01", "Director of Finance"),
        ("MNB00004", "anthony.powell", "Anthony", "Powell", "RSK", "CRO01", "Chief Risk Officer"),
        ("MNB00005", "rachel.evans", "Rachel", "Evans", "TRS", "WIR02", "Payments Operations Manager"),
        ("MNB00006", "sanjay.kapoor", "Sanjay", "Kapoor", "CML", "RM01", "Commercial Banking Manager"),
        ("MNB00007", "emily.bennett", "Emily", "Bennett", "RET", "MGR01", "Retail Branch Manager"),
        ("MNB00008", "daniel.griffin", "Daniel", "Griffin", "OPS", "OPS01", "Operations Manager"),
    ]
    for i, (eid, uname, first, last, dept, job, title) in enumerate(leaders):
        loc = LOCATIONS[i % len(LOCATIONS)]
        people.append(
            Person(
                eid, uname, first, last, f"{uname}@meridiannb.com", "",
                "1", dept, job, title, loc[0], loc[2], "Employee", "false",
                f"CC-{dept}-100", "2018-03-12", "",
            )
        )

    manager_pool = [p.employee_id for p in people]
    used_names: set[str] = {p.user_name for p in people}
    idx = 9
    while len(people) < n:
        first = random.choice(FIRST)
        last = random.choice(LAST)
        uname = slug(first, last, 0)
        suffix = 1
        while uname in used_names:
            uname = slug(first, last, suffix)
            suffix += 1
        used_names.add(uname)
        job_code, title, dept, _ = random.choice(JOBS)
        # Bias managers toward leaders + early people
        manager = random.choice(manager_pool[: max(4, len(manager_pool) // 2)])
        loc = random.choice(LOCATIONS)
        worker = "Contractor" if random.random() < 0.12 else "Employee"
        status = "0" if random.random() < 0.08 else "1"
        on_leave = "true" if status == "1" and random.random() < 0.06 else "false"
        hire = f"20{random.randint(15, 24)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        term = f"2026-0{random.randint(1,6)}-{random.randint(1,28):02d}" if status == "0" else ""
        eid = f"MNB{idx:05d}"
        people.append(
            Person(
                eid, uname, first, last, f"{uname}@meridiannb.com", manager,
                status, dept, job_code, title, loc[0], loc[2], worker, on_leave,
                f"CC-{dept}-{100 + (idx % 40)}", hire, term,
            )
        )
        if status == "1" and worker == "Employee" and random.random() < 0.25:
            manager_pool.append(eid)
        idx += 1

    # Scripted personas for SOD / JML demos
    scripted = [
        Person("MNB00090", "priya.wire", "Priya", "Mehta", "priya.wire@meridiannb.com",
               "MNB00005", "1", "TRS", "WIR01", "Wire Specialist", "US-NY", "USA",
               "Employee", "false", "CC-TRS-210", "2022-06-01", "",
               ["ELDAP", "WIRE_INIT", "ACH_OPS"]),
        Person("MNB00091", "marcus.approve", "Marcus", "Coleman", "marcus.approve@meridiannb.com",
               "MNB00005", "1", "TRS", "WIR02", "Wire Approver", "US-NY", "USA",
               "Employee", "false", "CC-TRS-210", "2021-02-14", "",
               ["ELDAP", "WIRE_APPR"]),
        Person("MNB00092", "jordan.reed", "Jordan", "Reed", "jordan.reed@meridiannb.com",
               "MNB00003", "1", "FIN", "GL01", "Staff Accountant", "US-CLT", "USA",
               "Employee", "false", "CC-FIN-300", "2020-09-09", "",
               ["ELDAP", "SAP_FI", "AWS_ADMIN", "GL_POST"]),  # intentional SOD
        Person("MNB00093", "raj.external", "Raj", "External", "raj.contractor@vendor-mail.invalid",
               "MNB00002", "1", "ITP", "CLD01", "Cloud Platform Engineer", "IN-BLR", "IND",
               "Contractor", "false", "CC-ITP-400", "2023-01-10", "",
               ["AWS_ADMIN"]),  # email won't match corp domain — orphan demos
        Person("MNB00094", "samir.hassan", "Samir", "Hassan", "samir.hassan@meridiannb.com",
               "MNB00002", "0", "ITP", "DEV01", "Application Developer", "NP-KTM", "NPL",
               "Employee", "false", "CC-ITP-410", "2019-11-01", "2026-05-30",
               ["ELDAP", "DWRP", "ODS", "SAP_FI"]),  # terminated with residual access
        Person("MNB00095", "sofia.torres", "Sofia", "Torres", "sofia.torres@meridiannb.com",
               "MNB00006", "1", "CML", "RM01", "Relationship Manager", "US-CHI", "USA",
               "Employee", "true", "CC-CML-220", "2018-08-20", "",
               ["ELDAP", "CRM", "ODS"]),
        Person("MNB00096", "kai.nguyen", "Kai", "Nguyen", "kai.nguyen@meridiannb.com",
               "MNB00002", "1", "DIG", "DIG01", "Digital Product Analyst", "US-NY", "USA",
               "Employee", "false", "CC-DIG-250", "2024-01-15", "",
               ["ELDAP", "IBSI", "ECOM"]),  # digital SOD
        Person("MNB00097", "amelia.brooks", "Amelia", "Brooks", "amelia.brooks@meridiannb.com",
               "MNB00007", "1", "RET", "TEL01", "Teller", "US-CLT", "USA",
               "Employee", "false", "CC-RET-110", "2026-07-20", "",
               []),  # joiner with no IT yet
    ]
    # Replace collisions / append
    by_id = {p.employee_id: p for p in people}
    for s in scripted:
        by_id[s.employee_id] = s
    return sorted(by_id.values(), key=lambda p: p.employee_id)


def assign_entitlements(people: list[Person]) -> None:
    for p in people:
        if p.entitlements:
            continue
        ents: list[str] = []
        if p.status == "1":
            ents.append("ELDAP")
        # Job-based defaults
        job_map = {
            "DEV01": ["DWRP", "ODS"],
            "SRE01": ["DWRP", "ODS", "AWS_ADMIN"],
            "CLD01": ["AWS_ADMIN", "DWRP"],
            "AD01": ["ELDAP"],
            "DBA01": ["ODS", "CORE"],
            "WIR01": ["WIRE_INIT"],
            "WIR02": ["WIRE_APPR"],
            "ACH01": ["ACH_OPS"],
            "GL01": ["SAP_FI", "GL_POST"],
            "SOX01": ["SOX_VIEW", "SAP_FI"],
            "AML01": ["AML_CASE", "ODS"],
            "DIG01": ["IBSI"],
            "RM01": ["CRM", "ODS"],
            "LO01": ["CRM", "ODS"],
            "OPS01": ["CORE", "ECOM"],
            "IAM01": ["ELDAP", "SOX_VIEW"],
            "SOC01": ["AML_CASE"],
            "TEL01": ["ELDAP"],
            "CSR01": ["ELDAP", "CRM"],
        }
        ents.extend(job_map.get(p.job, []))
        if p.worker_type == "Contractor" and "AWS_ADMIN" in ents and random.random() < 0.4:
            ents.append("PRIV_BREAK")
        # Residual access for some terminated
        if p.status == "0" and random.random() < 0.55:
            ents = list({*ents, "ELDAP", random.choice(["SAP_FI", "AWS_ADMIN", "CORE"])})
        p.entitlements = sorted(set(ents))


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def generate_lab_data() -> list[Person]:
    people = build_workforce(72)
    assign_entitlements(people)

    # Keep legacy filenames for earlier docs + new structured layout
    hr_headers = [
        "employeeId", "userName", "firstName", "lastName", "email", "managerId",
        "status", "departmentCode", "jobCode", "jobTitle", "locationCode", "country",
        "workerType", "onLeave", "costCenter", "hireDate", "terminationDate",
    ]
    hr_rows = [
        [
            p.employee_id, p.user_name, p.first, p.last, p.email, p.manager_id,
            p.status, p.dept, p.job, p.title, p.location, p.country,
            p.worker_type, p.on_leave, p.cost_center, p.hire_date, p.term_date,
        ]
        for p in people
    ]
    write_csv(LAB / "hr" / "MNB-HR-Employees.csv", hr_headers, hr_rows)
    write_csv(LAB / "HRApplications.txt", hr_headers, hr_rows)  # IIQ-friendly name

    # Flat IT access (one entitlement per row — realistic dump)
    it_headers = ["userName", "firstName", "lastName", "email", "jobTitle", "employeeId", "itAccess", "accountStatus"]
    it_rows: list[list[str]] = []
    for p in people:
        for ent in p.entitlements:
            acct_status = "disabled" if p.status == "0" else "active"
            # Deliberate messiness: one orphan-style mismatched email already on MNB00093
            email = p.email
            it_rows.append([p.user_name, p.first, p.last, email, p.title, p.employee_id, ent, acct_status])
    # Duplicate noisy rows (real exports often repeat)
    it_rows.append(it_rows[3][:])
    it_rows.append(it_rows[7][:])
    write_csv(LAB / "apps" / "MNB-IT-Access.csv", it_headers, it_rows)
    write_csv(LAB / "EmployeeData.txt", it_headers, it_rows)

    def app_rows(code: str) -> list[list[str]]:
        return [
            [p.user_name, p.email, p.employee_id, code, "active" if p.status == "1" else "disabled"]
            for p in people if code in p.entitlements
        ]

    app_headers = ["userName", "email", "employeeId", "entitlement", "accountStatus"]
    for code, filename in [
        ("CORE", "MNB-CoreBanking.csv"),
        ("SAP_FI", "MNB-SAP-Finance.csv"),
        ("AWS_ADMIN", "MNB-AWS-Cloud.csv"),
        ("WIRE_INIT", "MNB-WirePortal-Initiators.csv"),
        ("WIRE_APPR", "MNB-WirePortal-Approvers.csv"),
        ("ELDAP", "MNB-ActiveDirectory.csv"),
        ("CRM", "MNB-Salesforce-CRM.csv"),
        ("IBSI", "MNB-InternetBanking.csv"),
        ("ECOM", "MNB-Ecommerce-Ops.csv"),
    ]:
        write_csv(LAB / "apps" / filename, app_headers, app_rows(code))

    # Combined wire portal (both entitlements)
    wire_rows = []
    for p in people:
        for e in ("WIRE_INIT", "WIRE_APPR"):
            if e in p.entitlements:
                wire_rows.append([p.user_name, p.email, p.employee_id, e, "active" if p.status == "1" else "disabled"])
    write_csv(LAB / "apps" / "MNB-WirePortal.csv", app_headers, wire_rows)

    write_csv(
        LAB / "reference" / "departments.csv",
        ["departmentCode", "departmentName", "description"],
        [list(d) for d in DEPARTMENTS],
    )
    write_csv(
        LAB / "reference" / "job-codes.csv",
        ["jobCode", "jobTitle", "departmentCode", "description"],
        [list(j) for j in JOBS],
    )
    write_csv(
        LAB / "reference" / "entitlement-dictionary.csv",
        ["code", "name", "description", "risk"],
        [list(e) for e in ENTITLEMENTS],
    )
    write_csv(
        LAB / "reference" / "sod-matrix.csv",
        ["entitlementA", "entitlementB", "rationale"],
        [list(s) for s in SOD_PAIRS],
    )
    write_csv(
        LAB / "reference" / "locations.csv",
        ["locationCode", "city", "country", "notes"],
        [list(l) for l in LOCATIONS],
    )

    # Scenario deltas
    joiner = [
        "MNB00120", "nina.joiner", "Nina", "Foster", "nina.joiner@meridiannb.com",
        "MNB00007", "1", "RET", "TEL01", "Teller", "US-CLT", "USA",
        "Employee", "false", "CC-RET-110", "2026-07-26", "",
    ]
    write_csv(LAB / "scenarios" / "joiner" / "hr-delta-new-hire.csv", hr_headers, [joiner])

    # mover: Priya to Commercial
    mover = next(p for p in people if p.employee_id == "MNB00090")
    mover_row = [
        mover.employee_id, mover.user_name, mover.first, mover.last, mover.email, "MNB00006",
        "1", "CML", "RM01", "Relationship Manager", mover.location, mover.country,
        "Employee", "false", "CC-CML-220", mover.hire_date, "",
    ]
    write_csv(LAB / "scenarios" / "mover" / "hr-delta-priya-to-commercial.csv", hr_headers, [mover_row])

    leaver = next(p for p in people if p.employee_id == "MNB00092")
    leaver_row = [
        leaver.employee_id, leaver.user_name, leaver.first, leaver.last, leaver.email, leaver.manager_id,
        "0", leaver.dept, leaver.job, leaver.title, leaver.location, leaver.country,
        leaver.worker_type, "false", leaver.cost_center, leaver.hire_date, "2026-07-26",
    ]
    write_csv(LAB / "scenarios" / "leaver" / "hr-delta-terminate-jordan.csv", hr_headers, [leaver_row])

    # Notifications sample
    (LAB / "notifications" / "certification-sample.txt").write_text(
        textwrap.dedent(
            """\
            From: identity-noreply@meridiannb.com
            To: rachel.evans@meridiannb.com
            Subject: Action required — Q3 Manager Access Review (Treasury)

            Rachel,

            Meridian National Bank's quarterly access certification for your
            direct reports is ready. Please complete decisions by the due date.

            Campaign: MNB-Q3-Manager-Cert-Treasury
            Scope: High-risk entitlements on Wire Portal, SAP Finance, AWS Admin
            Due: 10 business days

            Login to IdentityIQ → Work Item Inbox → open the certification.

            — Identity Governance Office
            """
        ),
        encoding="utf-8",
    )
    (LAB / "email.txt").write_text(
        (LAB / "notifications" / "certification-sample.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    (LAB / "README.md").write_text(
        textwrap.dedent(
            """\
            # Meridian National Bank — Lab Data

            Realistic delimited files for the IdentityIQ 50-lesson curriculum.

            ## Quick copy

            ```bash
            mkdir -p ~/iiq-lab-data
            cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/
            cp -R lab-data/apps lab-data/scenarios lab-data/reference ~/iiq-lab-data/
            ```

            ## Files

            | Path | Purpose |
            | --- | --- |
            | `HRApplications.txt` / `hr/MNB-HR-Employees.csv` | Authoritative HR (~70 workers) |
            | `EmployeeData.txt` / `apps/MNB-IT-Access.csv` | Consolidated entitlement dump |
            | `apps/MNB-*.csv` | Per-platform extracts (Core, SAP, AWS, Wire, AD, …) |
            | `reference/*` | Dept, job, entitlement, SoD dictionaries |
            | `scenarios/*` | Joiner / mover / leaver delta rows |
            | `notifications/certification-sample.txt` | Manager cert email tone |

            Corporate email domain: `@meridiannb.com`

            Scripted personas (use in lessons): `MNB00090`–`MNB00097`.
            """
        ),
        encoding="utf-8",
    )

    meta = {
        "company": "Meridian National Bank",
        "domain": "meridiannb.com",
        "headcount": len(people),
        "active": sum(1 for p in people if p.status == "1"),
        "scripted_ids": [f"MNB0009{i}" for i in range(0, 8)],
    }
    (LAB / "reference" / "lab-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return people


# ---------------------------------------------------------------------------
# Curriculum (50 lessons)
# ---------------------------------------------------------------------------

@dataclass
class Lesson:
    num: int
    slug: str
    title: str
    level: str
    track: str
    minutes: str
    why: str
    story: str
    how: str
    goals: list[str]
    tasks: list[tuple[str, list[str]]]
    tips: list[str]
    checkpoint: list[str]
    stretch: list[str]
    data_files: list[str] = field(default_factory=list)


def L(num, slug, title, level, track, minutes, why, story, how, goals, tasks, tips, checkpoint, stretch, data=None):
    return Lesson(num, slug, title, level, track, minutes, why, story, how, goals, tasks, tips, checkpoint, stretch, data or [])


def curriculum() -> list[Lesson]:
    return [
        L(1, "bank-briefing-and-ui", "Bank Briefing & UI Orientation", "Beginner", "Foundations", "45–60",
          "You cannot govern what you cannot find. Orientation prevents random clicking when audit pressure hits.",
          "Day one on Meridian’s Identity Governance team. Leadership bought IdentityIQ to speed onboarding, kill orphan access after exits, and produce exam evidence. Your first job is not connectors—it is learning the control surface.",
          "IdentityIQ separates **configuration** (apps, roles, policies), **operational data** (identities, certifications), **tasks** (jobs), and **work items** (human decisions). You will wear admin, manager, and end-user hats across the curriculum.",
          ["Log in as spadmin", "Locate Identities, Applications, Tasks, Work Items", "Open Debug and recognize XML objects", "Write a one-paragraph MNB value statement"],
          [("Login & password hygiene", [
              "Start Tomcat if needed and open http://localhost:8080/identityiq.",
              "Login: spadmin / admin. Change the password if this lab is shared.",
              "Note the environment name/banner if present—treat lab vs prod cues seriously.",
          ]), ("Tour the identity cube", [
              "Open Identities / Identity Warehouse and search for spadmin.",
              "Click through attributes, accounts, roles, work items, and risk tabs.",
              "Write one sentence: “An identity cube is …”",
          ]), ("Applications & Tasks map", [
              "Open Applications (Setup/Define). Observe stock apps.",
              "Open Tasks. Do not run random jobs—note types (Aggregation, Refresh, Certification).",
          ]), ("Work Item Inbox", [
              "Open your Work Item Inbox. Empty is normal.",
              "Bookmark this screen—Lessons 35–46 fill it with real decisions.",
          ]), ("Debug awareness", [
              "Open Debug / Administrator console.",
              "Browse Application, Identity, TaskDefinition, Bundle, Workflow object types.",
              "Open one object and confirm it is XML under the hood.",
          ]), ("Skim Meridian lab data", [
              "Open ~/iiq-lab-data/HRApplications.txt and EmployeeData.txt.",
              "Find leadership rows MNB00001–MNB00008 and scripted personas MNB00090–MNB00097.",
              "Skim lab-data/reference/entitlement-dictionary.csv and sod-matrix.csv.",
          ])],
          ["Keep a lab notebook of object names with MNB- prefix.", "Prefer search over memorizing every menu path.", "If UI feels empty, confirm LCM init import from LOCAL_SETUP."],
          ["Admin URL and default user?", "What is an identity cube in one sentence?", "Which file is authoritative for who works at Meridian?"],
          ["Export spadmin identity XML from Debug and skim it.", "Read Getting Started PDF first 10 pages."],
          ["HRApplications.txt", "EmployeeData.txt", "reference/entitlement-dictionary.csv"]),

        L(2, "meridian-org-model", "Meridian Org Model & Risk Language", "Beginner", "Foundations", "45–60",
          "IAM designs fail when they ignore org reality. Departments, jobs, and risk tiers drive roles, SoD, and certifications.",
          "Before wiring connectors, Meridian’s CISO asks you to speak the bank’s language: Retail vs Treasury vs Risk, and why WIRE_INIT is not the same risk as CRM.",
          "Authoritative HR carries departmentCode, jobCode, workerType, and location. Entitlements have a risk dictionary. SoD pairs encode dual-control expectations from payments and finance.",
          ["Explain MNB dept map from reference data", "Map five job codes to likely entitlements", "List critical vs medium entitlements", "Identify two intentional SoD violators in lab data"],
          [("Read the org dictionaries", [
              "Open lab-data/reference/departments.csv and job-codes.csv.",
              "Draw a simple org sketch: leaders MNB00001–08 and which dept they own.",
          ]), ("Entitlement risk walkthrough", [
              "Open entitlement-dictionary.csv.",
              "Circle all risk=critical codes. These dominate certifications and SoD.",
          ]), ("Find toxic access in data", [
              "Inspect jordan.reed (MNB00092) and kai.nguyen (MNB00096) in EmployeeData.txt.",
              "Match their entitlements to sod-matrix.csv rationales.",
          ]), ("Contractor vs employee", [
              "Filter HR for workerType=Contractor. Note why contractors need tighter joiner/leaver SLAs.",
          ]), ("Write Meridian risk notes", [
              "In your notebook, define: birthright, requestable, privileged, break-glass—with one MNB example each.",
          ])],
          ["Use codes (TRS, WIRE_INIT) in object names—auditors recognize them.", "Do not invent entitlements outside the dictionary without updating reference files."],
          ["Name two critical entitlements and why.", "Which persona holds WIRE_INIT without WIRE_APPR?", "Why is SAP_FI + AWS_ADMIN toxic?"],
          ["Propose a third SoD pair Meridian should add and justify it."],
          ["reference/departments.csv", "reference/sod-matrix.csv"]),

        L(3, "lab-hygiene-and-naming", "Lab Hygiene, Naming & Evidence Habits", "Beginner", "Foundations", "30–45",
          "Messy labs teach bad prod habits. Naming, absolute paths, and evidence screenshots are how banks survive exams.",
          "Meridian audit wants reproducible builds. Your lab must look like a controlled change: prefixed objects, task results saved, and data paths that survive Tomcat restarts.",
          "Convention: applications/tasks/roles/policies start with MNB-. Delimited files use absolute paths under ~/iiq-lab-data. Keep a dated evidence folder for screenshots of task results.",
          ["Adopt MNB- naming convention", "Copy lab-data into ~/iiq-lab-data", "Create an evidence folder pattern", "Document absolute file paths"],
          [("Copy lab fixtures", [
              "From repo root: mkdir -p ~/iiq-lab-data && cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/ && cp -R lab-data/apps lab-data/scenarios lab-data/reference ~/iiq-lab-data/",
              "Confirm files exist with ls ~/iiq-lab-data.",
          ]), ("Path check", [
              "Write the absolute path to HRApplications.txt in your notebook.",
              "Confirm the OS user running Tomcat can read that path.",
          ]), ("Naming standard", [
              "Record the standard: MNB-HR, Aggregate MNB-HR, Refresh MNB Identities, MNB-SOD-*, MNB-Role-*.",
          ]), ("Evidence folder", [
              "Create ~/iiq-lab-evidence/YYYY-MM-DD/ and drop a text file describing today’s intent.",
          ]), ("Change log habit", [
              "Add a CHANGELOG.md in your notebook: date, object, why.",
          ])],
          ["Relative paths break under Tomcat working directories.", "Never reuse prod names in a shared lab without a prefix."],
          ["Why absolute paths?", "Give three object types that should use MNB- prefix.", "What belongs in evidence folders?"],
          ["Add a simple script that timestamps copies of task result text exports."]),

        L(4, "authoritative-hr-source", "Authoritative HR Source", "Beginner", "Foundations", "60–90",
          "If HR is wrong, every downstream control is wrong. Authoritative aggregation is the root of joiner/mover/leaver truth.",
          "When a teller is hired in Charlotte or a wire specialist joins in New York, HR gets the record first. IdentityIQ must learn people from Meridian HR—not from random IT spreadsheets.",
          "An authoritative Delimited File application creates/updates identities from HR columns: employeeId, managerId, status, departmentCode, jobCode, workerType, onLeave.",
          ["Create MNB-HR Delimited File app", "Map schema from HRApplications.txt", "Enable identity creation", "Run Aggregate MNB-HR successfully", "Verify a known identity cube"],
          [("Inspect HR header", [
              "Confirm columns in HRApplications.txt (employeeId through terminationDate).",
              "Note status=0 leavers and onLeave=true rows.",
          ]), ("Create application MNB-HR", [
              "Applications → Add New → DelimitedFile named MNB-HR.",
              "Point to absolute path ~/iiq-lab-data/HRApplications.txt, delimiter comma, has header.",
              "Owner: spadmin. Save.",
          ]), ("Schema discovery", [
              "Discover/define schema. Set account identity attribute to employeeId.",
              "Map email, firstname/lastname, manager, department, status, workerType, onLeave.",
          ]), ("Authoritative settings", [
              "Enable create identities from this application.",
              "Save. Document the setting in your notebook.",
          ]), ("Aggregate", [
              "Create Account Aggregation task Aggregate MNB-HR and run it.",
              "Open task result—account count should be > 0.",
          ]), ("Verify personas", [
              "Search helen.ross, priya.wire, samir.hassan (terminated).",
              "Confirm HR account on each cube; note how inactive looks today.",
          ])],
          ["Re-aggregate after schema changes.", "Zero accounts usually means path, permissions, or header parse issues."],
          ["What makes an app authoritative?", "Why employeeId over email as account id?", "Where do you look first when aggregation fails?"],
          ["Append scenarios/joiner/hr-delta-new-hire.csv into HR file and re-aggregate."],
          ["HRApplications.txt"]),

        L(5, "hr-schema-and-identity-attrs", "HR Schema & Identity Attribute Design", "Beginner", "Foundations", "60",
          "Attribute design decides what roles and policies can see. Bad mappings create silent control gaps.",
          "Meridian needs manager hierarchy, active/inactive, contractor flags, and department codes on the identity—not buried only on the account.",
          "Map account attributes onto identity attributes used by roles, lifecycle triggers, and certifications. Prefer stable codes (departmentCode) over display strings.",
          ["Promote key HR fields to identity attributes", "Confirm manager linkage", "Document attribute dictionary", "Validate contractor and onLeave flags"],
          [("Attribute inventory", [
              "List which HR columns must live on the Identity vs only on the Link.",
              "Minimum: email, manager, departmentCode, jobCode, status, workerType, onLeave, locationCode.",
          ]), ("Refine MNB-HR schema maps", [
              "Adjust schema so identity attributes populate after refresh.",
              "Normalize names if UI expects firstname vs firstName.",
          ]), ("Manager hierarchy check", [
              "Open priya.wire and confirm manager resolves toward rachel.evans / MNB00005.",
              "Open a nested report line and sketch two levels of management.",
          ]), ("Inactive & leave flags", [
              "Compare samir.hassan (status=0) vs sofia.torres (onLeave=true).",
              "Write how Meridian should treat each differently.",
          ]), ("Publish attribute dictionary", [
              "Create a short table in your notebook: attribute → source → used by (roles/SoD/JML).",
          ])],
          ["Codes beat free-text for role rules.", "Do not overwrite authoritative email from non-HR apps."],
          ["Which flag drives termination vs temporary freeze?", "Why keep departmentCode on the identity?", "Name one attribute certifications will display."],
          ["Add costCenter to identity and show it on the cube."]),

        L(6, "identity-cubes-and-refresh", "Identity Cubes & Refresh", "Beginner", "Foundations", "60",
          "Aggregation loads accounts; refresh recalculates the person. Without refresh, roles, managers, and policies lag reality.",
          "HR accounts exist. Meridian needs continuous recalculation so manager, status, detected roles, and policy state stay true before Monday’s ops meeting.",
          "Identity Refresh re-evaluates correlations, role assignments, manager links, and optionally policies. Schedule it after aggregations in production-like pipelines.",
          ["Inspect a full cube", "Create Refresh MNB Identities", "Run refresh after HR aggregate", "Observe attribute/manager updates", "Note scheduling options"],
          [("Cube deep-dive", [
              "Open christopher.hayes and inventory accounts, attributes, and roles tabs.",
          ]), ("Create refresh task", [
              "Tasks → Identity Refresh named Refresh MNB Identities.",
              "Filter to identities with MNB-HR accounts if available; else refresh all (lab is small).",
          ]), ("Enable useful options", [
              "Enable refresh options you understand (manager correlation, role assignment, policy checking—as available).",
              "Document which checkboxes you enabled.",
          ]), ("Run pipeline", [
              "Run Aggregate MNB-HR then Refresh MNB Identities.",
              "Capture task result screenshots into evidence folder.",
          ]), ("Change-detect drill", [
              "Flip onLeave for one active user in the HR file.",
              "Re-aggregate + refresh; confirm the cube reflects the change.",
          ])],
          ["Refresh is not optional glue—it is the calculation engine.", "Too many refresh options can slow large prod tenants—be intentional."],
          ["Aggregation vs refresh in one sentence each?", "Why run refresh after HR aggregate?", "What is dangerous about refreshing ‘everything’ in prod?"],
          ["Schedule Refresh MNB Identities daily at 02:00 in the UI (laptop lab practice)."]),

        L(7, "populations-and-selectors", "Populations & Identity Selectors", "Beginner", "Foundations", "45–60",
          "Certifications, reports, and refreshes need scoped populations. “All identities” does not scale and scares auditors.",
          "Meridian wants populations: Active Employees, Contractors, Treasury Staff, Terminated with Access. These become reusable scopes.",
          "Populations / identity selectors filter identities by attributes or links. Use them in refresh, certifications, and reporting.",
          ["Create MNB Active Employees population", "Create Contractors population", "Create Treasury population", "Use a population in a refresh or search"],
          [("Active employees", [
              "Create population MNB-Active-Employees where status indicates active / HR status=1.",
          ]), ("Contractors", [
              "Create MNB-Contractors on workerType=Contractor.",
          ]), ("Treasury staff", [
              "Create MNB-Treasury on departmentCode=TRS.",
          ]), ("Terminated with residual risk", [
              "Attempt a population or advanced search for status inactive that still has IT accounts (may be approximate in lab).",
          ]), ("Apply population", [
              "Point Refresh MNB Identities (or a copy) at MNB-Active-Employees and run.",
          ])],
          ["Name populations as reusable controls, not one-off searches.", "Document membership logic for audit."],
          ["Why populations beat ad-hoc filters?", "Which population should certifications start with?", "How do contractors differ in scope?"],
          ["Create MNB-On-Leave population and explain a control that uses it."]),

        L(8, "task-ops-and-scheduling", "Task Operations & Scheduling Discipline", "Beginner", "Foundations", "45",
          "Banks run IAM as a factory. Task order and schedules are operational controls, not conveniences.",
          "Meridian ops wants a nightly order: HR aggregate → app aggregates → refresh → policy scan. You practice the operational muscle now.",
          "Task results, hosts, cron-like schedules, and dependencies matter. Failures must be visible before the business day.",
          ["Inventory MNB tasks", "Define a nightly runbook order", "Schedule one task", "Practice reading a failed vs successful result"],
          [("Task inventory", [
              "List every MNB-* task you have (or will create) in your notebook.",
          ]), ("Runbook order", [
              "Write the order: Aggregate MNB-HR → Aggregate MNB-IT-Access → app-specific aggregates → Refresh MNB Identities.",
              "Note why HR is first.",
          ]), ("Schedule UI", [
              "Open scheduling for Refresh MNB Identities; set a daily time; save.",
              "Disable the schedule again if you do not want laptop overnight runs—practice is the point.",
          ]), ("Result literacy", [
              "Open a prior task result and identify start time, duration, counters, and errors.",
          ]), ("On-call note", [
              "Write a 5-line on-call checklist for ‘aggregation failed’.",
          ])],
          ["Never schedule destructive tasks without a maintenance window habit.", "Capture result IDs in evidence."],
          ["Why HR aggregate before IT aggregate?", "What fields do you read on a task result first?", "Name one risk of overlapping refreshes."],
          ["Create a sequential composite mindset doc even if your IIQ edition uses separate schedules."]),

        L(9, "it-access-inventory-app", "Onboard IT Access Inventory App", "Beginner", "Applications", "60–90",
          "Most banks start with a messy entitlement dump before perfect connectors. You must onboard imperfect truth safely.",
          "IT gives you EmployeeData.txt / MNB-IT-Access.csv: who has ODS, AWS_ADMIN, SAP_FI, WIRE_*. It is denormalized and duplicated—like production exports.",
          "Create non-authoritative application MNB-IT-Access. It must not create identities; it correlates onto HR people and materializes entitlements.",
          ["Create MNB-IT-Access", "Map entitlement attribute itAccess", "Aggregate successfully", "Confirm no identity creation", "Spot-check jordan.reed toxic entitlements"],
          [("Inspect the dump", [
              "Open EmployeeData.txt. Note duplicate usernames and multiple rows per person.",
              "Count distinct itAccess codes.",
          ]), ("Create MNB-IT-Access", [
              "Delimited File app → ~/iiq-lab-data/EmployeeData.txt.",
              "Account id: userName or employeeId; group/entitlement attribute: itAccess.",
          ]), ("Non-authoritative", [
              "Ensure this app does NOT create identities. Only MNB-HR should.",
          ]), ("Aggregate MNB-IT-Access", [
              "Create and run Aggregate MNB-IT-Access.",
          ]), ("Verify entitlements", [
              "Open jordan.reed and kai.nguyen cubes; confirm entitlements present (correlation may be partial until Lesson 17).",
          ])],
          ["Entitlement attributes turn columns into governable access.", "Duplicates in files are normal—document them."],
          ["Why must IT apps be non-authoritative?", "What column becomes the entitlement?", "Name two people useful for SoD demos."],
          ["Import apps/MNB-SAP-Finance.csv as a separate app later—preview the file now."],
          ["EmployeeData.txt"]),

        L(10, "entitlement-dictionary", "Entitlement Dictionary & Managed Attributes", "Beginner", "Applications", "45–60",
          "If entitlements are opaque codes, managers rubber-stamp certifications. Dictionaries make access human-reviewable.",
          "Meridian business owners need readable names: “Wire Portal — Initiate” not WIRE_INIT. Risk tiers drive campaign scope.",
          "Managed attributes / entitlement catalog entries carry display name, description, owner, and requestable flags.",
          ["Import dictionary concepts into notebook", "Enrich at least five entitlements in IIQ", "Mark requestable vs non-requestable", "Tag critical entitlements"],
          [("Load dictionary", [
              "Open reference/entitlement-dictionary.csv and keep it beside the IIQ UI.",
          ]), ("Enrich managed attributes", [
              "For WIRE_INIT, WIRE_APPR, SAP_FI, AWS_ADMIN, ELDAP—set display names and descriptions from the dictionary.",
          ]), ("Requestable flags", [
              "Mark CRM and DWRP requestable; mark AWS_ADMIN and PRIV_BREAK not birthright / tightly controlled.",
          ]), ("Owner assignment", [
              "Assign application/entitlement owners conceptually: rachel.evans for wire, deepa.nair for SAP, christopher.hayes for AWS.",
          ]), ("Evidence", [
              "Screenshot an enriched entitlement for your evidence folder.",
          ])],
          ["Owners who left the bank break certifications—keep owners current.", "Critical tags should match SoD and cert scopes."],
          ["Why display names matter in certs?", "Which entitlements should never be self-requestable?", "Who should own WIRE_APPR?"],
          ["Add PRIV_BREAK with a scary description and non-requestable flag."]),

        L(11, "onboard-core-banking", "Onboard Core Banking Extract", "Intermediate", "Applications", "60",
          "Core banking access is crown-jewel. Onboarding it early forces good correlation and certification habits.",
          "Operations runs on a midrange core (AS400-style). You onboard apps/MNB-CoreBanking.csv as MNB-CoreBanking.",
          "Separate high-risk platforms from the mega-dump when possible. Aggregation, ownership, and certs become clearer.",
          ["Create MNB-CoreBanking app", "Aggregate CORE entitlements", "Set app owner", "Document risk tier critical"],
          [("Inspect extract", ["Open apps/MNB-CoreBanking.csv and list holders."]),
           ("Create app", ["Delimited File MNB-CoreBanking → absolute path to the CSV.", "Entitlement attribute: entitlement."]),
           ("Aggregate", ["Task Aggregate MNB-CoreBanking; run; verify counts."]),
           ("Ownership", ["Set owner to daniel.griffin or spadmin with note of real owner."]),
           ("Control narrative", ["Write: Core access requires manager + ops owner approval."])],
          ["Do not mix core accounts into low-risk apps casually."],
          ["Why split core from the inventory dump?", "What risk tier is CORE?", "Who is a sensible business owner?"],
          ["Create a population of CORE holders."]),

        L(12, "onboard-sap-finance", "Onboard SAP Finance", "Intermediate", "Applications", "60",
          "Finance ERP access shows up in every regulatory conversation. You need clean account-to-person linkage.",
          "Finance directs you to onboard MNB-SAP-Finance.csv. jordan.reed already holds SAP_FI plus AWS—your future SoD case.",
          "Treat SAP as its own application object even if data started in a consolidated dump.",
          ["Create MNB-SAP-Finance", "Aggregate", "Identify SAP holders", "Note SoD partner AWS_ADMIN"],
          [("Create & aggregate", ["Build MNB-SAP-Finance from apps/MNB-SAP-Finance.csv and aggregate."]),
           ("Holder review", ["Search identities with SAP_FI; list in notebook."]),
           ("Toxic pair preview", ["Confirm jordan.reed also has AWS_ADMIN in IT inventory."]),
           ("Owner", ["Assign deepa.nair as conceptual owner."]),
           ("Requestability", ["SAP_FI is requestable only with Finance approval—document."])],
          ["Finance owners must participate in certifications—not only IT."],
          ["Why is SAP critical?", "Which lesson will enforce SAP vs AWS SoD?", "Name the scripted toxic user."],
          ["Export a simple CSV of SAP holders from a search for evidence."]),

        L(13, "onboard-aws-cloud", "Onboard AWS Cloud Admin", "Intermediate", "Applications", "60",
          "Cloud admin is modern break-glass. Unowned AWS access is an incident.",
          "Platform engineering provides MNB-AWS-Cloud.csv. Contractors sometimes appear here—watch MNB00093.",
          "AWS_ADMIN is critical, non-birthright, and SoD-sensitive with finance/core.",
          ["Create MNB-AWS-Cloud", "Aggregate", "Flag contractor holders", "Document break-glass relationship to PRIV_BREAK"],
          [("Onboard", ["Create MNB-AWS-Cloud; aggregate."]),
           ("Contractor lens", ["Find contractor users with AWS_ADMIN."]),
           ("Orphan tease", ["Note raj.external uses vendor-mail.invalid — correlation will struggle."]),
           ("Control", ["Write: AWS_ADMIN requires Technology Director approval + time limit."]),
           ("Cert scope note", ["AWS must be in every privileged access campaign."])],
          ["Cloud entitlements drift fast—aggregate frequently."],
          ["Why contractors + AWS need extra scrutiny?", "What email problem does MNB00093 illustrate?", "Birthright or request-only?"],
          ["Draft an AWS joiner checklist (ticket, MFA, expiry)."]),

        L(14, "onboard-wire-portal", "Onboard Wire Portal (Dual Control)", "Intermediate", "Applications", "60–90",
          "Payment rails require dual control. Modeling initiate vs approve as separate entitlements is non-negotiable.",
          "Treasury runs Wire Portal. priya.wire has WIRE_INIT; marcus.approve has WIRE_APPR. Nobody should have both without exception.",
          "Onboard MNB-WirePortal.csv (or the split initiator/approver files). These entitlements anchor SoD and certs.",
          ["Create MNB-WirePortal", "Aggregate both entitlements", "Verify Priya vs Marcus split", "Document dual-control narrative"],
          [("Inspect files", ["Compare MNB-WirePortal.csv with the initiator/approver splits."]),
           ("Create app", ["Onboard MNB-WirePortal with entitlement attribute."]),
           ("Aggregate & verify", ["Confirm Priya initiate-only and Marcus approve-only."]),
           ("Owner", ["Owner rachel.evans."]),
           ("Write control", ["“Wire initiation and approval are mutually exclusive except documented MNB exceptions.”"])],
          ["Never collapse initiate/approve into one entitlement code."],
          ["Who initiates? Who approves?", "What SoD pair will you create later?", "Why split files sometimes help?"],
          ["Onboard ACH_OPS holders from the inventory for a second payment control."],
          ["apps/MNB-WirePortal.csv"]),

        L(15, "onboard-directory-and-crm", "Directory, CRM & Digital Channel Apps", "Intermediate", "Applications", "60",
          "Baseline directory access and CRM are high volume; digital channel apps are high impact. Both need governance.",
          "You onboard MNB-ActiveDirectory, MNB-Salesforce-CRM, MNB-InternetBanking, and MNB-Ecommerce-Ops extracts to complete Meridian’s app footprint.",
          "Volume apps need strong correlation and birthright design; digital apps need SoD (IBSI vs ECOM).",
          ["Onboard AD + CRM apps", "Onboard IBSI + ECOM apps", "Verify kai.nguyen digital dual access", "Update app inventory table"],
          [("AD & CRM", ["Create and aggregate MNB-ActiveDirectory and MNB-Salesforce-CRM."]),
           ("Digital pair", ["Create MNB-InternetBanking and MNB-Ecommerce-Ops; aggregate."]),
           ("Find dual holder", ["Confirm kai.nguyen holds IBSI and ECOM."]),
           ("Inventory table", ["Update notebook: app → file → owner → risk."]),
           ("Aggregation schedule note", ["AD nightly; digital twice daily if changes are frequent—document intent."])],
          ["Birthright usually includes ELDAP; almost never IBSI+ECOM together."],
          ["Which digital SoD pair exists?", "Is ELDAP birthright-worthy?", "Name the digital dual-holder persona."],
          ["Mark CRM requestable for relationship managers."]),

        L(16, "multi-app-aggregation-strategy", "Multi-App Aggregation Strategy", "Intermediate", "Applications", "45–60",
          "Connector sprawl without a strategy creates race conditions and partial cubes. Order and batching are controls.",
          "Meridian now has HR + inventory + platform apps. You define the aggregation strategy ops will run forever.",
          "Authoritative first; then directories; then business apps; refresh after batches. Document RPO expectations for audit.",
          ["Write aggregation runbook", "Run a full lab pipeline once", "Record durations", "Define failure triage"],
          [("Runbook", ["Document exact task order and schedules."]),
           ("Execute pipeline", ["Run HR → IT inventory → Wire → SAP → AWS → refresh."]),
           ("Timing", ["Note durations in evidence—even if seconds in lab."]),
           ("Failure matrix", ["If HR fails, stop. If one target app fails, continue others but ticket it."]),
           ("Comms", ["Draft a Slack/email blurb ops would send on partial failure."])],
          ["Partial success still needs tickets—silent gaps fail exams."],
          ["What runs first and why?", "What do you do if Wire aggregate fails?", "Where does refresh sit?"],
          ["Add a calendar reminder simulation for Monday morning pipeline check."]),

        L(17, "correlation-basics", "Account Correlation Basics", "Intermediate", "Correlation", "60",
          "Uncorrelated accounts are unowned access—audit poison. Correlation attaches accounts to people.",
          "Meridian’s IT accounts must attach to HR identities. You configure correlation on MNB-IT-Access using email/employeeId.",
          "Correlation rules match account attributes to identity attributes. Failures become orphan/uncorrelated accounts.",
          ["Configure correlation on MNB-IT-Access", "Re-aggregate / refresh", "Inspect linked accounts on Priya", "List uncorrelated accounts"],
          [("Choose keys", ["Prefer employeeId then email. Document the order."]),
           ("Configure", ["On MNB-IT-Access set correlation to identity employeeId/email."]),
           ("Re-run", ["Aggregate MNB-IT-Access + Refresh MNB Identities."]),
           ("Verify", ["Open priya.wire—IT account should be linked."]),
           ("Orphans", ["Find uncorrelated accounts; expect raj.external / vendor-mail issues."])],
          ["Authoritative apps correlate differently than targets.", "Email typos create permanent orphans."],
          ["What is an uncorrelated account?", "Best correlation key at Meridian?", "Which persona is designed to break email match?"],
          ["Write Meridian’s correlation control narrative paragraph."]),

        L(18, "correlation-rules-advanced", "Correlation Rules & Edge Cases", "Intermediate", "Correlation", "60–90",
          "Real banks have dual emails, contractors, and legacy usernames. Rules must handle edges without false merges.",
          "You harden correlation: employeeId primary, email secondary, and manual correlation for stubborn orphans.",
          "False positives (two people merged) are worse than orphans. Prefer precision; remediate leftovers with process.",
          ["Document primary/secondary keys", "Attempt manual correlation for one orphan", "Prevent identity merge mistakes", "Define weekly orphan review"],
          [("Rule doc", ["Write correlation precedence for Meridian."]),
           ("Manual correlate", ["Manually correlate one stubborn account if UI allows."]),
           ("Ghost account", ["Decide: disable AWS for raj.external until HR email matches @meridiannb.com."]),
           ("Weekly control", ["Define owner (IAM01) and SLA for uncorrelated count."]),
           ("Evidence", ["Screenshot uncorrelated list before/after."])],
          ["Never correlate by firstName+lastName alone.", "Contractors often need separate authoritative sources later."],
          ["Why is name-based correlation dangerous?", "What is Meridian’s orphan SLA?", "Primary key?"],
          ["Propose a contractor HR file as a second authoritative source."]),

        L(19, "uncorrelated-remediation", "Uncorrelated Account Remediation", "Intermediate", "Correlation", "45–60",
          "Finding orphans is incomplete; remediating them is the control. Tickets and disables close the loop.",
          "You run an uncorrelated account review for Meridian and practice decision classes: correlate, disable, delete (lab), or exception.",
          "Remediation outcomes must be evidenced. Managers of record may not exist—security owns the backlog.",
          ["Export/list uncorrelated accounts", "Classify each", "Disable or correlate at least one", "Record decisions"],
          [("List", ["Collect uncorrelated accounts from IIQ."]),
           ("Classify", ["Table: account → decision → rationale."]),
           ("Act", ["Correlate or mark for disable; re-aggregate if needed."]),
           ("Backlog owner", ["Assign SEC/IAM as backlog owner."]),
           ("Metric", ["Record starting orphan count as a baseline KPI."])],
          ["Exceptions need expiry dates.", "Deleted accounts in prod need change tickets—lab is freer."],
          ["Four decision classes?", "Who owns the orphan backlog?", "Why expiry on exceptions?"],
          ["Create a fake ServiceNow ticket number scheme in your notebook (MNB-INC-####)."]),

        L(20, "orphan-dormant-hunting", "Orphan & Dormant Access Hunting", "Intermediate", "Correlation", "45–60",
          "Terminated staff with live entitlements are tomorrow’s headline. Hunting is proactive assurance.",
          "samir.hassan is terminated but still carries access in the inventory. You build a hunt for inactive identities with accounts.",
          "Combine HR status with account presence. Dormant accounts may also show accountStatus=disabled inconsistently—note data quality.",
          ["Find terminated with access", "Document residual entitlements", "Define leaver defect severity", "Propose auto-remediation trigger"],
          [("Search", ["Find status=0 identities that still show MNB-* accounts/ents."]),
           ("Case file", ["Open samir.hassan and list residual entitlements."]),
           ("Severity", ["Classify SAP/AWS/Core residuals as Sev-1."]),
           ("Trigger idea", ["Lifecycle leaver should disable within hours—write target SLA."]),
           ("Report seed", ["Name a future report MNB-Terminated-With-Access."])],
          ["Data quality issues (disabled vs active flags) are findings too."],
          ["Who is the seeded leaver with residual access?", "Sev-1 examples?", "What SLA would you pitch?"],
          ["Add on-leave users with privileged access as a second hunt."]),

        L(21, "manager-hierarchy", "Manager Hierarchy & Reassignment", "Intermediate", "Correlation", "45",
          "Approvals and certifications collapse without accurate managers. Hierarchy is an operational dependency.",
          "You validate managerId chains from HR and practice what happens when a manager leaves.",
          "Manager correlation typically uses HR manager employee ids. Broken chains route work items wrongly.",
          ["Validate 3 manager chains", "Identify empty managerId leaders", "Simulate manager change in HR file", "Observe work item routing implications"],
          [("Chain check", ["Pick priya.wire → manager → manager’s manager; draw it."]),
           ("Executives", ["Confirm leaders with empty managerId are intentional tops."]),
           ("Mover of manager field", ["Change one user’s managerId in HR; aggregate + refresh; verify cube."]),
           ("Risk note", ["Write what happens to open certifications if manager terminates."]),
           ("Control", ["HR must update managers before terminations when possible."])],
          ["Do not invent managers in IIQ that HR does not know."],
          ["Why do certs need managers?", "What is the risk when managerId is wrong?", "Top-level signal in data?"],
          ["Define a fallback certifier (rachel.evans or security) for broken chains."]),

        L(22, "attribute-sync-hygiene", "Identity Attribute Sync Hygiene", "Intermediate", "Correlation", "45",
          "Conflicting attribute sources create flip-flops. Authoritative wins; targets should not overwrite HR truth.",
          "You confirm email, department, and status flow from MNB-HR and are not clobbered by IT apps.",
          "Attribute promotion rules and application authoritative flags determine winners during refresh.",
          ["Trace email source", "Prevent IT app from owning status", "Document source-of-truth table", "Fix one mis-mapped attribute if found"],
          [("Source table", ["For email, dept, status, manager—write source app."]),
           ("Verify", ["Change a jobTitle only in IT file; ensure HR title still wins on identity if configured."]),
           ("Guardrail", ["Confirm MNB-IT-Access is not authoritative."]),
           ("Document", ["Publish source-of-truth table to evidence."]),
           ("Exception", ["Note any attribute that must come from a target app and why."])],
          ["Silent overwrites are worse than hard failures."],
          ["Which app owns status?", "Why IT titles are untrustworthy?", "What is flip-flopping?"],
          ["Add locationCode to the source-of-truth table."]),

        L(23, "role-model-intro", "Role Model Introduction", "Intermediate", "Roles", "45–60",
          "Roles turn entitlement soup into business language. Without roles, every request is a snowflake.",
          "Meridian adopts IT roles + business roles. Birthright for employees; specialized packs for Treasury, Developers, and Risk.",
          "Bundles (roles) group entitlements. Assignment rules tie roles to HR attributes. Detection shows what you already have.",
          ["Explain IT vs business roles", "Sketch Meridian role catalog", "Name birthright vs requestable roles", "Align roles to dept/job codes"],
          [("Catalog sketch", ["Draft roles: MNB-Birthright-Employee, MNB-Role-Developer, MNB-Role-Treasury-Initiate, MNB-Role-Treasury-Approve, MNB-Role-CloudAdmin (request)."]),
           ("Mapping", ["Map TEL01 → birthright only; WIR01 → initiate role; DEV01 → developer role."]),
           ("Anti-goals", ["CloudAdmin and WireApprove are never automatic birthright."]),
           ("Naming", ["Stick to MNB-Role-* and MNB-Birthright-*."]),
           ("Stakeholder", ["List who must approve the catalog (HR, Risk, IT, Treasury)."])],
          ["Role explosion is real—start narrow."],
          ["IT vs business role?", "Which roles are request-only?", "Why approve role not birthright?"],
          ["Add MNB-Role-AML-Investigator draft."]),

        L(24, "birthright-employee-role", "Birthright Employee Role", "Intermediate", "Roles", "60–90",
          "Joiners should be productive on day one without tickets for baseline access. Birthright is that promise—and a liability if over-scoped.",
          "You create MNB-Birthright-Employee granting ELDAP for active employees.",
          "Assignment rule: has MNB-HR account AND active status AND workerType Employee (contractors may differ).",
          ["Create MNB-Birthright-Employee", "Attach ELDAP", "Write assignment rule", "Refresh and verify tellers receive it", "Ensure terminated do not"],
          [("Create role", ["Bundle MNB-Birthright-Employee with ELDAP entitlement."]),
           ("Assignment", ["Rule/selector: active employees."]),
           ("Refresh", ["Run Refresh MNB Identities with role assignment enabled."]),
           ("Verify joiner", ["amelia.brooks / tellers show birthright; samir.hassan does not."]),
           ("Document", ["Birthright composition + exclusion rules."])],
          ["Birthright should be boring and minimal."],
          ["What entitlement is in birthright?", "Contractors included?", "How do leavers lose it?"],
          ["Create MNB-Birthright-Contractor with tighter scope."]),

        L(25, "dept-job-roles", "Department & Job-Based Roles", "Intermediate", "Roles", "60–90",
          "Most access follows the desk you sit in. Job-coded roles beat one-off entitlements for movers.",
          "You build roles driven by departmentCode/jobCode: developer pack, RM CRM pack, treasury initiate pack.",
          "Mover events work when roles key off HR codes that change with transfers.",
          ["Create MNB-Role-Developer", "Create MNB-Role-RelationshipManager", "Create MNB-Role-WireInitiator", "Verify assignment after refresh"],
          [("Developer", ["Entitlements DWRP, ODS; rule jobCode in DEV01/SRE01."]),
           ("RM", ["CRM (+ ODS optional); rule RM01/LO01."]),
           ("Wire initiator", ["WIRE_INIT; rule WIR01—not WIR02."]),
           ("Refresh & verify", ["Check known personas gained roles."]),
           ("Mover preview", ["Note Priya’s scenario file switches her to RM01—roles should follow in JML lessons."])],
          ["Keep wire approve separate from initiator role forever."],
          ["Which job gets WIRE_INIT role?", "What makes movers work?", "Developer entitlements?"],
          ["Add operations CORE role for OPS01."]),

        L(26, "it-role-packaging", "IT Role Packaging & Least Privilege", "Intermediate", "Roles", "45–60",
          "Packaging reduces request friction but can smuggle privilege. Every entitlement in a role needs a reason.",
          "You review role compositions for least privilege and split any risky bundles.",
          "If a role contains AWS_ADMIN plus DWRP “for convenience,” split it. Convenience is how banks fail SoD.",
          ["Audit each role’s entitlements", "Split any toxic combo", "Add role descriptions owners understand", "Mark requestable roles"],
          [("Audit", ["Table role → entitlements → justification."]),
           ("Split", ["Ensure CloudAdmin is standalone requestable role."]),
           ("Descriptions", ["Write business descriptions, not tech jargon only."]),
           ("Requestable", ["Developer optional packs requestable; birthright not requested."]),
           ("Peer review", ["Have a fictional Risk sign-off line in your notebook."])],
          ["Roles are controls—treat composition changes as changesets."],
          ["Why split CloudAdmin?", "What belongs in a role description?", "Who signs role composition?"],
          ["Introduce required roles vs optional add-ons concept."]),

        L(27, "role-detection-vs-assignment", "Role Detection vs Assignment", "Intermediate", "Roles", "45–60",
          "Detection explains what you already have; assignment decides what you should have. Confusing them breaks certifications.",
          "You observe detected roles from entitlements versus assigned birthright roles after refresh.",
          "Detection is analytical; assignment is normative. Both appear on the cube and matter in different processes.",
          ["Identify detected vs assigned on a cube", "Explain difference in Meridian words", "Use detection to find outliers", "Confirm assignment for birthright"],
          [("Inspect cube", ["Open a developer identity; note detected/assigned sections."]),
           ("Outliers", ["Find someone with AWS_ADMIN who lacks CloudAdmin assigned role—expected if request-only."]),
           ("Narrative", ["Write two sentences Meridian managers would understand."]),
           ("Refresh flags", ["Confirm which refresh options affect assignment vs detection."]),
           ("Cert implication", ["Certs may show entitlements, roles, or both—decide Meridian’s standard."])],
          ["Do not revoke birthright thinking it was only detected noise."],
          ["Detection vs assignment?", "Why can AWS appear without CloudAdmin role?", "What should managers certify?"],
          ["Propose certifying roles for low-risk and entitlements for critical."]),

        L(28, "privileged-access-roles", "Privileged Access Role Design", "Advanced", "Roles", "60",
          "Privileged access needs time bounds, approvals, and monitoring. Standing cloud admin is a governance failure mode.",
          "You design MNB-Role-CloudAdmin and MNB-Role-BreakGlass as request-only with strict approval logic (configured in later LCM lessons).",
          "Privileged roles should be rare, owned, and certified frequently.",
          ["Create privileged roles", "Exclude from birthright", "Define approval expectations", "Add to monthly priv cert scope list"],
          [("Create roles", ["CloudAdmin → AWS_ADMIN; BreakGlass → PRIV_BREAK."]),
           ("Guards", ["Not assignable by automated birthright rules."]),
           ("Approvers", ["Technology Director + Security for BreakGlass."]),
           ("Cert frequency", ["Monthly for privileged; quarterly for standard."]),
           ("Runbook", ["Joiner never auto-gets these; leaver revokes same day."])],
          ["Break-glass without logging is theater."],
          ["Who approves break-glass?", "Cert frequency for priv roles?", "Birthright eligible?"],
          ["Draft MFA / PAM requirement note alongside the role."]),

        L(29, "joiner-lifecycle", "Joiner Lifecycle", "Intermediate", "Lifecycle", "60–90",
          "Joiners stuck without access create shadow IT. Automated birthright with HR triggers is the bank’s first impression of IAM.",
          "You process scenarios/joiner/hr-delta-new-hire.csv (Nina Foster) through aggregate + refresh + birthright.",
          "Lifecycle joiner events can trigger workflows; in file labs, HR row insertion is the business event.",
          ["Insert joiner delta into HR file", "Aggregate + refresh", "Confirm identity + birthright", "Ticket any missing app access", "Write joiner SLA"],
          [("Apply delta", ["Append joiner CSV row into HRApplications.txt carefully."]),
           ("Pipeline", ["Aggregate MNB-HR; Refresh MNB Identities."]),
           ("Verify", ["Find nina.joiner; confirm ELDAP birthright."]),
           ("Gaps", ["CRM/Teller apps may need separate requests—note."]),
           ("SLA", ["Identity within 1 hour of HR active; birthright same cycle."])],
          ["Validate CSV column counts after edits.", "LCM event config is stretch if init-lcm imported."],
          ["What triggers joiner in this lab?", "What must Nina get automatically?", "Joiner SLA?"],
          ["Wire a joiner lifecycle event to create a work item if available."],
          ["scenarios/joiner/hr-delta-new-hire.csv"]),

        L(30, "mover-transfers", "Mover / Transfer Events", "Intermediate", "Lifecycle", "60–90",
          "Movers who keep old access accumulate privilege. Transfers must drop old birthright packs and gain new ones.",
          "Priya moves from Wire Specialist to Relationship Manager using scenarios/mover/hr-delta-priya-to-commercial.csv.",
          "Attribute change → refresh → role re-evaluation. WIRE_INIT should become request/removal territory; CRM role should appear.",
          ["Apply mover delta", "Refresh roles", "Confirm role loss/gain intent", "Request removal of wire initiate if still present", "Document mover control"],
          [("Apply HR change", ["Update Priya’s row from mover scenario (dept CML, job RM01, manager MNB00006)."]),
           ("Pipeline", ["Aggregate + refresh."]),
           ("Roles", ["Expect RM role path; wire initiator assignment should stop for job rule."]),
           ("Entitlement cleanup", ["If WIRE_INIT remains, create remediation action/work item."]),
           ("Control statement", ["Movers reviewed within 5 business days for residual high-risk access."])],
          ["Movers are harder than joiners because removal is required.", "SoD risk spikes during transition windows."],
          ["What changed for Priya?", "Why is residual WIRE_INIT dangerous on an RM?", "Mover SLA?"],
          ["Configure a lifecycle mover event on departmentCode change."],
          ["scenarios/mover/hr-delta-priya-to-commercial.csv"]),

        L(31, "leaver-disablement", "Leaver & Access Disablement", "Intermediate", "Lifecycle", "60–90",
          "Leavers with SAP and cloud keys are material incidents. Same-day disablement is a board-level expectation.",
          "You terminate jordan.reed via scenarios/leaver/hr-delta-terminate-jordan.csv and plan disabling accounts/entitlements.",
          "Leaver workflow: HR status→identity inactive→disable links→revoke roles→notify manager→evidence.",
          ["Apply leaver delta", "Refresh", "Identify residual entitlements", "Disable or plan disable of critical access", "Write leaver control standard"],
          [("Terminate", ["Set Jordan’s HR row from leaver scenario."]),
           ("Pipeline", ["Aggregate + refresh; confirm inactive signals."]),
           ("Residuals", ["List SAP_FI, AWS_ADMIN, GL_POST still present."]),
           ("Remediate", ["Practice disable/revoke steps available in your lab."]),
           ("Standard", ["Write Meridian leaver standard: timing, scope, notifications, evidence retention."])],
          ["onLeave is not leaver—do not conflate.", "Privileged leavers get Sev-1 treatment."],
          ["Leaver trigger attribute?", "Why Jordan is a scary leaver?", "Four parts of leaver standard?"],
          ["Also re-check samir.hassan residuals as a backlog defect."],
          ["scenarios/leaver/hr-delta-terminate-jordan.csv"]),

        L(32, "contractor-lifecycle", "Contractor & Contingent Worker Lifecycle", "Intermediate", "Lifecycle", "45–60",
          "Contractors often outlive their statements of work in the directory. Separate workerType handling is mandatory.",
          "You define contractor join/leave rules: no broad birthright, mandatory end dates, manager attestation.",
          "Filter populations and roles by workerType. Cloud contractors need expiry.",
          ["List contractors in HR", "Define contractor birthright policy", "Set expiry expectation for AWS contractors", "Draft attestation cadence"],
          [("Inventory", ["Export contractor list from HR data."]),
           ("Policy", ["Contractors get minimal ELDAP only if required; else request."]),
           ("AWS contractors", ["Any contractor with AWS_ADMIN needs end date + weekly review."]),
           ("Attestation", ["Manager monthly attestation for contingent workers."]),
           ("Ghost", ["Tie raj.external remediation to contractor onboarding email quality."])],
          ["SOW end date should live in HR or a companion source."],
          ["How do contractors differ from employees in birthright?", "Attestation cadence?", "Why AWS contractors are special?"],
          ["Propose a second authoritative Contingent Worker file."]),

        L(33, "leave-of-absence", "Leave of Absence Controls", "Intermediate", "Lifecycle", "45",
          "People on leave still have credentials. Temporary freeze prevents quiet misuse without full termination chaos.",
          "sofia.torres is onLeave=true. You design a freeze: disable interactive access, keep identity, notify manager.",
          "onLeave triggers should not run full leaver destruction if return is expected—but privileged access should pause.",
          ["Identify on-leave users", "Define freeze vs terminate", "Create manager work item concept", "Document return-to-work re-enable"],
          [("Find", ["Filter onLeave=true in HR."]),
           ("Policy", ["Write freeze: disable AD login / revoke priv ents; retain CRM data ownership notes."]),
           ("Notify", ["Manager receives review work item within 24h."]),
           ("Return", ["onLeave false → controlled re-enable + mini cert."]),
           ("Stretch config", ["Lifecycle event on onLeave if LCM available."])],
          ["Leaving leave active with wire rights is unacceptable."],
          ["How is leave different from terminate?", "What should happen to privileged ents on leave?", "Return control?"],
          ["Add policy flagging on-leave + WIRE_* or AWS_ADMIN."]),

        L(34, "rapid-offboarding-drill", "Rapid Offboarding Incident Drill", "Advanced", "Lifecycle", "60",
          "Involuntary terminations and insider risk need a drill, not a wiki page written during the incident.",
          "You run a tabletop + lab drill: security calls for immediate lockout of a payments user.",
          "Break-glass disable path: who can disable, evidence, follow-up HR alignment, and cert of residual access.",
          ["Write rapid offboard runbook", "Execute emergency disable on a lab user", "Capture timeline evidence", "Schedule follow-up HR reconcile", "Identify gaps"],
          [("Runbook", ["Steps: verify requester, disable AD/core/wire, revoke roles, snapshot entitlements, ticket, notify."]),
           ("Execute", ["Pick marcus.approve or a copy identity; disable what you can in lab."]),
           ("Timeline", ["Log timestamps in evidence folder."]),
           ("Reconcile", ["HR status must catch up—create fictional INC ticket."]),
           ("Retro", ["List gaps (no PAM, no SMS approve, etc.)."])],
          ["Drills without timestamps teach little.", "Never skip identity verification of the requester."],
          ["Who may authorize rapid offboard?", "What systems first?", "Why HR reconcile after?"],
          ["Add communications template for Legal/HR."]),

        L(35, "access-request-catalog", "Access Request Catalog", "Intermediate", "Requests", "60–90",
          "If people cannot request safely, they bypass you. A clean catalog is how IAM becomes the path of least resistance.",
          "Relationship managers need CRM; developers need DWRP. You mark requestable roles/entitlements and submit a request.",
          "LCM access requests create IdentityRequest objects, approvals, and provisioning plans.",
          ["Mark CRM/DWRP requestable", "Submit request for a Meridian user", "Track IdentityRequest", "Ensure AWS not casually requestable"],
          [("Catalog", ["Mark MNB-Role-RelationshipManager / CRM requestable; Developer optional entitlements requestable."]),
           ("Guard", ["AWS_ADMIN / PRIV_BREAK hidden or strongly controlled."]),
           ("Submit", ["As end user or admin-on-behalf, request CRM for an RM-aligned user."]),
           ("Track", ["Open IdentityRequest / work items generated."]),
           ("UX note", ["Display names from dictionary must appear in catalog."])],
          ["Requestable ≠ approved. Approvals still matter.", "Birthright items should not clutter the catalog."],
          ["What should be requestable?", "What must not?", "Where do you track the request?"],
          ["Add Wire Initiate as requestable with Treasury owner approval only."]),

        L(36, "approval-chains", "Approval Chains & Escalations", "Intermediate", "Requests", "60",
          "Wrong approvers create either rubber stamps or deadlock. Chains must mirror Meridian’s risk.",
          "You configure/observe manager approval for CRM and dual approval for AWS_ADMIN (manager + app owner).",
          "Approval schemes can be serial/parallel. Escalations handle absent managers.",
          ["Trace approval for a low-risk request", "Design dual approval for privileged", "Test reject path", "Define escalation after N days"],
          [("Low-risk", ["CRM request → manager only; complete approval."]),
           ("Privileged design", ["AWS → manager + christopher.hayes."]),
           ("Reject", ["Reject one request; confirm no provisioning."]),
           ("Escalation", ["Document 3-day escalate to manager’s manager / security."]),
           ("Evidence", ["Screenshot work item history."])],
          ["Parallel approvals speed priv requests without removing control."],
          ["Who approves CRM?", "Who approves AWS?", "What does reject guarantee?"],
          ["Add Risk approval for anything in sod-matrix."]),

        L(37, "break-glass-access", "Emergency / Break-Glass Access", "Advanced", "Requests", "45–60",
          "Outages tempt shared passwords. A governed break-glass path is safer than heroics on Zoom.",
          "You define Meridian break-glass: short-lived PRIV_BREAK, security approval, automatic expiry, post-incident cert.",
          "Model as requestable role with aggressive sunset and mandatory comment/ticket.",
          ["Document break-glass policy", "Create/request PRIV_BREAK path", "Require ticket number in comments", "Schedule post-access review"],
          [("Policy page", ["Max 8 hours, SEC approval, recorded bridge call optional."]),
           ("Request", ["Submit break-glass with comment MNB-INC-1042."]),
           ("Approve", ["Security identity approves."]),
           ("Sunset", ["Revoke same day; verify removal."]),
           ("Post-review", ["Manager + SEC review within 2 business days."])],
          ["Standing break-glass accounts fail the purpose."],
          ["Max duration?", "Required comment content?", "Post-review window?"],
          ["Integrate with PAM conceptually in your write-up."]),

        L(38, "identity-request-tracking", "IdentityRequest Tracking & Auditing", "Intermediate", "Requests", "45",
          "Examiners ask who approved what when. Request objects and audit logs are your answer.",
          "You trace an IdentityRequest end-to-end and export evidence suitable for audit.",
          "IdentityRequest, work items, provisioning transactions, and audit config form the trail.",
          ["Open a completed request", "Trace approvals", "Find provisioning status", "Export/screenshot evidence pack"],
          [("Locate request", ["Find your CRM or AWS request record."]),
           ("Approvals", ["List approver, timestamps, decision."]),
           ("Provisioning", ["See if plan executed or pending."]),
           ("Audit", ["Check audit search for access request events if enabled."]),
           ("Pack", ["Assemble evidence pack PDF/screens in folder."])],
          ["If audit is off, turn on relevant audit actions in lab."],
          ["Which objects prove approval?", "What if provisioning pending?", "What goes in an evidence pack?"],
          ["Enable additional audit actions thoughtfully and re-test."]),

        L(39, "sod-fundamentals", "SoD Fundamentals for Banking", "Intermediate", "Policies", "45–60",
          "Separation of duties is how banks prevent one person from moving money alone. Policies make that enforceable in IAM.",
          "You translate sod-matrix.csv into IdentityIQ policy objects and explain business rationales to Risk.",
          "SoD policies flag identities holding toxic entitlement/role pairs during refresh or continuous checks.",
          ["Read Meridian SoD matrix", "Pick two pairs to implement", "Explain business rationale in writing", "Run policy check refresh"],
          [("Matrix", ["Open reference/sod-matrix.csv; discuss each pair."]),
           ("Choose", ["Implement WIRE_INIT+WIRE_APPR and SAP_FI+AWS_ADMIN first."]),
           ("Write rationales", ["Use bank language, not only tech codes."]),
           ("Create policies", ["Build entitlement SoD policies MNB-SOD-Wire-DualControl and MNB-SOD-Finance-Cloud."]),
           ("Refresh", ["Run Refresh MNB Identities with policy checking; observe violations."])],
          ["Mitigation is not ignorance—document exceptions."],
          ["Why wire dual control?", "Which persona violates finance-cloud?", "When do policies evaluate?"],
          ["Add IBSI+ECOM policy for kai.nguyen."],
          ["reference/sod-matrix.csv"]),

        L(40, "payment-dual-control-policy", "Payment Dual-Control Policy Deep Dive", "Advanced", "Policies", "60",
          "Payments SoD failures are existential. You harden wire/ACH policies and exception process.",
          "Ensure Priya/Marcus remain clean; create a deliberate bad combo user or temporarily assign both wire ents to see a violation.",
          "Policy violation work items, severity, and corrective actions must be defined with Treasury.",
          ["Validate clean split Priya/Marcus", "Induce a violation safely in lab", "Process violation decision", "Write exception expiry rules"],
          [("Baseline", ["Confirm no violation on Priya/Marcus."]),
           ("Induce", ["Temporarily grant both wire ents to a test user OR use jordan-like pattern."]),
           ("Detect", ["Refresh; open policy violation."]),
           ("Decide", ["Revoke preferred; if mitigate, set 30-day expiry + compensating control."]),
           ("Treasury signoff", ["Document rachel.evans approval requirement for exceptions."])],
          ["Never leave induced violations in shared labs."],
          ["Preferred response to wire SoD hit?", "Exception max life?", "Who signs exceptions?"],
          ["Extend policy to ACH_OPS + WIRE_INIT pair."]),

        L(41, "policy-violations-mitigation", "Policy Violations & Mitigation", "Intermediate", "Policies", "45–60",
          "Open violations without owners rot. Mitigation workflows are how Risk accepts residual risk consciously.",
          "You work jordan.reed (or restored persona) finance-cloud violation through revoke vs mitigate paths.",
          "Mitigations need compensations (extra monitoring, dual review) and expirations.",
          ["Open violation", "Try revoke path", "Try mitigate path with expiry", "Report open violations count"],
          [("Open", ["Navigate policy violations UI; filter MNB-SOD-*."]),
           ("Revoke", ["Remove AWS_ADMIN from finance user; refresh; confirm clear."]),
           ("Mitigate", ["On another violation, mitigate 14 days with comment."]),
           ("KPI", ["Record open vs mitigated vs closed counts."]),
           ("Owner", ["Risk owns acceptance; IAM owns tooling."])],
          ["Eternal mitigations are fake compliance."],
          ["Who accepts residual risk?", "Why expirations?", "IAM vs Risk ownership?"],
          ["Create report schedule for open violations weekly."]),

        L(42, "risk-scores", "Risk Scores & Scoring Models", "Advanced", "Policies", "45",
          "Not all identities deserve equal scrutiny. Risk scores focus certifications and monitoring where it matters.",
          "You explore identity risk / entitlement risk settings and bump scores for wire/cloud holders.",
          "Scoring informs certification prioritization and dashboards—not a replacement for SoD.",
          ["Inspect risk UI", "Raise risk for critical ents", "Identify top risky identities", "Decide how Meridian uses scores"],
          [("UI", ["Find risk score configuration / identity risk."]),
           ("Weights", ["Critical entitlements → higher weight."]),
           ("Top risk", ["Note who rises (jordan, cloud admins, wire)."]),
           ("Usage", ["Write: scores prioritize certs; they do not auto-revoke."]),
           ("Limitations", ["Scores lag; still need event-driven leavers."])],
          ["Do not chase score vanity—tie to actions."],
          ["What do scores drive at Meridian?", "Who should rank high?", "Limitation of scores?"],
          ["Propose a dashboard widget list for the IAM weekly meeting."]),

        L(43, "manager-certifications", "Manager Access Certifications", "Intermediate", "Certifications", "90–120",
          "Quarterly access reviews are how managers attest reality. Bad campaigns train managers to click Approve All.",
          "You launch a scoped manager certification for Treasury or a small population, using the sample email tone.",
          "Certifications generate work items per manager. Decisions: approve, revoke, delegate, allow exception.",
          ["Create MNB Manager Cert campaign", "Limit scope to high-risk ents", "Generate & open as manager", "Complete decisions", "Review email sample"],
          [("Scope", ["Include Wire/SAP/AWS entitlements; population MNB-Treasury or small set."]),
           ("Create", ["Manager certification named MNB-Q-Lab-Manager-Cert."]),
           ("Generate", ["Generate campaign; open work items."]),
           ("Decide", ["Approve valid CRM/ODS; revoke residuals that look wrong."]),
           ("Email", ["Compare lab-data/notifications/certification-sample.txt to IIQ notifications."])],
          ["Small scopes teach better than thousand-line monsters.", "Delegation needs rules."],
          ["Why scope tight?", "Four decision types?", "Who gets the email?"],
          ["Enable email in lab mail settings if available and capture a message."],
          ["notifications/certification-sample.txt"]),

        L(44, "app-owner-certifications", "Application Owner Certifications", "Intermediate", "Certifications", "60–90",
          "Managers know people; app owners know toxic entitlements. Owner certs catch what managers miss.",
          "You run an application owner certification on MNB-WirePortal or MNB-AWS-Cloud.",
          "Owner certs review who has access on an application regardless of HR manager quality.",
          ["Create app-owner cert", "Complete as owner", "Compare quality vs manager cert", "Document when to use which"],
          [("Create", ["Application owner cert for MNB-WirePortal."]),
           ("Complete", ["Decide on each account/entitlement."]),
           ("Compare", ["Write 5 lines: manager vs owner strengths."]),
           ("Cadence", ["Owner certs semi-annual for critical apps; manager quarterly."]),
           ("Evidence", ["Save sign-off screenshots."])],
          ["Owner must be a real accountable human—not a DL nobody reads."],
          ["When prefer owner cert?", "Cadence for critical apps?", "Owner anti-pattern?"],
          ["Run AWS owner cert next."]),

        L(45, "targeted-campaigns", "Targeted & Focused Campaigns", "Advanced", "Certifications", "45–60",
          "After incidents or failed controls, targeted campaigns beat waiting for quarter-end.",
          "You design a focused cert: Terminated-with-access, Contractors-with-AWS, or On-leave-with-privileged.",
          "Targeted certs are agile risk responses and examiner favorites when tied to findings.",
          ["Pick a focus risk", "Build population", "Launch micro-cert", "Close with remediation report"],
          [("Focus", ["Choose Terminated-with-access or Contractors-with-AWS."]),
           ("Population", ["Build/reuse population."]),
           ("Launch", ["Short-lived cert due in 5 days."]),
           ("Remediate", ["Revokes create work; track to close."]),
           ("Report", ["One-page summary for Risk committee."])],
          ["Micro-certs need executive air cover so managers prioritize."],
          ["Give one incident that justifies targeted cert.", "Due date strategy?", "What goes in the one-pager?"],
          ["Automate quarterly micro-cert for contractors."]),

        L(46, "cert-remediation-evidence", "Certification Remediation & Evidence", "Intermediate", "Certifications", "45–60",
          "A completed cert with open revokes is incomplete. Remediation closure is the real control.",
          "You follow revoke decisions into provisioning/work items and assemble an exam evidence binder.",
          "Evidence: campaign definition, population logic, completion %, revoke tickets, sampling of decisions.",
          ["Trace a revoke to outcome", "Measure completion %", "Build evidence binder checklist", "Sample 5 decisions for quality"],
          [("Trace revoke", ["Pick a revoke; follow to account disable/plan."]),
           ("Completion", ["Record % complete and late managers."]),
           ("Binder", ["Checklist of artifacts examiners want."]),
           ("QA sample", ["Review 5 approves—any rubber-stamping symptoms?"]),
           ("Improve", ["Propose training note for managers."])],
          ["Rubber-stamp detection: too-fast completes, approve-all patterns."],
          ["What proves a revoke happened?", "Binder contents?", "Rubber-stamp signals?"],
          ["Create a manager scorecard concept (on-time %, revoke rate)."]),

        L(47, "provisioning-troubleshooting", "Provisioning Plans & Troubleshooting", "Advanced", "Ops", "90",
          "Approvals without provisioning are theater. You must read plans and diagnose “nothing happened.”",
          "You inspect provisioning plans for a request/revoke and learn failure modes for file-based apps.",
          "Plans list account creates/modifies/deletes and attribute changes. Task results and logs explain failures.",
          ["Locate a provisioning plan", "Interpret operations", "Induce a safe failure (bad path)", "Fix and retry", "Write debug playbook"],
          [("Find plan", ["From IdentityRequest or refresh provisioning."]),
           ("Read", ["Identify Application, Native Identity, Attribute Requests."]),
           ("Break", ["Point a file connector at a bad path briefly; run; observe error."]),
           ("Fix", ["Restore path; retry; confirm success."]),
           ("Playbook", ["5 steps: request → plan → task result → app logs → retry."])],
          ["File connectors often “provision” by writing files—know your connector’s reality.", "Never debug only in the UI—use task results."],
          ["What is a provisioning plan?", "First place to look on failure?", "Why file apps confuse beginners?"],
          ["Enable more verbose logging temporarily in lab and capture a snippet."]),

        L(48, "audit-ready-reporting", "Audit-Ready Reporting & Dashboards", "Intermediate", "Ops", "60–90",
          "If you cannot show it, auditors assume it does not exist. Reports turn controls into evidence.",
          "You build/search reports: AWS holders, open SoD violations, cert completion, terminated-with-access.",
          "Standard reports + advanced search + scheduled delivery to Risk form Meridian’s assurance pack.",
          ["Run three assurance searches/reports", "Name them with dates", "Schedule one", "Map each to a control statement"],
          [("AWS holders", ["Report MNB-AWS-Holders-YYYY-MM-DD."]),
           ("SoD open", ["Report open MNB-SOD violations."]),
           ("Cert status", ["Completion for latest manager cert."]),
           ("Terminated access", ["Search seeded leavers with ents."]),
           ("Control map", ["Each report → control ID fiction e.g. CTL-IAM-12."])],
          ["Date-stamp report names for evidence hygiene.", "Schedule to humans who act—not only shared mailboxes."],
          ["Name three assurance reports.", "Why date-stamp?", "Who receives weekly SoD mail?"],
          ["Draft a monthly IAM metrics email outline."]),

        L(49, "email-templates-notifications", "Email Templates & Notifications", "Intermediate", "Ops", "45–60",
          "Notifications drive human SLAs. Bad emails get ignored; clear ones get certifications done.",
          "You review Meridian sample certification mail and locate IdentityIQ email templates to align tone and content.",
          "Templates cover certifications, approvals, policy violations, and lifecycle notices.",
          ["Compare sample mail to IIQ templates", "Identify cert email template", "Propose copy improvements", "Check recipient logic"],
          [("Sample", ["Read notifications/certification-sample.txt."]),
           ("Templates", ["Find EmailTemplate objects in Debug/UI."]),
           ("Improve", ["Rewrite subject/body for clarity and due date emphasis."]),
           ("Recipients", ["Manager vs owner vs requester—document."]),
           ("Noise control", ["Avoid spamming on every trivial event."])],
          ["From-addresses must be trusted domains (meridiannb.com) in real life."],
          ["What makes a cert email actionable?", "Where are templates stored?", "Noise risk?"],
          ["Draft a leaver notification to manager template."]),

        L(50, "capstone-exam-readiness", "Capstone: Exam Readiness & Go-Live Checklist", "Advanced", "Capstone", "90–120",
          "Go-live is a control statement, not a feeling. You prove Meridian can survive an internal audit week.",
          "Capstone: verify pipeline, SoD, certs, joiner/mover/leaver evidence, and produce a go-live checklist + residual risks.",
          "A production-ready IAM lab demonstrates closed-loop governance: data → roles → requests → policies → certs → provisioning → reports.",
          ["Run full aggregation+refresh pipeline", "Show one clean and one violated SoD case", "Show cert completion evidence", "Show joiner and leaver evidence", "Publish go-live checklist + residual risks"],
          [("Pipeline", ["HR → apps → refresh; save results."]),
           ("SoD demo", ["Marcus/Priya clean; one finance-cloud or digital dual case documented."]),
           ("Cert demo", ["Completed manager or owner cert with a revoke traced."]),
           ("JML demo", ["Nina joiner + Priya mover + a leaver packet."]),
           ("Checklist", [
               "Authoritative HR live; correlation keys documented; birthright minimal; priv request-only;",
               "SoD matrix enforced; cert cadences set; orphan KPI owned; rapid offboard drill dated;",
               "Reports scheduled; email templates reviewed; naming standards enforced; residual risks listed.",
           ]),
           ("Retro", ["List top 5 gaps before real bank production."])],
          ["Residual risk honesty beats greenwashed checklists.", "Keep MNB- prefixes until true prod cutover naming is approved."],
          ["What artifacts prove exam readiness?", "Name two residual risks you still accept.", "What is closed-loop governance?"],
          ["Optional: onboard a new app MNB-MobileDeposit with its own entitlements and repeat lessons 9–14 quickly."]),
    ]


def render_lesson(lesson: Lesson, prev_slug: str | None, next_slug: str | None) -> str:
    goals = "\n".join(f"- [ ] {g}" for g in lesson.goals)
    tips = "\n".join(f"- {t}" for t in lesson.tips)
    checks = "\n".join(f"{i}. {c}" for i, c in enumerate(lesson.checkpoint, 1))
    stretch = "\n".join(f"- {s}" for s in lesson.stretch)
    data = ""
    if lesson.data_files:
        data = "\n**Lab data:** " + ", ".join(f"`{d}`" for d in lesson.data_files) + "\n"

    task_blocks = []
    for title, steps in lesson.tasks:
        steps_txt = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
        task_blocks.append(f"### Task — {title}\n\n{steps_txt}\n")

    nav_prev = f"**Previous:** [Lesson {lesson.num - 1}]({prev_slug}.md)  \n" if prev_slug else ""
    nav_next = f"**Next:** [Lesson {lesson.num + 1}]({next_slug}.md)" if next_slug else "**You finished the 50-lesson Meridian curriculum.**"
    how = lesson.how
    if "```" not in how and len(how) < 400:
        how_block = how
    else:
        how_block = how

    return f"""# Lesson {lesson.num:02d} — {lesson.title}

**Level:** {lesson.level}  
**Track:** {lesson.track}  
**Time:** {lesson.minutes}  
**Prereq:** {"Lesson %02d" % (lesson.num - 1) if lesson.num > 1 else "Working IIQ login ([LOCAL_SETUP.md](../LOCAL_SETUP.md))"}  
{data}
## Why this matters

{lesson.why}

---

## Story

{lesson.story}

---

## How it works

{how_block}

---

## Lesson goals

{goals}

---

## Tasks

{chr(10).join(task_blocks)}
---

## Tips & tricks

{tips}

---

## Checkpoint

{checks}

---

## Stretch

{stretch}

---

{nav_prev}{nav_next}
"""


def write_lessons() -> list[Lesson]:
    lessons = curriculum()
    assert len(lessons) == 50, len(lessons)
    # remove old numbered lessons except archive
    for p in LESSONS.glob("*.md"):
        if p.name in ("README.md", "README.md.bak"):
            continue
        if p.name.startswith("0") or p.name[:2].isdigit():
            p.unlink()

    for i, lesson in enumerate(lessons):
        prev_slug = f"{lessons[i-1].num:02d}-{lessons[i-1].slug}" if i else None
        next_slug = f"{lessons[i+1].num:02d}-{lessons[i+1].slug}" if i < len(lessons) - 1 else None
        path = LESSONS / f"{lesson.num:02d}-{lesson.slug}.md"
        path.write_text(render_lesson(lesson, prev_slug, next_slug), encoding="utf-8")

    # README
    tracks: dict[str, list[Lesson]] = {}
    for les in lessons:
        tracks.setdefault(les.track, []).append(les)

    rows = "\n".join(
        f"| {l.num:02d} | [{l.title}]({l.num:02d}-{l.slug}.md) | {l.track} | {l.level} | {l.minutes} |"
        for l in lessons
    )
    track_toc = "\n".join(
        f"- **{name}:** lessons {items[0].num:02d}–{items[-1].num:02d}"
        for name, items in tracks.items()
    )

    readme = f"""# Meridian National Bank — IdentityIQ 50-Lesson Bundle

Progressive, hands-on path to learn **SailPoint IdentityIQ 8.5** by implementing realistic IAM work for a fictitious bank.

**Company:** Meridian National Bank (MNB)  
**Domain:** `meridiannb.com`  
**Your role:** IAM Engineer on the Identity Governance team  
**Platform:** Local IdentityIQ 8.5 lab from this repo  
**Published learn site:** build under `learn/` → host at `https://iam.lmsapp.us/learn`

---

## Before you start

1. Complete [LOCAL_SETUP.md](../LOCAL_SETUP.md) until you can log in as `spadmin`.  
2. Read [INFRASTRUCTURE.md](../INFRASTRUCTURE.md) once for vocabulary.  
3. Copy lab files:

```bash
mkdir -p ~/iiq-lab-data
cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/
cp -R lab-data/apps lab-data/scenarios lab-data/reference lab-data/notifications ~/iiq-lab-data/
```

---

## Tracks

{track_toc}

---

## Learning path (50 lessons)

| # | Lesson | Track | Level | Time |
| ---: | --- | --- | --- | --- |
{rows}

Work **in order**. Later lessons assume objects and data from earlier ones.

---

## How each lesson is structured

- **Why this matters** — control / business rationale  
- **Story** — Meridian context  
- **How it works** — concept in plain language  
- **Lesson goals** — what “done” means  
- **Tasks** — multi-step exercises  
- **Tips & tricks** — gotchas  
- **Checkpoint** — self-test  
- **Stretch** — optional harder practice  

---

## Meridian National Bank — lore & data

MNB is a mid-size retail + commercial bank with payments, digital channels, and shared-services tech in Kathmandu/Bengaluru.

| Org signal | Lab file |
| --- | --- |
| Employees & managers | `HRApplications.txt` / `hr/MNB-HR-Employees.csv` |
| Entitlement dump | `EmployeeData.txt` / `apps/MNB-IT-Access.csv` |
| Per-app extracts | `apps/MNB-*.csv` |
| SoD pairs | `reference/sod-matrix.csv` |
| Dictionaries | `reference/entitlement-dictionary.csv`, `job-codes.csv`, `departments.csv` |
| JML deltas | `scenarios/joiner|mover|leaver/` |
| Cert email tone | `notifications/certification-sample.txt` |

Scripted personas: `MNB00090`–`MNB00097` (wire split, toxic SAP+AWS, orphan cloud, leaver residual, on-leave RM, digital dual, pending joiner).

Regenerate data + lessons:

```bash
python3 tools/generate-mnb-curriculum.py
```

---

## Suggested pace

- **Weeks 1–2:** Foundations + Applications (01–16)  
- **Weeks 3–4:** Correlation + Roles (17–28)  
- **Weeks 5–6:** Lifecycle + Requests (29–38)  
- **Weeks 7–8:** Policies + Certs + Ops + Capstone (39–50)  

---

## Need help?

- Setup → [LOCAL_SETUP.md](../LOCAL_SETUP.md)  
- Concepts → [INFRASTRUCTURE.md](../INFRASTRUCTURE.md)  
- Homelab URL → [HOMELAB-CD.md](../HOMELAB-CD.md)  
- Product depth → PDFs in `identityiq-8.5/doc/`
"""
    (LESSONS / "README.md").write_text(readme, encoding="utf-8")
    return lessons


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Meridian lab-data (default) and optionally stub lessons."
    )
    parser.add_argument(
        "--rewrite-lesson-stubs",
        action="store_true",
        help=(
            "DANGEROUS: overwrite docs/lessons/NN-*.md with thin stubs. "
            "Enterprise tutorials are hand-authored — do not use unless you intend to replace them."
        ),
    )
    args = parser.parse_args()

    people = generate_lab_data()
    print(f"Generated {len(people)} workers → {LAB}")

    if args.rewrite_lesson_stubs:
        lessons = write_lessons()
        print(f"WARNING: overwrote {len(lessons)} lesson stubs → {LESSONS}")
    else:
        print("Skipped lesson markdown (enterprise tutorials preserved).")
        print("Lab-data only. Pass --rewrite-lesson-stubs to regenerate thin stubs.")


if __name__ == "__main__":
    main()
