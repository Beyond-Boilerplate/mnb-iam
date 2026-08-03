"""Load auto-story config.yaml with env overrides (stdlib YAML subset if no PyYAML)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
DEFAULT_CONFIG = PKG / "config.yaml"


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VAL from scripts/auto_story/.env into os.environ (no overwrite)."""
    env_path = path or (PKG / ".env")
    if not env_path.is_file():
        # Fall back to Teller .env
        alt = ROOT / "tools" / "iiq-chat" / ".env"
        env_path = alt if alt.is_file() else env_path
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val


try:
    import yaml as _yaml
except ImportError:  # pragma: no cover
    _yaml = None


def _parse_scalar(s: str) -> Any:
    s = s.strip()
    if s in ("null", "~", ""):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    # strip inline comments
    if " #" in s:
        s = s.split(" #", 1)[0].rstrip()
    return s


def _minimal_yaml_load(text: str) -> dict[str, Any]:
    """Parse indent-based maps/lists sufficient for config.yaml."""
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    i = 0
    while i < len(lines):
        indent, content = lines[i]
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if content.startswith("- "):
            item_raw = content[2:].strip()
            if not isinstance(parent, list):
                raise ValueError(f"List item without list parent: {content}")
            if ":" in item_raw and not item_raw.startswith("'") and not item_raw.startswith('"'):
                # map item
                k, _, v = item_raw.partition(":")
                obj: dict[str, Any] = {k.strip(): _parse_scalar(v)}
                parent.append(obj)
                stack.append((indent, obj))
            else:
                parent.append(_parse_scalar(item_raw))
            i += 1
            continue

        if ":" not in content:
            raise ValueError(f"Cannot parse line: {content}")
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()

        if rest in (">", ">-", "|", "|-"):
            # folded / literal block: collect following more-indented lines
            block_lines: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j][0] > indent:
                block_lines.append(lines[j][1])
                j += 1
            val = " ".join(block_lines) if rest.startswith(">") else "\n".join(block_lines)
            if not isinstance(parent, dict):
                raise ValueError("Mapping key under non-dict")
            parent[key] = val
            i = j
            continue

        if rest == "":
            # peek next
            if i + 1 < len(lines) and lines[i + 1][0] > indent and lines[i + 1][1].startswith("- "):
                child: Any = []
            else:
                child = {}
            if not isinstance(parent, dict):
                raise ValueError("Mapping key under non-dict")
            parent[key] = child
            stack.append((indent, child))
            i += 1
            continue

        if not isinstance(parent, dict):
            raise ValueError("Mapping key under non-dict")
        parent[key] = _parse_scalar(rest)
        i += 1

    return root


def load_config(path: Path | None = None) -> dict[str, Any]:
    load_dotenv()
    cfg_path = path or Path(os.environ.get("AUTO_STORY_CONFIG") or DEFAULT_CONFIG)
    raw = cfg_path.read_text(encoding="utf-8")
    if _yaml is not None:
        data = _yaml.safe_load(raw) or {}
    else:
        data = _minimal_yaml_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {cfg_path}")
    data["_config_path"] = str(cfg_path)
    data["_repo_root"] = str(ROOT)
    return data


def resolve_path(cfg: dict[str, Any], rel: str) -> Path:
    root = Path(cfg.get("_repo_root") or ROOT)
    p = Path(rel)
    return p if p.is_absolute() else root / p


def llm_api_key(cfg: dict[str, Any]) -> str:
    env_name = (cfg.get("llm") or {}).get("api_key_env") or "OPENROUTER_API_KEY"
    return os.environ.get(env_name, "").strip()


def jira_creds(cfg: dict[str, Any]) -> tuple[str, str, str]:
    j = cfg.get("jira") or {}
    site = os.environ.get(j.get("site_env") or "JIRA_SITE", "").strip().rstrip("/")
    email = (
        os.environ.get(j.get("bot_email_env") or "JIRA_BOT_EMAIL", "").strip()
        or os.environ.get(j.get("email_env") or "JIRA_EMAIL", "").strip()
    )
    token = os.environ.get(j.get("token_env") or "JIRA_API_TOKEN", "").strip()
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        token = token[1:-1]
    return site, email, token


def mcp_url(cfg: dict[str, Any]) -> str:
    a = cfg.get("agent") or {}
    env = a.get("mcp_url_env") or "IIQ_MCP_URL"
    return (os.environ.get(env) or a.get("mcp_url_default") or "http://127.0.0.1:8766/mcp").rstrip(
        "/"
    )


def mcp_api_key(cfg: dict[str, Any]) -> str:
    a = cfg.get("agent") or {}
    env = a.get("mcp_api_key_env") or "MCP_API_KEY"
    key = os.environ.get(env) or os.environ.get("IIQ_MCP_API_KEY") or ""
    if key:
        return key
    # Lab docker-compose default when unset
    return str(a.get("mcp_api_key_default") or "mnb-lab-mcp-key")
