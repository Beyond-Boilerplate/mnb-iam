#!/usr/bin/env python3
"""Shared paths for Meridian IIQ delivery helpers."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DELIVERY_ROOT = REPO_ROOT / ".ai-delivery"
MEMORY_ROOT = DELIVERY_ROOT / "_memory"
GOTCHAS = MEMORY_ROOT / "GOTCHAS.md"
STATE_DIR = DELIVERY_ROOT / "_state"
MCP_URL = "http://127.0.0.1:8766/mcp"
IIQ_BASE = "http://localhost:8080/identityiq"

VALID_WORK_TYPES = (
    "ui-branding",
    "app-onboarding",
    "identity-admin",
    "access-request",
    "certification",
    "policy-sod",
    "jml-lifecycle",
    "task-ops",
    "automation-rule-workflow",
    "plugin-work",
    "governance-admin",
    "investigation",
)


def memory_dir(skill: str) -> Path:
    return MEMORY_ROOT / skill
