#!/usr/bin/env python3
"""Clean lab Meridian objects, re-onboard MNB-HR + MNB-IT-Access, mark requestables, full lifecycle.

Usage (IIQ up, MCP on :8766, plugin ≥1.3.3):
  cd tools/iiq-mcp && PYTHONPATH=src .venv/bin/python scripts/smoke_lifecycle.py
"""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

MCP = "http://127.0.0.1:8766/mcp"
RESULTS: list[dict[str, Any]] = []

HR_FILE = "/opt/iiq-lab-data/hr/MNB-HR-Employees.csv"
IT_FILE = "/opt/iiq-lab-data/apps/MNB-IT-Access.csv"
HOST_HR = Path("/Users/alishaghatane/Documents/Sailpoint/lab-data/hr/MNB-HR-Employees.csv")
HOST_IT = Path("/Users/alishaghatane/Documents/Sailpoint/lab-data/apps/MNB-IT-Access.csv")
REQUESTABLE_IT = ["CRM", "DWRP", "SOX_VIEW", "ELDAP", "ACH_OPS"]


class Mcp:
    def __init__(self) -> None:
        self.sid: str | None = None
        self._id = 0

    def _req(self, payload: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
        data = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.sid:
            headers["mcp-session-id"] = self.sid
        req = urllib.request.Request(MCP, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=180) as resp:
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            body = resp.read().decode()
        msg: dict[str, Any] = {}
        for line in body.splitlines():
            if line.startswith("data: "):
                msg = json.loads(line[6:])
                break
        return hdrs, msg

    def init(self) -> None:
        hdrs, _ = self._req(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "smoke_lifecycle", "version": "1.0"},
                },
            }
        )
        self.sid = hdrs.get("mcp-session-id")
        self._req({"jsonrpc": "2.0", "method": "notifications/initialized"})
        assert self.sid

    def call(
        self, name: str, arguments: dict[str, Any] | None = None, *, allow_fail: bool = False
    ) -> dict[str, Any]:
        self._id += 1
        t0 = time.time()
        try:
            _, msg = self._req(
                {
                    "jsonrpc": "2.0",
                    "id": self._id,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments or {}},
                }
            )
        except Exception as exc:  # noqa: BLE001
            row = {
                "tool": name,
                "ok": False,
                "error": {"exception": str(exc)},
                "ms": int((time.time() - t0) * 1000),
            }
            RESULTS.append(row)
            print(f"FAIL {name}: {exc}", flush=True)
            if allow_fail:
                return row
            raise
        res = msg.get("result") or {}
        text = ((res.get("content") or [{}])[0].get("text")) or ""
        try:
            parsed: Any = json.loads(text) if text else {}
        except json.JSONDecodeError:
            parsed = {"_text": text[:800]}
        ok = not res.get("isError") and not (
            isinstance(parsed, dict) and parsed.get("ok") is False
        )
        err = None if ok else (parsed.get("error") if isinstance(parsed, dict) else parsed)
        data = (
            parsed.get("data")
            if isinstance(parsed, dict) and "data" in parsed
            else parsed
        )
        row = {
            "tool": name,
            "ok": ok,
            "ms": int((time.time() - t0) * 1000),
            "args": arguments or {},
            "error": err,
            "data": data if ok else None,
            "allowed_fail": allow_fail,
        }
        RESULTS.append(row)
        print(
            ("OK  " if ok else "FAIL")
            + f" {name} ({row['ms']}ms)"
            + (f" {json.dumps(err, default=str)[:160]}" if not ok else ""),
            flush=True,
        )
        if not ok and not allow_fail:
            raise RuntimeError(f"{name} failed: {err}")
        return row


def unwrap(row: dict[str, Any]) -> Any:
    return row.get("data")


