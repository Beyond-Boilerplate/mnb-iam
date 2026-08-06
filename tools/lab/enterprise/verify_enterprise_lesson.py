#!/usr/bin/env python3
"""Enterprise Sandbox lesson asserts — print every check as PASS/FAIL with assert text.

Usage:
  ./tools/lab/enterprise/verify-lesson.sh 203
  ./tools/lab/enterprise/verify-lesson.sh 201 202 203
  ./tools/lab/enterprise/verify-lesson.sh --all

Sources (in order): MCP tools, plugin REST, host HTTP, docker iiq console fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[3]
SPECS_DIR = Path(__file__).resolve().parent / "lesson-asserts"
CHAT = REPO / "tools" / "iiq-chat"
sys.path.insert(0, str(CHAT))

try:
    from mcp_client import McpClient, McpError  # noqa: E402
except ImportError:  # pragma: no cover
    McpClient = None  # type: ignore
    McpError = Exception  # type: ignore


@dataclass
class CheckResult:
    lesson: str
    check_id: str
    assert_text: str
    ok: bool
    detail: str = ""
    soft: bool = False


@dataclass
class Ctx:
    mcp: Any = None
    iiq_base: str = "http://127.0.0.1:8080/identityiq"
    iiq_user: str = "spadmin"
    iiq_pass: str = "admin"
    mcp_url: str = "http://127.0.0.1:8766/mcp"
    mcp_key: str = "mnb-lab-mcp-key"
    container: str = "mnb-identityiq"
    _sys_cfg: dict[str, Any] | None = field(default=None, repr=False)
    _apps: set[str] | None = field(default=None, repr=False)


JSON_MODE = False


def _log(msg: str) -> None:
    # In --json mode, keep stdout reserved for the single JSON payload;
    # progress/notes still go to stderr so `--json` stays pipeable.
    print(msg, file=sys.stderr if JSON_MODE else sys.stdout, flush=True)


def http_json(url: str, *, auth: tuple[str, str] | None = None, timeout: float = 15.0) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    if auth:
        import base64

        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def http_ok(url: str, timeout: float = 8.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


def ensure_mcp(ctx: Ctx) -> bool:
    if ctx.mcp is not None:
        return True
    if McpClient is None:
        return False
    try:
        client = McpClient(url=ctx.mcp_url, api_key=ctx.mcp_key, timeout=90.0)
        client.init()
        ctx.mcp = client
        return True
    except Exception as exc:  # noqa: BLE001
        _log(f"  note: MCP unavailable ({exc})")
        return False


def load_system_config(ctx: Ctx) -> dict[str, Any]:
    if ctx._sys_cfg is not None:
        return ctx._sys_cfg

    attrs: dict[str, Any] = {}

    # 1) Plugin REST (full attributes, host/port not secrets)
    try:
        url = f"{ctx.iiq_base.rstrip('/')}/plugin/rest/mnbToolkit/agent/system/config"
        data = http_json(url, auth=(ctx.iiq_user, ctx.iiq_pass))
        payload = data.get("data") if isinstance(data, dict) else None
        if isinstance(payload, dict) and isinstance(payload.get("attributes"), dict):
            attrs = dict(payload["attributes"])
    except Exception:
        pass

    # 2) MCP export Configuration XML
    if not attrs and ensure_mcp(ctx):
        try:
            result = ctx.mcp.call(
                "export_sailpoint_object",
                {"class_name": "Configuration", "name": "SystemConfiguration"},
            )
            data = result.get("data") if isinstance(result, dict) else {}
            xml = (data or {}).get("xml") if isinstance(data, dict) else None
            if isinstance(xml, str) and xml:
                for m in re.finditer(
                    r'<entry key="([^"]+)"(?:\s+value="([^"]*)")?\s*/>',
                    xml,
                ):
                    attrs[m.group(1)] = m.group(2) if m.group(2) is not None else ""
                for m in re.finditer(
                    r'<entry key="([^"]+)">\s*<value>\s*<String>([^<]*)</String>',
                    xml,
                ):
                    attrs[m.group(1)] = m.group(2)
        except Exception as exc:  # noqa: BLE001
            _log(f"  note: MCP export SystemConfiguration failed ({exc})")

    # 3) docker iiq console fallback
    if not attrs:
        script = r"""
