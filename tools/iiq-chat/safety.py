"""Write/mutate tool classification for Teller safety gates."""

from __future__ import annotations

# Name fragments that usually mean a side-effecting MCP tool.
_WRITE_FRAGMENTS = (
    "unlock",
    "disable",
    "enable",
    "password",
    "reset",
    "trigger",
    "aggregat",
    "create",
    "delete",
    "remove",
    "update",
    "set_",
    "assign",
    "revoke",
    "provision",
    "approve",
    "reject",
    "launch",
    "run_",
    "start_",
    "stop_",
    "import",
    "export_object",  # export alone may be read; export_object often writes files
    "move",
    "terminate",
    "refresh_identity",
    "correlate",
    "certify",
    "sign_off",
    "bulk_",
    "write",
    "mutate",
    "patch",
    "put_",
    "post_",
)

# Strong read signals — win when both match (e.g. list_triggered_*)
_READ_PREFIXES = (
    "list_",
    "get_",
    "search_",
    "count_",
    "find_",
    "describe_",
    "ping",
    "health",
    "status",
    "preview_",
    "diff_",
    "show_",
)


def is_write_tool(name: str) -> bool:
    """Heuristic: True if calling this MCP tool likely mutates IIQ state."""
    n = (name or "").strip().lower()
    if not n:
        return False
    if n.startswith(_READ_PREFIXES) or n in {"toolkit_ping", "iiq_ping"}:
        # list_/get_ of something with "trigger" in the name stay reads
        if n.startswith(("list_", "get_", "search_", "count_", "find_", "describe_")):
            return False
    return any(frag in n for frag in _WRITE_FRAGMENTS)