def poll_task(c: Mcp, task_result_id: str, *, timeout_s: int = 180) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = c.call(
            "get_task_result",
            {"task_result_id": task_result_id, "raw": True},
            allow_fail=True,
        )
        data = unwrap(last) or {}
        if isinstance(data, dict) and data.get("completionStatus"):
            return data
        time.sleep(2)
    raise TimeoutError(f"TaskResult {task_result_id} not complete: {last}")


def delete_if_exists(c: Mcp, class_name: str, name: str) -> None:
    c.call(
        "delete_sailpoint_object",
        {
            "class_name": class_name,
            "name": name,
            "justification": "smoke_lifecycle cleanup",
        },
        allow_fail=True,
    )


def main() -> int:
    c = Mcp()
    c.init()

    print("\n=== 0. Bootstrap plugin settings ===", flush=True)
    c.call(
        "update_plugin_settings",
        {
            "plugin_name": "mnb_iam_toolkit",
            "settings": {
                "agentApiEnabled": "true",
                "taskRunEnabled": "true",
                "mutateGovernanceEnabled": "true",
                "passwordResetEnabled": "true",
                "advancedOpsEnabled": "true",
                "allowedTaskNames": (
                    "Account Aggregation*,Refresh Identity Cube*,Refresh*,"
                    "Aggregate *,Identity Refresh*"
                ),
            },
            "justification": "smoke bootstrap",
        },
        allow_fail=True,
    )
    ping = unwrap(c.call("toolkit_ping")) or {}
    print("ping", json.dumps(ping, default=str)[:500], flush=True)

    print("\n=== 1. Aggressive cleanup ===", flush=True)
    delete_if_exists(c, "GroupDefinition", "MNB-Active-Employees-Lab")
    for role in ("MNB-Requestable-CRM", "MNB-IT-Birthright"):
        delete_if_exists(c, "Bundle", role)

    idents = unwrap(c.call("search_identities", {"count": 100}, allow_fail=True)) or {}
    for it in idents.get("items") or []:
        un = (it or {}).get("userName") or ""
        if un in {"spadmin"} or not un:
            continue
        delete_if_exists(c, "Identity", un)

    for app in (
        "MNB-HR",
        "MNB-IT-Access",
        "MNB-CustomAPI-Wizard-Demo",
        "MNB-CSV-Wizard-Smoke",
        "CSV Import Application",
        "CSV Comma Delimited User Import",
        "HR",
        "del",
    ):
        delete_if_exists(c, "Application", app)

    print("\n=== 2. Onboard MNB-HR (authoritative) ===", flush=True)
    cols = next(csv.reader(HOST_HR.open()))
    attr_xml = "\n".join(
        f'      <AttributeDefinition name="{col}" type="string"/>' for col in cols
    )
    c.call(
        "create_application",
        {
            "name": "MNB-HR",
            "type": "DelimitedFile",
            "description": "Meridian authoritative HR",
            "owner": "spadmin",
            "overwrite": True,
            "authoritative": True,
            "justification": "smoke re-onboard HR",
            "attributes": {
                "file": HR_FILE,
                "delimiter": ",",
                "hasHeader": True,
                "filetransport": "local",
                "parseType": "delimited",
                "filterEmptyRecords": True,
                "_schemaIdentityAttribute": "userId",
                "_schemaDisplayAttribute": "name",
            },
        },
    )
    hr_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Application PUBLIC "sailpoint.dtd" "sailpoint.dtd">
<Application authoritative="true" connector="sailpoint.connector.DelimitedFileConnector"
  featuresString="DIRECT_PERMISSIONS, NO_RANDOM_ACCESS, DISCOVER_SCHEMA" name="MNB-HR" type="DelimitedFile">
  <Attributes>
    <Map>
      <entry key="file" value="{HR_FILE}"/>
      <entry key="filetransport" value="local"/>
      <entry key="parseType" value="delimited"/>
      <entry key="delimiter" value=","/>
      <entry key="hasHeader"><value><Boolean>true</Boolean></value></entry>
      <entry key="filterEmptyRecords"><value><Boolean>true</Boolean></value></entry>
      <entry key="templateApplication" value="DelimitedFile Template"/>
    </Map>
  </Attributes>
  <Owner><Reference class="sailpoint.object.Identity" name="spadmin"/></Owner>
  <Schemas>
    <Schema displayAttribute="name" identityAttribute="userId" nativeObjectType="account" objectType="account">
{attr_xml}
    </Schema>
  </Schemas>
