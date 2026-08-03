"""Auto-story run browser APIs for Meridian Teller."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(
    os.environ.get("SAILPOINT_ROOT")
    or os.environ.get("AUTO_STORY_REPO_ROOT")
    or Path(__file__).resolve().parents[2]
).resolve()
DELIVERY = Path(os.environ.get("AI_DELIVERY_DIR") or (REPO_ROOT / ".ai-delivery")).resolve()
EXAMPLES = Path(__file__).resolve().parent / "static" / "auto-story-examples.json"

_JOBS: dict[str, dict[str, Any]] = {}
_JOBS_LOCK = threading.Lock()

ARTIFACT_FILES = {
    "feasibility": ("feasibility.json", "json"),
    "plan": ("plan.md", "text"),
    "evidence": ("evidence.json", "json"),
    "verify": ("verify.json", "json"),
    "handoff": ("handoff.json", "json"),
    "implement": ("implement.json", "json"),
}


def _safe_segment(name: str) -> str | None:
    if not name or ".." in name or "/" in name or "\\" in name:
        return None
    return name


def list_runs(limit: int = 100) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if not DELIVERY.is_dir():
        return runs
    for issue_dir in sorted(DELIVERY.iterdir(), key=lambda p: p.name):
        if not issue_dir.is_dir() or issue_dir.name.startswith("_"):
            continue
        runs_dir = issue_dir / "runs"
        if not runs_dir.is_dir():
            continue
        for run_dir in sorted(runs_dir.iterdir(), key=lambda p: p.name, reverse=True):
            if not run_dir.is_dir():
                continue
            events_path = run_dir / "events.jsonl"
            summary = ""
            outcome = ""
            mtime = run_dir.stat().st_mtime
            if events_path.is_file():
                try:
                    lines = events_path.read_text(encoding="utf-8").splitlines()
                    if lines:
                        first = json.loads(lines[0])
                        summary = str(first.get("summary") or "")
                        mtime = max(mtime, events_path.stat().st_mtime)
                    for line in reversed(lines[-30:]):
                        ev = json.loads(line)
                        if ev.get("type") in ("HANDOFF", "VERIFY", "ERROR", "DECIDE"):
                            outcome = str(ev.get("summary") or ev.get("message") or ev.get("type") or "")
                            break
                except (OSError, json.JSONDecodeError):
                    pass
            runs.append(
                {
                    "issue": issue_dir.name,
                    "run_id": run_dir.name,
                    "summary": summary,
                    "outcome": outcome,
                    "mtime": mtime,
                    "path": str(run_dir.relative_to(REPO_ROOT)),
                }
            )
    runs.sort(key=lambda r: r["mtime"], reverse=True)
    return runs[:limit]


def _run_dir(issue: str, run_id: str) -> Path | None:
    iss = _safe_segment(issue)
    rid = _safe_segment(run_id)
    if not iss or not rid:
        return None
    path = DELIVERY / iss / "runs" / rid
    if not path.is_dir():
        return None
    try:
        path.resolve().relative_to(DELIVERY.resolve())
    except ValueError:
        return None
    return path


def read_events(issue: str, run_id: str, after: int = 0) -> list[dict[str, Any]]:
    path = _run_dir(issue, run_id)
    if not path:
        return []
    events_path = path / "events.jsonl"
    if not events_path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for i, line in enumerate(events_path.read_text(encoding="utf-8").splitlines()):
        if i < after:
            continue
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"type": "ERROR", "summary": "bad jsonl line", "raw": line[:200]})
    return events


def read_artifacts(issue: str, run_id: str) -> dict[str, Any]:
    path = _run_dir(issue, run_id)
    if not path:
        return {}
    out: dict[str, Any] = {}
    for key, (fname, kind) in ARTIFACT_FILES.items():
        fpath = path / fname
        if not fpath.is_file():
            continue
        try:
            text = fpath.read_text(encoding="utf-8")
            if kind == "json":
                out[key] = json.loads(text)
            else:
                out[key] = text
        except (OSError, json.JSONDecodeError) as exc:
            out[key] = {"error": str(exc)}
    return out


def load_examples() -> list[dict[str, Any]]:
    if not EXAMPLES.is_file():
        return []
    data = json.loads(EXAMPLES.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _resolve_fixture(fixture: str) -> Path | None:
    raw = Path(fixture)
    path = raw if raw.is_absolute() else (REPO_ROOT / raw)
    try:
        resolved = path.resolve()
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        return None
    if not resolved.is_file():
        return None
    return resolved


def _ensure_scripts_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def poll_ready() -> dict[str, Any]:
    """List agent-ready Jira issues (same JQL as CLI poll)."""
    _ensure_scripts_path()
    try:
        from scripts.auto_story.config import load_config
        from scripts.auto_story.runner import poll_ready as _poll
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"import failed: {exc}", "issues": []}
    try:
        cfg = load_config()
        issues = _poll(cfg)
        return {
            "ok": True,
            "jql": (cfg.get("jira") or {}).get("ready_jql"),
            "issues": issues,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "issues": []}


def start_run(
    *,
    issue: str,
    fixture: str | None = None,
    no_llm: bool = False,
    live: bool = False,
    confirm_live: bool = False,
) -> dict[str, Any]:
    """Spawn auto-story in a background thread.

    Live requires confirm_live=True (UI double-confirm). Never Done.
    """
    if live and not confirm_live:
        return {"ok": False, "error": "Live requires confirm_live=true (mutates IIQ + Jira → In Review)."}
    # Alias kept for older callers
    return _start_job(issue=issue, fixture=fixture, no_llm=no_llm, live=live)


def start_dry_run(
    *,
    issue: str,
    fixture: str | None = None,
    no_llm: bool = True,
    live: bool = False,
    confirm_live: bool = False,
) -> dict[str, Any]:
    return start_run(
        issue=issue,
        fixture=fixture,
        no_llm=no_llm,
        live=live,
        confirm_live=confirm_live,
    )


def _newest_run_id(issue: str, *, after_mtime: float) -> str | None:
    runs_dir = DELIVERY / issue / "runs"
    if not runs_dir.is_dir():
        return None
    best: tuple[float, str] | None = None
    for p in runs_dir.iterdir():
        if not p.is_dir():
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if mtime + 0.05 < after_mtime:
            continue
        if best is None or mtime >= best[0]:
            best = (mtime, p.name)
    return best[1] if best else None


def _last_event_summary(issue: str, run_id: str) -> dict[str, Any]:
    events = read_events(issue, run_id)
    if not events:
        return {"event_count": 0, "last_event": None}
    last = events[-1]
    return {
        "event_count": len(events),
        "last_event": {
            "type": last.get("type"),
            "summary": last.get("summary") or last.get("message") or last.get("type"),
            "ts": last.get("ts"),
        },
    }


def _parse_result_payload(stdout: str, issue: str) -> tuple[str | None, str]:
    run_id = None
    issue_out = issue
    payload: dict[str, Any] | None = None
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, dict):
            payload = parsed
    except json.JSONDecodeError:
        start = stdout.find("{")
        end = stdout.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(stdout[start : end + 1])
                if isinstance(parsed, dict):
                    payload = parsed
            except json.JSONDecodeError:
                payload = None
    if payload:
        run_id = payload.get("run_id") or payload.get("runId")
        if not run_id:
            run_dir = str(
                payload.get("run_dir") or (payload.get("evidence") or {}).get("run_dir") or ""
            )
            if "/runs/" in run_dir:
                run_id = run_dir.rstrip("/").split("/runs/")[-1]
        issue_out = str(payload.get("issue") or issue)
    else:
        m = re.search(r"/runs/([0-9A-Za-zT-]+)", stdout)
        if m:
            run_id = m.group(1)
    return (str(run_id) if run_id else None), issue_out


def _start_job(
    *,
    issue: str,
    fixture: str | None = None,
    no_llm: bool = False,
    live: bool = False,
) -> dict[str, Any]:
    iss = _safe_segment(issue)
    if not iss:
        if issue and re.fullmatch(r"[A-Za-z][A-Za-z0-9]+-\d+", issue.strip()):
            iss = issue.strip()
        else:
            return {"ok": False, "error": "invalid issue"}
    fixture_path: Path | None = None
    if fixture:
        fixture_path = _resolve_fixture(fixture)
        if not fixture_path:
            raw = Path(fixture)
            cand = raw if raw.is_absolute() else (REPO_ROOT / raw)
            try:
                resolved = cand.resolve()
                resolved.relative_to(REPO_ROOT.resolve())
            except ValueError:
                resolved = None
            if resolved and resolved.is_dir():
                fixture_path = resolved
            else:
                return {"ok": False, "error": "invalid or missing fixture"}
        elif fixture_path.is_file():
            fixture_path = fixture_path.parent

    job_id = uuid.uuid4().hex[:12]
    started_at = time.time()
    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "status": "running",
            "issue": iss,
            "message": "starting",
            "run_id": None,
            "error": None,
            "live": live,
            "started_at": started_at,
            "event_count": 0,
            "last_event": None,
        }

    def worker() -> None:
        import time as _time

        cmd = [
            "python3",
            "-m",
            "scripts.auto_story",
            "run",
            "--issue",
            iss,
            "--tail",
        ]
        if fixture_path:
            cmd.extend(["--fixture", str(fixture_path)])
        if no_llm:
            cmd.append("--no-llm")
        if live:
            cmd.append("--live")
        try:
            with _JOBS_LOCK:
                _JOBS[job_id]["message"] = " ".join(cmd)
            env = os.environ.copy()
            # Drain pipes in threads so --tail stderr cannot deadlock the child
            proc = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1,
            )
            stdout_chunks: list[str] = []
            stderr_chunks: list[str] = []

            def _drain(stream: Any, sink: list[str]) -> None:
                try:
                    if stream is None:
                        return
                    for line in stream:
                        sink.append(line)
                        if len(sink) > 4000:
                            del sink[:2000]
                except Exception:  # noqa: BLE001
                    return

            t_out = threading.Thread(target=_drain, args=(proc.stdout, stdout_chunks), daemon=True)
            t_err = threading.Thread(target=_drain, args=(proc.stderr, stderr_chunks), daemon=True)
            t_out.start()
            t_err.start()

            deadline = time.time() + 900
            run_id: str | None = None
            while proc.poll() is None:
                if time.time() > deadline:
                    proc.kill()
                    with _JOBS_LOCK:
                        _JOBS[job_id].update(
                            {"status": "error", "error": "timeout after 900s", "message": "timeout"}
                        )
                    return
                found = _newest_run_id(iss, after_mtime=started_at - 1)
                if found and found != run_id:
                    run_id = found
                    with _JOBS_LOCK:
                        _JOBS[job_id]["run_id"] = run_id
                        _JOBS[job_id]["message"] = f"streaming {iss}/{run_id}"
                if run_id:
                    meta = _last_event_summary(iss, run_id)
                    with _JOBS_LOCK:
                        _JOBS[job_id].update(meta)
                        if meta.get("last_event"):
                            le = meta["last_event"]
                            _JOBS[job_id]["message"] = f"{le.get('type')}: {le.get('summary')}"
                time.sleep(0.35)

            t_out.join(timeout=5)
            t_err.join(timeout=5)
            stdout = "".join(stdout_chunks).strip()
            stderr = "".join(stderr_chunks).strip()
            parsed_run, issue_out = _parse_result_payload(stdout, iss)
            if parsed_run:
                run_id = parsed_run
            if not run_id:
                run_id = _newest_run_id(iss, after_mtime=started_at - 1)
            meta = _last_event_summary(iss, run_id) if run_id else {"event_count": 0, "last_event": None}

            with _JOBS_LOCK:
                if proc.returncode == 0:
                    _JOBS[job_id].update(
                        {
                            "status": "ok",
                            "issue": issue_out,
                            "run_id": run_id,
                            "message": "completed",
                            "stdout_tail": stdout[-800:].replace("\x00", ""),
                            **meta,
                        }
                    )
                else:
                    _JOBS[job_id].update(
                        {
                            "status": "error",
                            "issue": issue_out,
                            "run_id": run_id,
                            "error": (stderr or stdout)[-800:].replace("\x00", "")
                            or f"exit {proc.returncode}",
                            "message": "failed",
                            **meta,
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            with _JOBS_LOCK:
                _JOBS[job_id].update({"status": "error", "error": str(exc), "message": "exception"})

    threading.Thread(target=worker, daemon=True, name=f"auto-story-{job_id}").start()
    return {"ok": True, "job_id": job_id, "issue": iss, "live": live}


def job_status(job_id: str) -> dict[str, Any] | None:
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return None
        out = dict(job)
    # Refresh live event meta if still running with a known run
    if out.get("status") == "running" and out.get("issue") and out.get("run_id"):
        meta = _last_event_summary(str(out["issue"]), str(out["run_id"]))
        out.update(meta)
        with _JOBS_LOCK:
            if job_id in _JOBS:
                _JOBS[job_id].update(meta)
    return out


def list_jobs(limit: int = 20) -> list[dict[str, Any]]:
    with _JOBS_LOCK:
        jobs = [dict(j) for j in _JOBS.values()]
    jobs.sort(key=lambda j: float(j.get("started_at") or 0), reverse=True)
    return jobs[:limit]
