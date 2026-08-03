"""Thin OpenRouter chat client for podcast-studio agents."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Prefer a capable free/paid model; override with PODCAST_STUDIO_MODEL.
DEFAULT_MODEL = os.environ.get(
    "PODCAST_STUDIO_MODEL",
    "openrouter/free",
)


class StudioLLM:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        raw = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        self.api_key = (raw or "").strip().strip("\"'")
        self.model = model or DEFAULT_MODEL
        fallbacks = os.environ.get(
            "PODCAST_STUDIO_FALLBACK_MODELS",
            "openrouter/free,"
            "meta-llama/llama-3.3-70b-instruct:free,"
            "nvidia/nemotron-3-super-120b-a12b:free,"
            "google/gemma-3-27b-it:free",
        )
        self.fallbacks = [m.strip() for m in fallbacks.split(",") if m.strip()]

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, user: str, *, temperature: float = 0.7, max_tokens: int = 8000) -> str:
        if not self.configured:
            raise SystemExit(
                "OPENROUTER_API_KEY is required for podcast-studio agents. "
                "export OPENROUTER_API_KEY=sk-or-…"
            )
        models = [self.model] + [m for m in self.fallbacks if m != self.model]
        # de-dupe preserve order
        seen: set[str] = set()
        models = [m for m in models if not (m in seen or seen.add(m))]
        last_err: Exception | None = None
        for model in models:
            try:
                text = self._once(model, system, user, temperature=temperature, max_tokens=max_tokens)
                if model != self.model:
                    print(f"  (llm fallback ok: {model})")
                return text
            except Exception as exc:  # noqa: BLE001 — try next model
                last_err = exc
                print(f"  (llm miss {model}: {exc})")
                continue
        raise SystemExit(f"All OpenRouter models failed: {last_err}")

    def _once(self, model: str, system: str, user: str, *, temperature: float, max_tokens: int) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "http://localhost:4173"),
                "X-Title": "Meridian IAM Podcast Studio",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"{model} HTTP {exc.code}: {body}") from exc
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected OpenRouter payload: {repr(data)[:400]}") from exc
