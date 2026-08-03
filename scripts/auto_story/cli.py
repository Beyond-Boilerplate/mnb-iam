"""CLI for auto-story runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config, resolve_path
from .runner import poll_ready, run_story


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="auto-story",
        description="Meridian Auto-story Jira runner (Teller-class MCP agent, In Review only)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.yaml (or set AUTO_STORY_CONFIG)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_poll = sub.add_parser("poll", help="List agent-ready issues")
    p_poll.add_argument("--json", action="store_true")

    p_run = sub.add_parser("run", help="Run one issue through the control loop")
    p_run.add_argument("--issue", required=True, help="Issue key e.g. KAN-1 or MNB-105")
    p_run.add_argument(
        "--live",
        action="store_true",
        help="Allow mutating IIQ MCP + Jira transitions (default is dry-run)",
    )
    p_run.add_argument("--tail", action="store_true", help="Stream ledger events to stderr")
    p_run.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Fixture dir (offline). Skips Jira assign/transition.",
    )
    p_run.add_argument(
        "--no-llm",
        action="store_true",
        help="Use heuristic feasibility only (no OpenRouter/etc.)",
    )
    p_run.add_argument(
        "--verbose-think",
        action="store_true",
        help="Fuller THINK payloads in the ledger",
    )

    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    if getattr(args, "verbose_think", False):
        cfg.setdefault("agent", {})["verbose_think"] = True

    if args.cmd == "poll":
        try:
            issues = poll_ready(cfg)
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1
        if args.json:
            print(json.dumps({"ok": True, "issues": issues}, indent=2))
        else:
            for i in issues:
                print(f"{i.get('key')}\t{i.get('summary')}")
            if not issues:
                print("(no agent-ready issues)")
        return 0

    if args.cmd == "run":
        fixture = args.fixture
        if fixture:
            fixture = resolve_path(cfg, str(fixture)) if not Path(fixture).is_absolute() else Path(fixture)
        try:
            result = run_story(
                issue_key=args.issue,
                cfg=cfg,
                live=bool(args.live),
                tail=bool(args.tail),
                fixture_dir=fixture,
                use_llm=not bool(args.no_llm),
            )
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("ok") or result.get("skipped") or result.get("dry_run") else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