</Application>
"""
    c.call(
        "import_sailpoint_object",
        {"xml": hr_xml, "scrub_ids": True, "justification": "HR schema"},
    )
    c.call("test_application_connection", {"application": "MNB-HR"})
    agg = unwrap(
        c.call(
            "trigger_aggregation",
            {
                "app_id": "MNB-HR",
                "full_or_delta": "full",
                "justification": "HR aggregate",
            },
        )
    )
    tr = ((agg or {}).get("response") or {}).get("taskResultId")
    assert tr, agg
    hr_result = poll_task(c, tr)
    print(
        "HR agg",
        hr_result.get("completionStatus"),
        hr_result.get("attributes"),
        flush=True,
    )

    print("\n=== 3. Onboard MNB-IT-Access ===", flush=True)
    it_cols = next(csv.reader(HOST_IT.open()))
    it_attr = "\n".join(
        f'      <AttributeDefinition name="{col}" type="string"'
        + (' entitlement="true" managed="true"' if col == "itAccess" else "")
        + "/>"
        for col in it_cols
    )
    c.call(
        "create_application",
        {
            "name": "MNB-IT-Access",
            "type": "DelimitedFile",
            "description": "Meridian IT entitlement inventory (non-authoritative)",
            "owner": "spadmin",
            "overwrite": True,
            "authoritative": False,
            "justification": "smoke IT access",
            "attributes": {
                "file": IT_FILE,
                "delimiter": ",",
                "hasHeader": True,
                "filetransport": "local",
                "parseType": "delimited",
                "mergeRows": True,
                "indexColumn": "userName",
                "_schemaIdentityAttribute": "userName",
                "_schemaDisplayAttribute": "userName",
            },
        },
    )
    it_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Application PUBLIC "sailpoint.dtd" "sailpoint.dtd">
<Application authoritative="false" connector="sailpoint.connector.DelimitedFileConnector"
  featuresString="DIRECT_PERMISSIONS, NO_RANDOM_ACCESS, DISCOVER_SCHEMA" name="MNB-IT-Access" type="DelimitedFile">
  <Attributes>
    <Map>
      <entry key="file" value="{IT_FILE}"/>
      <entry key="filetransport" value="local"/>
      <entry key="parseType" value="delimited"/>
      <entry key="delimiter" value=","/>
      <entry key="hasHeader"><value><Boolean>true</Boolean></value></entry>
      <entry key="mergeRows"><value><Boolean>true</Boolean></value></entry>
      <entry key="indexColumn" value="userName"/>
      <entry key="templateApplication" value="DelimitedFile Template"/>
    </Map>
  </Attributes>
  <Owner><Reference class="sailpoint.object.Identity" name="spadmin"/></Owner>
  <Schemas>
    <Schema displayAttribute="userName" identityAttribute="userName" nativeObjectType="account"
      objectType="account" groupAttribute="itAccess">
{it_attr}
    </Schema>
  </Schemas>
</Application>
"""
    c.call(
        "import_sailpoint_object",
        {"xml": it_xml, "scrub_ids": True, "justification": "IT schema"},
    )
    c.call("test_application_connection", {"application": "MNB-IT-Access"})
    agg_it = unwrap(
        c.call(
            "trigger_aggregation",
            {
                "app_id": "MNB-IT-Access",
                "full_or_delta": "full",
                "justification": "IT aggregate",
            },
        )
    )
    tr_it = ((agg_it or {}).get("response") or {}).get("taskResultId")
    assert tr_it, agg_it
    it_result = poll_task(c, tr_it)
    print(
        "IT agg",
        it_result.get("completionStatus"),
        it_result.get("attributes"),
        flush=True,
    )

    print("\n=== 4. Refresh identities ===", flush=True)
    ref = unwrap(
        c.call(
            "run_task_now",
            {
                "task_name": "Refresh Identity Cube",
                "sync": False,
                "justification": "post agg refresh",
                "args": {
                    "promoteAttributes": "true",
                    "refreshManagerStatus": "true",
                    "refreshIdentityEntitlements": "true",
                },
            },
        )
    )
    tr_r = (ref or {}).get("taskResultId")
    assert tr_r, ref
    poll_task(c, tr_r)

    print("\n=== 5. Requestables + role ===", flush=True)
    c.call(
        "promote_entitlements",
        {
            "application": "MNB-IT-Access",
            "attribute": "itAccess",
            "justification": "promote IT managed attributes for LCM catalog",
        },
    )
    for code in REQUESTABLE_IT:
        c.call(
            "update_entitlement_metadata",
            {
                "app": "MNB-IT-Access",
                "attribute": "itAccess",
                "value": code,
                "patch": {
                    "requestable": True,
                    "displayName": f"MNB {code}",
                    "description": f"Meridian lab requestable {code}",
                },
                "justification": "enable LCM catalog",
            },
        )
    c.call(
        "create_role",
        {
            "definition": {
                "name": "MNB-Requestable-CRM",
                "displayName": "MNB Requestable CRM",
                "type": "business",
                "requestable": True,
                "owner": "spadmin",
                "description": "Lab business role for LCM access request smoke",
                "profiles": [
                    {
                        "application": "MNB-IT-Access",
                        "name": "CRM-access",
                        "attribute": "itAccess",
                        "value": "CRM",
                    }
                ],
            },
            "justification": "LCM requestable role with CRM profile",
        },
    )
    c.call(
        "attach_role_profile",
        {
            "role_name": "MNB-Requestable-CRM",
            "application": "MNB-IT-Access",
            "attribute": "itAccess",
            "value": "CRM",
            "replace": True,
            "justification": "ensure CRM profile attached",
        },
        allow_fail=True,
    )
    req_probe = unwrap(
        c.call("get_requestable_items", {"identity_id": "helen.ross", "count": 20})
    )
    print("requestables-pre", json.dumps(req_probe, default=str)[:500], flush=True)

    print("\n=== 6. Lifecycle ===", flush=True)
    search = unwrap(c.call("search_identities", {"query": "Helen", "count": 5})) or {}
    items = search.get("items") or []
    if not items:
        search = unwrap(c.call("search_identities", {"query": "MNB00001", "count": 5})) or {}
        items = search.get("items") or []
    if not items:
        search = unwrap(c.call("search_identities", {"query": "helen", "count": 5})) or {}
        items = search.get("items") or []
    assert items, "no identity after HR agg"
    ident = items[0]
    iid = ident.get("id")
    iname = ident.get("userName")
    print("identity", iname, iid, flush=True)

    c.call("get_identity_accounts", {"id": iid})
    c.call("list_applications", {"query": "MNB", "count": 20})
    c.call("get_application_health", {"app_id": "MNB-HR"})
    c.call("list_capabilities", {"limit": 50})
    caps_raw = unwrap(RESULTS[-1])
    cap_names: list[str] = []
    if isinstance(caps_raw, list):
        cap_names = [x.get("name") for x in caps_raw if isinstance(x, dict)]
    elif isinstance(caps_raw, dict):
        for x in caps_raw.get("items") or []:
            if isinstance(x, dict) and x.get("name"):
                cap_names.append(x["name"])

    c.call(
        "create_population",
        {
            "name": "MNB-Active-Employees-Lab",
            "filter": "inactive == false",
            "description": "Active identities",
            "justification": "lifecycle population",
        },
    )
    c.call("get_population_definition", {"pop_id": "MNB-Active-Employees-Lab"})
    c.call(
        "preview_population_membership",
        {"pop_id": "MNB-Active-Employees-Lab", "count": 10},
    )

    wgs = unwrap(c.call("list_workgroups", {"limit": 20})) or []
    if isinstance(wgs, list) and wgs:
        c.call(
            "manage_workgroup_members",
            {
                "workgroup": wgs[0].get("name"),
                "member": iname,
                "op": "add",
                "justification": "lifecycle WG",
            },
            allow_fail=True,
        )

    pick_cap = next(
        (n for n in cap_names if n and n not in {"SystemAdministrator"}),
        None,
    )
    if pick_cap:
        c.call(
            "assign_identity_capability",
            {
                "identity_name": iname,
                "capability": pick_cap,
                "op": "assign",
                "justification": "lifecycle",
            },
            allow_fail=True,
        )

    req = unwrap(c.call("get_requestable_items", {"identity_id": iname, "count": 20})) or {}
    print("requestables", json.dumps(req, default=str)[:600], flush=True)
    role_items = ((req.get("roles") or {}).get("items")) if isinstance(req, dict) else []
    ent_items = (
        ((req.get("entitlements") or {}).get("items")) if isinstance(req, dict) else []
    )
    ar_items: list[dict[str, Any]] = []
    if role_items:
        r0 = role_items[0]
        ar_items.append(
            {
                "type": "role",
                "id": r0.get("id"),
                "name": r0.get("name") or r0.get("displayName"),
            }
        )
    elif ent_items:
        e0 = ent_items[0]
        ar_items.append(
            {
                "type": "entitlement",
                "application": "MNB-IT-Access",
                "attribute": e0.get("attribute") or "itAccess",
                "value": e0.get("value") or e0.get("displayName"),
                "id": e0.get("id"),
            }
        )
    else:
        ar_items.append(
            {
                "type": "entitlement",
                "application": "MNB-IT-Access",
                "attribute": "itAccess",
                "value": "CRM",
            }
        )

    ar = c.call(
        "create_access_request",
        {
            "identity_id": iname,
            "items": ar_items,
            "justification": "smoke LCM access request after IT-Access requestables",
        },
        allow_fail=True,
    )
    print("AR", json.dumps(unwrap(ar) or ar.get("error"), default=str)[:500], flush=True)

    c.call("count_open_sod_violations")
    c.call("list_agent_work_items", {"limit": 20})
    c.call("search_audit_events", {"count": 10}, allow_fail=True)

    fails = [r for r in RESULTS if not r["ok"] and not r.get("allowed_fail")]
    oks = [r for r in RESULTS if r["ok"]]
    soft = [r for r in RESULTS if not r["ok"] and r.get("allowed_fail")]
    path = "/tmp/mcp-lifecycle-clean.json"
    json.dump(
        {
            "ok": len(oks),
            "fail": len(fails),
            "soft_fail": len(soft),
            "total": len(RESULTS),
            "identity": iname,
            "results": RESULTS,
        },
        open(path, "w"),
        indent=2,
        default=str,
    )
    print(
        f"\nSUMMARY ok={len(oks)} fail={len(fails)} soft={len(soft)} total={len(RESULTS)} → {path}",
        flush=True,
    )
    for f in fails:
        print(
            f" - {f['tool']}: {json.dumps(f.get('error'), default=str)[:200]}",
            flush=True,
        )
    critical = {
        "create_application",
        "trigger_aggregation",
        "run_task_now",
        "search_identities",
        "get_identity_accounts",
    }
    crit_fail = [f for f in fails if f["tool"] in critical]
    return 1 if crit_fail else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("FATAL", exc, file=sys.stderr)
        json.dump(
            {"results": RESULTS, "fatal": str(exc)},
            open("/tmp/mcp-lifecycle-clean.json", "w"),
            indent=2,
            default=str,
        )
        raise SystemExit(2)
