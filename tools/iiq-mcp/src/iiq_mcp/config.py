"""Environment-driven configuration for the IIQ MCP server."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings loaded from environment / optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    iiq_base_url: str = Field(
        default="http://localhost:8080/identityiq",
        alias="IIQ_BASE_URL",
    )
    iiq_user: str = Field(default="spadmin", alias="IIQ_USER")
    iiq_password: str = Field(default="", alias="IIQ_PASSWORD")

    mcp_host: str = Field(default="127.0.0.1", alias="MCP_HOST")
    mcp_port: int = Field(default=8766, alias="MCP_PORT")
    mcp_api_key: str = Field(default="", alias="MCP_API_KEY")
    mcp_path: str = Field(default="/mcp", alias="MCP_PATH")

    iiq_mcp_enabled_phases: str = Field(default="1", alias="IIQ_MCP_ENABLED_PHASES")
    iiq_mcp_max_rps: float = Field(default=5.0, alias="IIQ_MCP_MAX_RPS")
    iiq_mcp_max_concurrent: int = Field(default=4, alias="IIQ_MCP_MAX_CONCURRENT")
    iiq_mcp_audit_log: Path = Field(
        default=Path("./var/mcp-write-audit.jsonl"),
        alias="IIQ_MCP_AUDIT_LOG",
    )
    iiq_mcp_idempotency_db: Path = Field(
        default=Path("./var/mcp-idempotency.sqlite"),
        alias="IIQ_MCP_IDEMPOTENCY_DB",
    )
    iiq_mcp_default_page_size: int = Field(default=25, alias="IIQ_MCP_DEFAULT_PAGE_SIZE")
    iiq_mcp_max_page_size: int = Field(default=100, alias="IIQ_MCP_MAX_PAGE_SIZE")
    iiq_mcp_http_timeout_seconds: float = Field(
        default=60.0, alias="IIQ_MCP_HTTP_TIMEOUT_SECONDS"
    )

    @field_validator("iiq_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    def enabled_phases(self) -> set[int]:
        """Parse comma-separated phase numbers (e.g. ``1`` or ``1,2``)."""
        phases: set[int] = set()
        for part in self.iiq_mcp_enabled_phases.split(","):
            part = part.strip()
            if not part:
                continue
            phases.add(int(part))
        return phases or {1}

    def phase_enabled(self, phase: int) -> bool:
        return phase in self.enabled_phases()


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
