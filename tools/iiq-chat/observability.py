"""Structured JSON logs, in-process metrics, and light tracing for Teller."""

from __future__ import annotations

import json
import sys
import threading
import time
import uuid
from collections import deque
from contextlib import contextmanager
from typing import Any, Iterator


def new_correlation_id() -> str:
    return uuid.uuid4().hex[:16]


def log_event(
    event: str,
    *,
    correlation_id: str | None = None,
    user_id: str | None = None,
    run_id: str | None = None,
    tool: str | None = None,
    latency_ms: float | None = None,
    outcome: str | None = None,
    **extra: Any,
) -> None:
    """Emit one JSON log line to stderr (stdout stays for server banners)."""
    payload: dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        "service": "teller",
    }
    if correlation_id:
        payload["correlationId"] = correlation_id
    if user_id:
        payload["userId"] = user_id
    if run_id:
        payload["runId"] = run_id
    if tool:
        payload["tool"] = tool
    if latency_ms is not None:
        payload["latencyMs"] = round(float(latency_ms), 2)
    if outcome:
        payload["outcome"] = outcome
    for key, value in extra.items():
        if value is not None:
            payload[key] = value
    sys.stderr.write(json.dumps(payload, default=str) + "\n")
    sys.stderr.flush()


class MetricsRegistry:
    """Thread-safe counters + latency samples for operator dashboards."""

    def __init__(self, *, max_samples: int = 500) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}
        self._samples: dict[str, deque[float]] = {}
        self._max_samples = max_samples
        self._started = time.time()
        self._mcp_up = False
        self._mcp_checks = 0
        self._mcp_ok = 0

    def inc(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount

    def observe(self, name: str, value_ms: float) -> None:
        with self._lock:
            bucket = self._samples.setdefault(name, deque(maxlen=self._max_samples))
            bucket.append(float(value_ms))

    def set_mcp(self, up: bool) -> None:
        with self._lock:
            self._mcp_checks += 1
            if up:
                self._mcp_ok += 1
            self._mcp_up = up

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latencies: dict[str, Any] = {}
            for name, samples in self._samples.items():
                if not samples:
                    continue
                ordered = sorted(samples)
                latencies[name] = {
                    "count": len(ordered),
                    "p50": _percentile(ordered, 50),
                    "p95": _percentile(ordered, 95),
                    "p99": _percentile(ordered, 99),
                    "max": ordered[-1],
                }
            checks = self._mcp_checks or 1
            return {
                "uptimeSec": round(time.time() - self._started, 1),
                "counters": dict(self._counters),
                "latencies": latencies,
                "mcp": {
                    "up": self._mcp_up,
                    "uptimeRatio": round(self._mcp_ok / checks, 4),
                    "checks": self._mcp_checks,
                    "ok": self._mcp_ok,
                },
            }


def _percentile(ordered: list[float], pct: float) -> float:
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return round(ordered[0], 2)
    rank = (pct / 100.0) * (len(ordered) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return round(ordered[lo] * (1 - frac) + ordered[hi] * frac, 2)


METRICS = MetricsRegistry()


@contextmanager
def timed(
    metric_name: str,
    *,
    event: str | None = None,
    correlation_id: str | None = None,
    run_id: str | None = None,
    tool: str | None = None,
    user_id: str | None = None,
    **extra: Any,
) -> Iterator[dict[str, Any]]:
    """Context manager that records latency and optionally logs outcome."""
    ctx: dict[str, Any] = {"outcome": "success"}
    started = time.perf_counter()
    try:
        yield ctx
    except Exception:
        ctx["outcome"] = "error"
        raise
    finally:
        ms = (time.perf_counter() - started) * 1000.0
        METRICS.observe(metric_name, ms)
        if event:
            log_event(
                event,
                correlation_id=correlation_id,
                user_id=user_id,
                run_id=run_id,
                tool=tool,
                latency_ms=ms,
                outcome=str(ctx.get("outcome") or "success"),
                **extra,
            )


def span_attrs(
    *,
    correlation_id: str | None = None,
    run_id: str | None = None,
    tool: str | None = None,
    user_id: str | None = None,
) -> dict[str, str]:
    """Attributes suitable for future OTel spans (logged today as trace.*)."""
    out: dict[str, str] = {}
    if correlation_id:
        out["trace.correlationId"] = correlation_id
    if run_id:
        out["trace.runId"] = run_id
    if tool:
        out["trace.tool"] = tool
    if user_id:
        out["trace.userId"] = user_id
    return out