import sailpoint.object.Configuration;
Configuration cfg = context.getObjectByName(Configuration.class, "SystemConfiguration");
if (cfg == null) return "MISSING";
StringBuilder sb = new StringBuilder();
String[] keys = new String[] {
  "defaultEmailHost","defaultEmailPort","defaultEmailFromAddress",
  "emailNotifierType","smtp_encryptionType"
};
for (int i = 0; i < keys.length; i++) {
  Object v = cfg.get(keys[i]);
  sb.append(keys[i]).append("=").append(v == null ? "" : String.valueOf(v)).append("\n");
}
return sb.toString();
"""
        rule_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Rule PUBLIC "sailpoint.dtd" "sailpoint.dtd">
<Rule language="beanshell" name="MNB-Rule-Assert-Email-Config">
  <Source><![CDATA[{script}]]></Source>
</Rule>
"""
        try:
            tmp = Path("/tmp/MNB-Rule-Assert-Email-Config.xml")
            tmp.write_text(rule_xml, encoding="utf-8")
            subprocess.run(
                ["docker", "cp", str(tmp), f"{ctx.container}:/tmp/MNB-Rule-Assert-Email-Config.xml"],
                check=True,
                capture_output=True,
            )
            proc = subprocess.run(
                [
                    "docker",
                    "exec",
                    ctx.container,
                    "sh",
                    "-c",
                    "cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin && "
                    "./iiq console iiqBeans <<'EOF'\n"
                    "import /tmp/MNB-Rule-Assert-Email-Config.xml\n"
                    "rule MNB-Rule-Assert-Email-Config\n"
                    "EOF",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            for line in out.splitlines():
                if "=" in line and any(
                    k in line
                    for k in (
                        "defaultEmailHost",
                        "defaultEmailPort",
                        "defaultEmailFromAddress",
                        "emailNotifierType",
                    )
                ):
                    k, _, v = line.partition("=")
                    attrs[k.strip().lstrip("> ").strip()] = v.strip()
        except Exception as exc:  # noqa: BLE001
            _log(f"  note: console SystemConfiguration fallback failed ({exc})")

    ctx._sys_cfg = attrs
    return attrs


def list_apps(ctx: Ctx) -> set[str]:
    if ctx._apps is not None:
        return ctx._apps
    names: set[str] = set()
    if ensure_mcp(ctx):
        try:
            result = ctx.mcp.call("list_applications", {"query": "MNB", "count": 200})
            data = result.get("data") if isinstance(result, dict) else {}
            items = (data or {}).get("items") or (data or {}).get("Resources") or []
            for item in items if isinstance(items, list) else []:
                if isinstance(item, dict) and item.get("name"):
                    names.add(str(item["name"]))
        except Exception as exc:  # noqa: BLE001
            _log(f"  note: list_applications failed ({exc})")
    ctx._apps = names
    return names


def identity_exists(ctx: Ctx, name: str) -> bool:
    if ensure_mcp(ctx):
        try:
            result = ctx.mcp.call("search_identities", {"query": name, "count": 5})
            data = result.get("data") if isinstance(result, dict) else {}
            items = (data or {}).get("items") or (data or {}).get("Resources") or []
            if isinstance(items, list) and items:
                return True
        except Exception:
            pass
    return False


def object_exists(ctx: Ctx, class_name: str, name: str) -> bool:
    if ensure_mcp(ctx):
        try:
            result = ctx.mcp.call(
                "export_sailpoint_object",
                {"class_name": class_name, "name": name},
            )
            if isinstance(result, dict) and result.get("ok") is False:
                return False
            data = result.get("data") if isinstance(result, dict) else {}
            xml = (data or {}).get("xml") if isinstance(data, dict) else None
            return isinstance(xml, str) and len(xml) > 20
        except Exception:
            return False
    return False


def mailpit_subjects(limit: int = 20) -> list[str]:
    port = os.environ.get("MAILPIT_UI_PORT", "8025")
    try:
        data = http_json(f"http://127.0.0.1:{port}/api/v1/messages?limit={limit}")
        msgs = data.get("messages") if isinstance(data, dict) else []
        out = []
        for m in msgs if isinstance(msgs, list) else []:
            if isinstance(m, dict):
                out.append(str(m.get("Subject") or ""))
        return out
    except Exception:
        return []


# —— check runners ——

def run_check(ctx: Ctx, lesson: str, check: dict[str, Any]) -> CheckResult:
    cid = str(check.get("id") or "check")
    assert_text = str(check.get("assert") or check.get("message") or cid)
    soft = bool(check.get("soft"))
    ctype = str(check.get("type") or "")

    def ok(detail: str = "") -> CheckResult:
        return CheckResult(lesson, cid, assert_text, True, detail, soft)

    def fail(detail: str = "") -> CheckResult:
        return CheckResult(lesson, cid, assert_text, False, detail, soft)

    try:
        if ctype == "http.ok":
            url = check["url"]
            return ok(url) if http_ok(url) else fail(f"not reachable: {url}")

        if ctype == "mcp.health":
            if not ensure_mcp(ctx):
                return fail("MCP init failed")
            try:
                h = ctx.mcp.healthz()
                return ok(str(h)[:120])
            except Exception as exc:  # noqa: BLE001
                return fail(str(exc))

        if ctype == "app.exists":
            name = check["name"]
            apps = list_apps(ctx)
            if name in apps:
                return ok(name)
            # soft: empty list means list failed — try export
            if object_exists(ctx, "Application", name):
                return ok(f"{name} (via export)")
            return fail(f"missing Application {name}")

        if ctype == "object.exists":
            clazz = check["objectClass"]
            name = check["name"]
            return ok(name) if object_exists(ctx, clazz, name) else fail(f"missing {clazz}/{name}")

        if ctype == "identity.exists":
            name = check["name"]
            return ok(name) if identity_exists(ctx, name) else fail(f"identity not found: {name}")

        if ctype == "system_config.eq":
            key = check["key"]
            expected = str(check["equals"])
            attrs = load_system_config(ctx)
            if not attrs:
                return fail("could not read SystemConfiguration")
            actual = attrs.get(key)
            actual_s = "" if actual is None else str(actual)
            if actual_s == expected or actual_s.lower() == expected.lower():
                return ok(f"{key}={actual_s}")
            return fail(f"{key} expected {expected!r} got {actual_s!r}")

        if ctype == "system_config.contains":
            key = check["key"]
            needle = str(check["contains"])
            attrs = load_system_config(ctx)
            if not attrs:
                return fail("could not read SystemConfiguration")
            actual_s = "" if attrs.get(key) is None else str(attrs.get(key))
            if needle.lower() in actual_s.lower():
                return ok(f"{key}={actual_s}")
            return fail(f"{key} missing {needle!r} (got {actual_s!r})")

        if ctype == "system_config.in":
            key = check["key"]
            options = [str(x).lower() for x in (check.get("options") or [])]
            attrs = load_system_config(ctx)
            if not attrs:
                return fail("could not read SystemConfiguration")
            actual_s = "" if attrs.get(key) is None else str(attrs.get(key))
            if actual_s.lower() in options:
                return ok(f"{key}={actual_s}")
            return fail(f"{key}={actual_s!r} not in {options}")

        if ctype == "json.path_contains":
            url = check["url"]
            needle = str(check["contains"])
            try:
                raw = urllib.request.urlopen(url, timeout=15).read().decode()
            except Exception as exc:  # noqa: BLE001
                return fail(str(exc))
            if needle in raw:
                return ok(f"found {needle!r}")
            return fail(f"{needle!r} not in {url}")

        if ctype == "mailpit.subject":
            subject = str(check["subject"])
            subjects = mailpit_subjects()
            if any(subject in s for s in subjects):
                return ok(f"Mailpit has {subject!r}")
            return fail(f"no Mailpit message with subject containing {subject!r}")

        if ctype == "shell.ok":
            cmd = check["command"]
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(REPO),
                capture_output=True,
                text=True,
                timeout=float(check.get("timeout", 180)),
            )
            if proc.returncode == 0:
                return ok((proc.stdout or "")[-200:].strip())
            return fail((proc.stderr or proc.stdout or "")[-300:].strip())

        return fail(f"unknown check type {ctype!r}")
    except Exception as exc:  # noqa: BLE001
        return fail(f"exception: {exc}")


def load_spec(lesson: str) -> dict[str, Any]:
    # Accept 203 or 203-mailpit-iiq-email
    candidates = list(SPECS_DIR.glob(f"{lesson}*.json"))
    if not candidates and lesson.isdigit():
        candidates = list(SPECS_DIR.glob(f"{int(lesson):03d}*.json"))
    if not candidates:
        raise SystemExit(f"No assert spec for lesson {lesson} under {SPECS_DIR}")
    path = sorted(candidates)[0]
    return json.loads(path.read_text(encoding="utf-8"))


def print_result(r: CheckResult) -> None:
    status = "PASS" if r.ok else ("SOFT" if r.soft and not r.ok else "FAIL")
    # soft fails still show as FAIL-soft for visibility but don't fail the run
    if r.soft and not r.ok:
        status = "FAIL*"
    line = f"{status:5} {r.lesson}.{r.check_id}  assert: {r.assert_text}"
    if r.detail:
        line += f"  [{r.detail}]"
    if r.soft and not r.ok:
        line += "  (soft — does not fail lesson)"
    _log(line)


def run_lesson(ctx: Ctx, lesson: str) -> tuple[int, int, int, list[CheckResult]]:
    spec = load_spec(lesson)
    title = spec.get("title") or lesson
    checks = spec.get("checks") or []
    _log(f"\n==> Lesson {spec.get('lesson', lesson)} — {title}")
    _log(f"    {len(checks)} assert(s)")
    passed = failed = soft_failed = 0
    results: list[CheckResult] = []
    for check in checks:
        r = run_check(ctx, str(spec.get("lesson") or lesson), check)
        print_result(r)
        results.append(r)
        if r.ok:
            passed += 1
        elif r.soft:
            soft_failed += 1
        else:
            failed += 1
    return passed, failed, soft_failed, results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("lessons", nargs="*", help="Lesson numbers (201 202 203) or stems")
    p.add_argument("--all", action="store_true", help="Run every spec in lesson-asserts/")
    p.add_argument("--mcp-url", default=os.environ.get("IIQ_MCP_URL", "http://127.0.0.1:8766/mcp"))
    p.add_argument(
        "--mcp-api-key",
        default=os.environ.get("MCP_API_KEY")
        or os.environ.get("IIQ_MCP_API_KEY")
        or "mnb-lab-mcp-key",
    )
    p.add_argument(
        "--iiq-base",
        default=os.environ.get("IIQ_BASE_URL", "http://127.0.0.1:8080/identityiq"),
    )
    p.add_argument("--iiq-user", default=os.environ.get("IIQ_USER", "spadmin"))
    p.add_argument("--iiq-password", default=os.environ.get("IIQ_PASSWORD", "admin"))
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit one JSON report on stdout (for Academy's /api/verify) instead of text",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    global JSON_MODE
    args = parse_args(argv)
    JSON_MODE = bool(args.json)
    if args.all:
        lessons = sorted({p.name.split("-")[0] for p in SPECS_DIR.glob("*.json")})
    else:
        lessons = args.lessons
    if not lessons:
        _log("Usage: verify-lesson.sh 203   or   verify-lesson.sh --all")
        return 2

    ctx = Ctx(
        iiq_base=args.iiq_base,
        iiq_user=args.iiq_user,
        iiq_pass=args.iiq_password,
        mcp_url=args.mcp_url,
        mcp_key=args.mcp_api_key,
    )

    total_p = total_f = total_s = 0
    all_results: list[CheckResult] = []
    for lesson in lessons:
        try:
            p, f, s, results = run_lesson(ctx, lesson)
        except SystemExit as exc:
            msg = str(exc)
            all_results.append(CheckResult(lesson, "spec-missing", msg, False, msg, soft=False))
            total_f += 1
            if not JSON_MODE:
                _log(msg)
            continue
        total_p += p
        total_f += f
        total_s += s
        all_results.extend(results)

    if JSON_MODE:
        payload = {
            "schema": "mnb-enterprise-lesson-verify/v1",
            "lessons": lessons,
            "summary": {
                "total": total_p + total_f + total_s,
                "passed": total_p,
                "failed": total_f,
                "softFailed": total_s,
            },
            "verdict": "PASS" if total_f == 0 else "FAIL",
            "checks": [
                {
                    "id": f"{r.lesson}.{r.check_id}",
                    "status": "PASS" if r.ok else ("SOFT" if r.soft else "FAIL"),
                    "message": r.assert_text,
                    "detail": r.detail,
                    "soft": r.soft,
                }
                for r in all_results
            ],
        }
        print(json.dumps(payload))
        return 0 if total_f == 0 else 1

    _log(
        f"\nResult: {total_p} passed, {total_f} failed"
        + (f", {total_s} soft-fail" if total_s else "")
    )
    return 0 if total_f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
