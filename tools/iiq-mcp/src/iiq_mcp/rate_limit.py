"""Token-bucket + concurrency limiter for MCP → IIQ calls."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from iiq_mcp.errors import rate_limited


class RateLimiter:
    """Simple async rate limiter (RPS + max concurrent)."""

    def __init__(self, max_rps: float, max_concurrent: int) -> None:
        self._max_rps = max(0.1, float(max_rps))
        self._tokens = self._max_rps
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()
        self._sem = asyncio.Semaphore(max(1, int(max_concurrent)))

    async def _take_token(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._updated
            self._updated = now
            self._tokens = min(self._max_rps, self._tokens + elapsed * self._max_rps)
            if self._tokens < 1.0:
                need = 1.0 - self._tokens
                wait = need / self._max_rps
                await asyncio.sleep(wait)
                self._tokens = 0.0
                self._updated = time.monotonic()
            else:
                self._tokens -= 1.0

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        await self._take_token()
        acquired = False
        try:
            # Non-blocking try first to fail fast under overload
            try:
                await asyncio.wait_for(self._sem.acquire(), timeout=5.0)
                acquired = True
            except TimeoutError as exc:
                raise rate_limited(
                    "Too many concurrent IIQ calls; reduce agent parallelism."
                ) from exc
            yield
        finally:
            if acquired:
                self._sem.release()
