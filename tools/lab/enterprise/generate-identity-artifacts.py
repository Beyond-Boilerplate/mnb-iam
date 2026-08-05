#!/usr/bin/env python3
"""Generate Enterprise Lab artifacts from identity-master.json.

Outputs:
  lab-data/enterprise/generated/openldap-people.ldif
  lab-data/enterprise/generated/samba-users.csv
  lab-data/enterprise/generated/hcm-workers.json
  lab-data/enterprise/generated/keycloak-users.json
  lab-data/enterprise/generated/crm-scim-users.json
  lab-data/connectors/hcm/workers.json  (served by connector-mock)
  lab-data/connectors/crm/Users.json
  lab-data/connectors/itsm/tickets.json (stub catalog)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MASTER = ROOT / "lab-data" / "enterprise" / "identity-master.json"
OUT = ROOT / "lab-data" / "enterprise" / "generated"
HCM = ROOT / "lab-data" / "connectors" / "hcm"
CRM = ROOT / "lab-data" / "connectors" / "crm"
ITSM = ROOT / "lab-data" / "connectors" / "itsm"


def load_master() -> dict:
    return json.loads(MASTER.read_text(encoding="utf-8"))


def write_openldap_ldif(idents: list[dict], password: str) -> None:
    lines = [
        "# Generated from identity-master.json — merge/reference for OpenLDAP seed",
        "# Primary seed remains lab-data/connectors/ldap/mnb-openldap.ldif",
        "",
    ]
    for i in idents:
        if i.get("status") == "terminated":
            continue
        uid = i["username"]
        lines += [
            f"dn: uid={uid},ou=people,dc=meridiannb,dc=com",
            "objectClass: inetOrgPerson",
            "objectClass: organizationalPerson",
            "objectClass: person",
            "objectClass: top",
            f"uid: {uid}",
            f"cn: {i['firstName']} {i['lastName']}",
            f"sn: {i['lastName']}",
            f"givenName: {i['firstName']}",
            f"mail: {i['email']}",
            f"employeeNumber: {i['userId']}",
            f"title: {i.get('title') or 'Associate'}",
            f"userPassword: {i.get('password') or password}",
            "",
        ]
    path = OUT / "openldap-people.ldif"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def write_samba_csv(idents: list[dict], password: str) -> None:
    path = OUT / "samba-users.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "sAMAccountName",
                "givenName",
                "sn",
                "mail",
                "employeeNumber",
                "department",
                "title",
                "userAccountControl",
                "password",
            ],
        )
        w.writeheader()
        for i in idents:
            uac = "514" if i.get("status") == "terminated" else "512"
            w.writerow(
                {
                    "sAMAccountName": i["username"],
                    "givenName": i["firstName"],
                    "sn": i["lastName"],
                    "mail": i["email"],
                    "employeeNumber": i["userId"],
                    "department": i.get("department") or "",
                    "title": i.get("title") or "",
                    "userAccountControl": uac,
                    "password": i.get("password") or password,
                }
            )
    print(f"wrote {path.relative_to(ROOT)}")


def write_hcm(idents: list[dict]) -> None:
    workers = []
    for i in idents:
        workers.append(
            {
                "id": i["userId"],
                "workerId": i["userId"],
                "userName": i["username"],
                "firstName": i["firstName"],
                "lastName": i["lastName"],
                "email": i["email"],
                "department": i.get("department"),
                "title": i.get("title"),
                "managerId": i.get("managerUserId"),
                "employeeType": i.get("employeeType") or "Employee",
                "active": i.get("status") != "terminated",
                "hireDate": i.get("hireDate"),
                "status": "Terminated" if i.get("status") == "terminated" else "Active",
            }
        )
    payload = {"schemas": ["urn:meridian:hcm:workers"], "total": len(workers), "workers": workers}
    OUT.mkdir(parents=True, exist_ok=True)
    HCM.mkdir(parents=True, exist_ok=True)
    (OUT / "hcm-workers.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (HCM / "workers.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote lab-data/connectors/hcm/workers.json ({len(workers)} workers)")


def write_crm_scim(idents: list[dict]) -> None:
    resources = []
    for i in idents:
        if i.get("status") == "terminated":
            continue
        resources.append(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": f"crm-{i['userId']}",
                "userName": i["username"],
                "name": {"givenName": i["firstName"], "familyName": i["lastName"]},
                "emails": [{"value": i["email"], "primary": True}],
                "active": True,
                "externalId": i["userId"],
                "groups": [{"display": "CRM-Users"}],
            }
        )
    payload = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "Resources": resources,
    }
    CRM.mkdir(parents=True, exist_ok=True)
    (OUT / "crm-scim-users.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (CRM / "Users.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote lab-data/connectors/crm/Users.json ({len(resources)} users)")


def write_itsm_stub() -> None:
    ITSM.mkdir(parents=True, exist_ok=True)
    payload = {
        "catalog": [
            {"id": "REQ-LAPTOP", "name": "Laptop Access", "fulfillment": "manual"},
            {"id": "REQ-VPN", "name": "VPN Access", "fulfillment": "group"},
            {"id": "REQ-WIRE", "name": "Wire Portal Entitlement", "fulfillment": "iiq"},
        ],
        "tickets": [],
    }
    (ITSM / "tickets.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("wrote lab-data/connectors/itsm/tickets.json")


def write_keycloak_users(idents: list[dict], password: str) -> None:
    users = []
    for i in idents:
        if i.get("status") == "terminated":
            continue
        users.append(
            {
                "username": i["username"],
                "email": i["email"],
                "firstName": i["firstName"],
                "lastName": i["lastName"],
                "enabled": True,
                "emailVerified": True,
                "credentials": [{"type": "password", "value": i.get("password") or password, "temporary": False}],
                "attributes": {"employeeId": [i["userId"]]},
                "groups": list(i.get("groups") or ["mnb-employees"]) + ["portal-users"],
            }
        )
    path = OUT / "keycloak-users.json"
    path.write_text(json.dumps({"users": users}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> int:
    if not MASTER.exists():
        print(f"missing {MASTER}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    master = load_master()
    idents = master.get("identities") or []
    password = master.get("defaultPassword") or "LabUser1!"
    write_openldap_ldif(idents, password)
    write_samba_csv(idents, password)
    write_hcm(idents)
    write_crm_scim(idents)
    write_itsm_stub()
    write_keycloak_users(idents, password)
    print(f"ok — {len(idents)} identities from {MASTER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
