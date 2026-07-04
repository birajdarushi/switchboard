"""cedx/normalize/field_map.py — declarative alias -> canonical field mapping.

This is the single place field renames are handled. When a source uses an alias
(e.g. `Value:` instead of `Amount:`), we map it to canonical AND flag SCHEMA_DRIFT.
Keeping this declarative (a dict, not scattered if-statements) is what the brief
means by "declarative normalization to a versioned artifact".
"""
from __future__ import annotations

SCHEMA_VERSION = "canonical_v1"

# canonical field -> set of accepted source aliases (all lowercased)
ALIASES: dict[str, set[str]] = {
    "id": {"id", "record_id", "ref"},
    "owner": {"owner", "assignee", "owned_by"},
    "deadline": {"deadline", "due", "due_date"},
    "category": {"category", "type", "kind"},
    "amount": {"amount", "value", "amt", "total"},
    "notes": {"notes", "note", "comment", "comments"},
    "version": {"version", "ver", "rev"},
}

# reverse lookup: alias -> canonical
_REVERSE = {alias: canon for canon, al in ALIASES.items() for alias in al}

# the "primary" (non-renamed) key for each canonical field — anything else is drift
PRIMARY = {canon: canon for canon in ALIASES}


def canonical_key(raw_key: str) -> str | None:
    return _REVERSE.get(raw_key.strip().lower())


def is_drifted(raw_key: str) -> bool:
    """True if this source key is a non-primary alias (field was renamed)."""
    k = raw_key.strip().lower()
    canon = _REVERSE.get(k)
    return canon is not None and k != PRIMARY.get(canon)
