#!/usr/bin/env python3
"""Blackbox Teller evaluation runner.

Feeds golden utterances to POST /api/chat and asserts on reply + tool steps.
Designed for free-tier OpenRouter: configurable inter-case delay + optional jitter.

Examples:

  # Smoke only (fast subset)
  TELLER_URL=http://127.0.0.1:4180 OPENROUTER_API_KEY=… \\
    python3 tools/iiq-chat/eval/runner.py --tier smoke --delay 8

  # Full suite, write HTML+JSON report
  python3 tools/iiq-chat/eval/runner.py --tier full --delay 12 --jitter 3

  # Filter + limit
  python3 tools/iiq-chat/eval/runner.py --tags identity,access --limit 5

  # Offline: assert engine only (fixture mode)
  python3 tools/iiq-chat/eval/runner.py --list
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVAL_ROOT = Path(__file__).resolve().parent
CHAT_ROOT = EVAL_ROOT.parent
sys.path.insert(0, str(CHAT_ROOT))
sys.path.insert(0, str(EVAL_ROOT))

from assert_engine import evaluate_case  # noqa: E402
from client import TellerClient  # noqa: E402

CASES_DIR = EVAL_ROOT / "cases"
REPORTS_DIR = EVAL_ROOT / "reports"

TIER_ORDER = {"smoke": 0, "core": 1, "full": 2, "stress": 3}


def load_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(CASES_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    item.setdefault("_file", path.name)
                    cases.append(item)
        elif isinstance(data, dict) and "cases" in data:
            for item in data["cases"]:
                if isinstance(item, dict):
                    item.setdefault("_file", path.name)
                    cases.append(item)
        elif isinstance(data, dict) and data.get("id"):
            data.setdefault("_file", path.name)
            cases.append(data)
    return cases


def filter_cases(
    cases: list[dict[str, Any]],
    *,
    tier: str,
    tags: set[str] | None,
    ids: set[str] | None,
    include_xfail: bool,
    mutate: bool | None,
) -> list[dict[str, Any]]:
    max_tier = TIER_ORDER.get(tier, 1)
    out: list[dict[str, Any]] = []
    for c in cases:
        c_tier = TIER_ORDER.get(str(c.get("tier") or "core"), 1)
        if c_tier > max_tier:
            continue
        if ids and c.get("id") not in ids:
            continue
        c_tags = {str(t) for t in (c.get("tags") or [])}
        if tags and not (c_tags & tags):
            continue
        if not include_xfail and c.get("xfail"):
            continue
        if mutate is False and c.get("mutate"):
            continue
        if mutate is True and not c.get("mutate"):
            continue
        out.append(c)
    return out


def _html_report(rows: list[dict[str, Any]], meta: dict[str, Any]) -> str:
    def esc(s: Any) -> str:
        return (
            str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    passed = sum(1 for r in rows if r["status"] == "pass")
    failed = sum(1 for r in rows if r["status"] == "fail")
    xfail = sum(1 for r in rows if r["status"] == "xfail")
    xpass = sum(1 for r in rows if r["status"] == "xpass")
    skipped = sum(1 for r in rows if r["status"] == "skip")

    trs = []
    for r in rows:
        cls = r["status"]
        fails = "<br/>".join(esc(f) for f in (r.get("failures") or [])[:6])
        tools = ", ".join(esc(t) for t in (r.get("tools") or [])[:8])
        trs.append(
            f"<tr class='{cls}'><td>{esc(r.get('id'))}</td><td>{esc(r['status'])}</td>"
            f"<td>{esc(r.get('tier'))}</td><td>{esc(','.join(r.get('tags') or []))}</td>"
            f"<td>{esc((r.get('query') or '')[:80])}</td><td>{tools}</td>"
            f"<td>{esc((r.get('reply') or '')[:160])}</td><td>{fails}</td>"
            f"<td>{r.get('elapsed_s', '')}</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>Teller eval {esc(meta.get('started'))}</title>
<style>
body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 24px; background: #0f1419; color: #e7ecf1; }}
h1 {{ font-size: 1.25rem; }}
.meta {{ color: #9aa7b5; margin-bottom: 16px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #2a3540; padding: 6px 8px; vertical-align: top; }}
th {{ background: #1a222c; text-align: left; position: sticky; top: 0; }}
tr.pass td:nth-child(2) {{ color: #3dd68c; }}
tr.fail td:nth-child(2) {{ color: #ff6b6b; font-weight: 600; }}
tr.xfail td:nth-child(2) {{ color: #f0c14b; }}
tr.xpass td:nth-child(2) {{ color: #7aa2ff; }}
tr.skip td:nth-child(2) {{ color: #9aa7b5; }}
.stats span {{ margin-right: 14px; }}
</style></head><body>
<h1>Teller blackbox eval</h1>
<div class="meta">
  <div>started={esc(meta.get('started'))} · teller={esc(meta.get('teller_url'))} · tier={esc(meta.get('tier'))} · delay={esc(meta.get('delay_s'))}s</div>
  <div class="stats">
    <span>pass={passed}</span><span>fail={failed}</span><span>xfail={xfail}</span>
    <span>xpass={xpass}</span><span>skip={skipped}</span><span>total={len(rows)}</span>
  </div>
</div>
<table>
<thead><tr><th>id</th><th>status</th><th>tier</th><th>tags</th><th>query</th><th>tools</th><th>reply</th><th>failures</th><th>s</th></tr></thead>
<tbody>
{''.join(trs)}
</tbody></table>
</body></html>
"""


