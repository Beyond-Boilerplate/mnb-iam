#!/usr/bin/env python3
"""Meridian lesson verifier — pass/fail + gap report against a live IIQ lab.

Prefers IIQ HTTP APIs (SCIM Users, OOTB REST probes). Falls back to iiq console
for object.exists / identity checks when REST/SCIM cannot answer.

Usage:
  ./tools/iiq-verify/verify-lesson.sh 04
  python3 tools/iiq-verify/verify_lesson.py --lesson 04 --base-url http://localhost:8080/identityiq

Env:
  IIQ_BASE_URL   default http://localhost:8080/identityiq
  IIQ_USER       default spadmin
  IIQ_PASSWORD   default admin
  IIQ_HOME       for console fallback (Tomcat lab)
  IIQ_VERIFY_MODE  local | docker | k8s | auto
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPECS = Path(__file__).resolve().parent / "lesson-specs"
REPORT_DIR = Path.home() / "iiq-lab-evidence" / "verify"


class IIQClient:
    def __init__(self, base_url: str, user: str, password: str, mode: str) -> None:
        self.base = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.mode = mode
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self._auth = f"Basic {token}"
        self.transport_notes: list[str] = []

    def http(self, method: str, path: str, accept: str = "application/json") -> tuple[int, str]:
        url = path if path.startswith("http") else f"{self.base}{path}"
        req = urllib.request.Request(
            url,
            method=method,
            headers={
                "Authorization": self._auth,
                "Accept": accept,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return e.code, body
        except Exception as e:  # noqa: BLE001
            return 0, str(e)

    def http_ok(self, path: str) -> tuple[bool, str]:
        # login.jsf often needs no auth
        url = f"{self.base}{path}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return 200 <= resp.status < 400, f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            return 200 <= e.code < 400, f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001
            return False, str(e)

    def scim_user(self, name: str) -> dict[str, Any] | None:
        q = urllib.parse.quote(f'userName eq "{name}"')
        code, body = self.http("GET", f"/scim/v2/Users?filter={q}")
        if code == 200:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return None
            resources = data.get("Resources") or data.get("resources") or []
            if resources:
                self.transport_notes.append("scim")
                return resources[0]
        return None

    def rest_identity_probe(self, name: str) -> dict[str, Any] | None:
        # Probe a few common OOTB / plugin shapes; tolerate absence.
        for path in (
            f"/rest/identities/{urllib.parse.quote(name)}",
            f"/rest/identity/{urllib.parse.quote(name)}",
        ):
            code, body = self.http("GET", path)
            if code == 200 and body.strip().startswith(("{", "[")):
                try:
                    self.transport_notes.append("rest")
                    return json.loads(body)
                except json.JSONDecodeError:
                    continue
        return None

    def console(self, command: str) -> str:
        if self.mode == "docker":
            return self._console_docker(command)
        if self.mode == "k8s":
            return self._console_k8s(command)
        return self._console_local(command)

    def _console_local(self, command: str) -> str:
        iiq_home = os.environ.get("IIQ_HOME", str(Path.home() / "iiq-lab/tomcat/webapps/identityiq"))
        bin_dir = Path(iiq_home) / "WEB-INF" / "bin"
        iiq = bin_dir / "iiq"
        if not iiq.exists():
            return f"ERROR: iiq console not found under {iiq_home}"
        self.transport_notes.append("console-local")
        proc = subprocess.run(
            ["./iiq", "console", "iiqBeans", "-c", command],
            cwd=str(bin_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return (proc.stdout or "") + (proc.stderr or "")

    def _console_docker(self, command: str) -> str:
        self.transport_notes.append("console-docker")
        safe = command.replace('"', '\\"')
        container = os.environ.get("IIQ_DOCKER_CONTAINER", "").strip()
        if container:
            # Preferred in Compose academy sidecar (docker.sock + named container)
            shell = (
                'cd "$IIQ_HOME/WEB-INF/bin" 2>/dev/null || '
                "cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin; "
                f'./iiq console iiqBeans -c "{safe}"'
            )
            proc = subprocess.run(
                ["docker", "exec", "-T", container, "sh", "-c", shell],
                capture_output=True,
                text=True,
                timeout=180,
            )
            return (proc.stdout or "") + (proc.stderr or "")
        proc = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(ROOT / "docker-compose.iiq.yml"),
                "exec",
                "-T",
                "identityiq",
                "sh",
                "-c",
                f'cd "$IIQ_HOME/WEB-INF/bin" && ./iiq console iiqBeans -c "{safe}"',
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        return (proc.stdout or "") + (proc.stderr or "")
    def _console_k8s(self, command: str) -> str:
        self.transport_notes.append("console-k8s")
        ns = os.environ.get("NAMESPACE", "sailpoint")
        deploy = os.environ.get("IIQ_DEPLOYMENT", "identityiq")
        safe = command.replace('"', '\\"')
        pod = subprocess.check_output(
            [
                "kubectl",
                "-n",
                ns,
                "get",
                "pod",
                "-l",
                f"app.kubernetes.io/name={deploy}",
                "-o",
                "jsonpath={.items[0].metadata.name}",
            ],
            text=True,
        ).strip()
        proc = subprocess.run(
            [
                "kubectl",
                "-n",
                ns,
                "exec",
                pod,
                "-c",
                "identityiq",
                "--",
                "sh",
                "-c",
                f'cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin && ./iiq console iiqBeans -c "{safe}"',
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        return (proc.stdout or "") + (proc.stderr or "")

    def object_exists(self, clazz: str, name: str) -> tuple[bool, str]:
        out = self.console(f'get {clazz} "{name}"')
        low = out.lower()
        if "unknown object" in low or "no object" in low or "not found" in low or out.strip().startswith("ERROR:"):
            return False, out.strip()[:400]
        if f'name="{name}"' in out or f"name='{name}'" in out or clazz in out:
            return True, "found via console"
        # empty-ish
        if len(out.strip()) < 20:
            return False, out.strip()[:400]
        return True, "console returned payload"

    def identity_xml(self, name: str) -> str:
        # Prefer SCIM/REST then console
        scim = self.scim_user(name)
        if scim:
            return json.dumps(scim)
        rest = self.rest_identity_probe(name)
        if rest:
            return json.dumps(rest)
        return self.console(f'get Identity "{name}"')

    def identity_exists(self, name: str) -> tuple[bool, str]:
        scim = self.scim_user(name)
        if scim:
            return True, "found via SCIM"
        rest = self.rest_identity_probe(name)
        if rest:
            return True, "found via REST"
        out = self.console(f'get Identity "{name}"')
        low = out.lower()
        if "unknown object" in low or "no object" in low or "not found" in low:
            return False, out.strip()[:300]
        if f'name="{name}"' in out or "<Identity" in out:
            return True, "found via console"
        return False, out.strip()[:300]

    def identity_count(self) -> tuple[int | None, str]:
        out = self.console("count Identity")
        m = re.search(r"(\d+)", out)
        if m:
            return int(m.group(1)), "console count Identity"
        return None, out.strip()[:200]

    def identity_attr(self, name: str, attr: str) -> tuple[str | None, str]:
        payload = self.identity_xml(name)
        # JSON SCIM
        try:
            data = json.loads(payload)
            # SCIM emails / name
            if attr == "email":
                emails = data.get("emails") or []
                if emails and isinstance(emails, list):
                    val = emails[0].get("value") if isinstance(emails[0], dict) else str(emails[0])
                    return val, "scim/rest"
            if attr in ("firstname", "firstName"):
                name_obj = data.get("name") or {}
                if isinstance(name_obj, dict) and name_obj.get("givenName"):
                    return str(name_obj["givenName"]), "scim/rest"
            if attr in data and data[attr] is not None:
                return str(data[attr]), "scim/rest"
            attrs = data.get("attributes") or data.get("Attributes") or {}
            if isinstance(attrs, dict) and attr in attrs:
                return str(attrs[attr]), "scim/rest"
        except json.JSONDecodeError:
            pass
        # XML Identity attributes map
        pat = rf'<entry key="{re.escape(attr)}" value="([^"]*)"'
        m = re.search(pat, payload)
        if m:
            return m.group(1), "console-xml"
        # also try without value quoting variants
        return None, "attribute not found on Identity (Link-only? run Lesson 05 maps + Refresh MNB Attributes)"


def resolve_spec(lesson: str) -> Path:
    lesson = lesson.strip()
    # numeric or stem
    candidates = list(SPECS.glob(f"{lesson}-*.json"))
    if not candidates:
        candidates = list(SPECS.glob(f"{int(lesson):02d}-*.json")) if lesson.isdigit() else []
    if not candidates:
        # exact stem
        p = SPECS / f"{lesson}.json"
        if p.exists():
            return p
        raise SystemExit(f"No lesson spec for '{lesson}' under {SPECS}")
    return sorted(candidates)[0]


def detect_mode() -> str:
    env = os.environ.get("IIQ_VERIFY_MODE", "auto").lower()
    if env != "auto":
        return env
    # Prefer docker if compose project running
    try:
        out = subprocess.run(
            ["docker", "compose", "-f", str(ROOT / "docker-compose.iiq.yml"), "ps", "-q", "identityiq"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        if out.returncode == 0 and out.stdout.strip():
            return "docker"
    except Exception:  # noqa: BLE001
        pass
    iiq_home = Path(os.environ.get("IIQ_HOME", str(Path.home() / "iiq-lab/tomcat/webapps/identityiq")))
    if (iiq_home / "WEB-INF/bin/iiq").exists():
        return "local"
    return "local"


def run_check(client: IIQClient, check: dict[str, Any]) -> dict[str, Any]:
    cid = check.get("id", "check")
    ctype = check["type"]
    msg = check.get("message", cid)
    result: dict[str, Any] = {
        "id": cid,
        "type": ctype,
        "message": msg,
        "status": "FAIL",
        "detail": "",
        "hint": check.get("softFailHint") or check.get("hint") or "",
    }

    try:
        if ctype == "http.ok":
            ok, detail = client.http_ok(check.get("path", "/login.jsf"))
            result["status"] = "PASS" if ok else "FAIL"
            result["detail"] = detail
        elif ctype == "host.file.exists":
            rel = check["path"]
            path = ROOT / rel if not Path(rel).is_absolute() else Path(rel)
            home = Path.home() / "iiq-lab-data" / Path(rel).name
            ok = path.exists() or home.exists()
            result["status"] = "PASS" if ok else "FAIL"
            result["detail"] = str(path if path.exists() else home)
        elif ctype == "object.exists":
            classes = [check["objectClass"]] + list(check.get("alternateClasses") or [])
            ok = False
            detail = ""
            for clazz in classes:
                ok, detail = client.object_exists(clazz, check["name"])
                if ok:
                    break
            result["status"] = "PASS" if ok else "FAIL"
            result["detail"] = detail
        elif ctype == "object.absent":
            ok, detail = client.object_exists(check["objectClass"], check["name"])
            # absent expected
            if not ok:
                result["status"] = "PASS"
                result["detail"] = "absent as expected"
            else:
                soft = check.get("severity")
                result["status"] = "WARN" if soft else "FAIL"
                result["detail"] = f"object unexpectedly present ({detail})"
                if soft:
                    result["hint"] = result["hint"] or "OK if leftover lab; wipe or delete before Lesson 04."
        elif ctype == "identity.exists":
            ok, detail = client.identity_exists(check["name"])
            result["status"] = "PASS" if ok else "FAIL"
            result["detail"] = detail
            if not ok:
                result["hint"] = result["hint"] or "Run Aggregate MNB-HR (Lesson 04) then re-verify."
        elif ctype == "identity.countMin":
            n, detail = client.identity_count()
            need = int(check["min"])
            if n is None:
                result["status"] = "FAIL"
                result["detail"] = detail
            else:
                result["status"] = "PASS" if n >= need else "FAIL"
                result["detail"] = f"count={n} (need >={need}); {detail}"
        elif ctype == "identity.attr":
            name = check["name"]
            attr = check["attr"]
            val, how = client.identity_attr(name, attr)
            if val is None:
                result["status"] = "FAIL"
                result["detail"] = how
                result["hint"] = (
                    result["hint"]
                    or "Promote Link→Identity maps (Lesson 05) and run Refresh MNB Attributes."
                )
            else:
                ok = True
                if "contains" in check:
                    ok = check["contains"] in val
                if "equals" in check:
                    ok = val == check["equals"]
                if "equalsIgnoreCase" in check:
                    ok = val.lower() == str(check["equalsIgnoreCase"]).lower()
                result["status"] = "PASS" if ok else "FAIL"
                result["detail"] = f"{attr}={val!r} via {how}"
        else:
            result["status"] = "FAIL"
            result["detail"] = f"unknown check type {ctype}"
    except Exception as e:  # noqa: BLE001
        result["status"] = "FAIL"
        result["detail"] = f"exception: {e}"

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify a Meridian academy lesson against live IIQ")
    ap.add_argument("--lesson", "-l", required=True, help="Lesson number or stem (e.g. 04 or 04-authoritative-hr-source)")
    ap.add_argument("--base-url", default=os.environ.get("IIQ_BASE_URL", "http://localhost:8080/identityiq"))
    ap.add_argument("--user", default=os.environ.get("IIQ_USER", "spadmin"))
    ap.add_argument("--password", default=os.environ.get("IIQ_PASSWORD", "admin"))
    ap.add_argument("--mode", default=None, help="local|docker|k8s|auto")
    ap.add_argument("--json-out", default=None, help="Write report JSON path")
    args = ap.parse_args()

    spec_path = resolve_spec(args.lesson)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    mode = args.mode or detect_mode()
    client = IIQClient(args.base_url, args.user, args.password, mode)

    results = [run_check(client, c) for c in spec.get("checks", [])]
    fails = [r for r in results if r["status"] == "FAIL"]
    warns = [r for r in results if r["status"] == "WARN"]
    verdict = "PASS" if not fails else "FAIL"

    report = {
        "schema": "mnb-lesson-verify-report/v1",
        "lesson": spec.get("lesson"),
        "stem": spec.get("stem"),
        "title": spec.get("title"),
        "verdict": verdict,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "target": {"baseUrl": args.base_url, "mode": mode, "user": args.user},
        "transport": sorted(set(client.transport_notes)),
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "PASS"),
            "failed": len(fails),
            "warned": len(warns),
        },
        "gaps": [
            {
                "id": r["id"],
                "message": r["message"],
                "detail": r["detail"],
                "hint": r.get("hint") or "",
            }
            for r in fails
        ],
        "checks": results,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.json_out) if args.json_out else REPORT_DIR / f"lesson-{spec.get('lesson')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Human report
    print(f"Lesson {spec.get('lesson')} — {spec.get('title')}")
    print(f"Target: {args.base_url}  mode={mode}")
    print(f"Verdict: {verdict}")
    print("-" * 60)
    for r in results:
        mark = {"PASS": "✓", "FAIL": "✗", "WARN": "!"}.get(r["status"], "?")
        print(f"  [{mark}] {r['status']:4}  {r['message']}")
        if r["status"] != "PASS":
            print(f"         detail: {r['detail']}")
            if r.get("hint"):
                print(f"         hint:   {r['hint']}")
    print("-" * 60)
    if fails:
        print("Gaps to fix:")
        for g in report["gaps"]:
            print(f"  - {g['id']}: {g['message']} — {g['detail']}")
    print(f"Report: {out_path}")
    print("Paste this JSON into the learn site Verify panel to track progress.")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
