"""OpenAI-compatible Chat Completions providers (config-swappable)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


class LlmError(RuntimeError):
    pass


PROVIDER_DEFAULTS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
    },
    "azure_openai": {
        "base_url": None,  # must set llm.base_url
        "api_key_env": "AZURE_OPENAI_API_KEY",
    },
    "gemini_openai_compat": {
        # Google OpenAI-compatible endpoint; set base_url if different
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key_env": "GOOGLE_API_KEY",
    },
}


@dataclass
class LlmProvider:
    provider: str
    model: str
    api_key: str
    base_url: str
    fallback_models: list[str] = field(default_factory=list)
    referer: str = "http://localhost:4180"
    title: str = "Meridian Auto-story"

    @classmethod
    def from_config(cls, cfg: dict[str, Any], api_key: str | None = None) -> "LlmProvider":
        llm = cfg.get("llm") or {}
        provider = str(llm.get("provider") or "openrouter").lower()
        defaults = PROVIDER_DEFAULTS.get(provider) or PROVIDER_DEFAULTS["openrouter"]
        base = llm.get("base_url") or defaults.get("base_url")
        if not base:
            raise LlmError(f"llm.base_url required for provider={provider}")
        key_env = llm.get("api_key_env") or defaults.get("api_key_env") or "OPENROUTER_API_KEY"
        key = (api_key if api_key is not None else os.environ.get(key_env, "")).strip()
        return cls(
            provider=provider,
            model=str(llm.get("model") or "openrouter/free"),
            api_key=key,
            base_url=str(base),
            fallback_models=list(llm.get("fallback_models") or []),
            referer=str(llm.get("referer") or "http://localhost:4180"),
            title=str(llm.get("title") or "Meridian Auto-story"),
        )

    def chat_completions(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise LlmError(f"API key missing for provider={self.provider}")
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        data = json.dumps(body).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = self.referer
            headers["X-Title"] = self.title
        req = urllib.request.Request(self.base_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:600]
            raise LlmError(f"LLM HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LlmError(f"LLM unreachable: {exc}") from exc