def run(args: argparse.Namespace) -> int:
    cases = load_cases()
    if args.list:
        for c in cases:
            print(
                f"{c.get('id'):40} tier={c.get('tier','core'):6} "
                f"tags={','.join(c.get('tags') or [])} "
                f"{'XFAIL ' if c.get('xfail') else ''}"
                f"{'MUTATE ' if c.get('mutate') else ''}"
                f"| {c.get('query','')[:70]}"
            )
        print(f"\n{len(cases)} cases in {CASES_DIR}")
        return 0

    tags = {t.strip() for t in (args.tags or "").split(",") if t.strip()} or None
    ids = {t.strip() for t in (args.ids or "").split(",") if t.strip()} or None
    mutate_filter: bool | None = None
    if args.read_only:
        mutate_filter = False
    elif args.mutate_only:
        mutate_filter = True

    selected = filter_cases(
        cases,
        tier=args.tier,
        tags=tags,
        ids=ids,
        include_xfail=not args.exclude_xfail,
        mutate=mutate_filter,
    )
    if args.limit and args.limit > 0:
        selected = selected[: args.limit]

    if not selected:
        print("No cases selected.", file=sys.stderr)
        return 2

    client = TellerClient(base_url=args.teller_url, timeout=args.timeout)
    health = client.health()
    config = client.config()
    if health.get("ok") is False:
        print(f"Teller unhealthy: {health}", file=sys.stderr)
        return 2
    if not config.get("llmConfigured") or not config.get("llmAuthOk"):
        print(
            f"WARN: LLM not ready (llmConfigured={config.get('llmConfigured')} "
            f"llmAuthOk={config.get('llmAuthOk')}) — chat cases will fail.",
            file=sys.stderr,
        )
    if args.refresh_tools:
        client.refresh_tools()

    started = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    print(
        f"Running {len(selected)} cases against {client.base_url} "
        f"(tier={args.tier}, delay={args.delay}s±{args.jitter}s)"
    )

    for i, case in enumerate(selected):
        cid = case.get("id") or f"case-{i}"
        query = str(case.get("query") or "").strip()
        if case.get("skip"):
            rows.append(
                {
                    "id": cid,
                    "status": "skip",
                    "tier": case.get("tier"),
                    "tags": case.get("tags") or [],
                    "query": query,
                    "failures": [],
                    "reply": "",
                    "tools": [],
                    "elapsed_s": 0,
                    "xfail": bool(case.get("xfail")),
                }
            )
            print(f"  [{i+1}/{len(selected)}] SKIP {cid}")
            continue

        t0 = time.time()
        print(f"  [{i+1}/{len(selected)}] ASK  {cid}: {query[:90]}")
        response = client.chat(query, history=case.get("history") or [])
        elapsed = round(time.time() - t0, 2)
        result = evaluate_case(case, response if isinstance(response, dict) else {"ok": False})

        tools = []
        steps = response.get("steps") if isinstance(response, dict) else []
        if isinstance(steps, list):
            tools = [str(s.get("tool")) for s in steps if isinstance(s, dict) and s.get("tool")]

        xfail = bool(case.get("xfail"))
        if result.ok and xfail:
            status = "xpass"
        elif result.ok:
            status = "pass"
        elif xfail:
            status = "xfail"
        else:
            status = "fail"

        row = {
            "id": cid,
            "status": status,
            "tier": case.get("tier") or "core",
            "tags": case.get("tags") or [],
            "query": query,
            "failures": result.failures,
            "notes": result.notes + ([case.get("xfail_reason")] if case.get("xfail_reason") else []),
            "reply": (response.get("reply") if isinstance(response, dict) else "") or "",
            "tools": tools,
            "elapsed_s": elapsed,
            "xfail": xfail,
            "model": response.get("model") if isinstance(response, dict) else None,
            "response_ok": response.get("ok") if isinstance(response, dict) else False,
        }
        rows.append(row)
        mark = {"pass": "OK", "fail": "FAIL", "xfail": "XFAIL", "xpass": "XPASS"}[status]
        extra = ""
        if result.failures:
            extra = " — " + result.failures[0][:120]
        print(f"         {mark}  tools={tools}{extra} ({elapsed}s)")

        # Persist raw response for debugging
        if args.save_raw:
            raw_dir = REPORTS_DIR / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / f"{cid}.json").write_text(
                json.dumps(
                    {"case": case, "response": response, "assert": row},
                    indent=2,
                    default=str,
                )
            )

        if i < len(selected) - 1 and args.delay > 0:
            wait = args.delay + (random.uniform(0, args.jitter) if args.jitter else 0)
            time.sleep(wait)

    meta = {
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "teller_url": client.base_url,
        "tier": args.tier,
        "delay_s": args.delay,
        "jitter_s": args.jitter,
        "case_count": len(selected),
        "config": {
            "llmConfigured": config.get("llmConfigured"),
            "llmAuthOk": config.get("llmAuthOk"),
            "model": config.get("model"),
            "toolCount": config.get("toolCount"),
        },
    }
    summary = {
        "pass": sum(1 for r in rows if r["status"] == "pass"),
        "fail": sum(1 for r in rows if r["status"] == "fail"),
        "xfail": sum(1 for r in rows if r["status"] == "xfail"),
        "xpass": sum(1 for r in rows if r["status"] == "xpass"),
        "skip": sum(1 for r in rows if r["status"] == "skip"),
    }
    meta["summary"] = summary

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = REPORTS_DIR / f"teller-eval-{stamp}.json"
    html_path = REPORTS_DIR / f"teller-eval-{stamp}.html"
    latest_json = REPORTS_DIR / "latest.json"
    latest_html = REPORTS_DIR / "latest.html"

    payload = {"meta": meta, "results": rows}
    json_path.write_text(json.dumps(payload, indent=2, default=str))
    html = _html_report(rows, meta)
    html_path.write_text(html)
    latest_json.write_text(json_path.read_text())
    latest_html.write_text(html)

    print("\n=== Summary ===")
    print(
        f"pass={summary['pass']} fail={summary['fail']} "
        f"xfail={summary['xfail']} xpass={summary['xpass']} skip={summary['skip']}"
    )
    print(f"report: {html_path}")
    print(f"latest: {latest_html}")

    # Exit: fail on unexpected failures; xfail alone is OK
    if summary["fail"] > 0:
        return 1
    if args.strict_xpass and summary["xpass"] > 0:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--teller-url", default=os.environ.get("TELLER_URL", "http://127.0.0.1:4180"))
    p.add_argument(
        "--tier",
        default="core",
        choices=list(TIER_ORDER),
        help="Include cases up to this tier (smoke ⊂ core ⊂ full ⊂ stress)",
    )
    p.add_argument("--tags", default="", help="Comma-separated tag filter (OR)")
    p.add_argument("--ids", default="", help="Comma-separated case id filter")
    p.add_argument("--limit", type=int, default=0, help="Max cases to run (0=all)")
    p.add_argument("--delay", type=float, default=10.0, help="Seconds between cases (rate-limit)")
    p.add_argument("--jitter", type=float, default=2.0, help="Extra random delay 0..jitter")
    p.add_argument("--timeout", type=float, default=180.0, help="Per-chat HTTP timeout")
    p.add_argument("--list", action="store_true", help="List cases and exit")
    p.add_argument("--read-only", action="store_true", help="Skip mutate=true cases")
    p.add_argument("--mutate-only", action="store_true", help="Only mutate=true cases")
    p.add_argument("--exclude-xfail", action="store_true", help="Do not run xfail cases")
    p.add_argument("--strict-xpass", action="store_true", help="Exit 1 if an xfail unexpectedly passes")
    p.add_argument("--refresh-tools", action="store_true", help="POST /api/tools/refresh first")
    p.add_argument("--save-raw", action="store_true", help="Write per-case raw JSON under reports/raw/")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
