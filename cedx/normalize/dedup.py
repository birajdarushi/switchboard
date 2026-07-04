"""cedx/normalize/dedup.py — SUPERSEDED_VERSION handling (Class B, auto-resolved).

Same id seen more than once → keep the highest version as active, mark the older
one(s) superseded and logged. Never silently drop data.
"""
from __future__ import annotations

from dataclasses import dataclass

from cedx.intake import IntakeItem


@dataclass
class DedupResult:
    active: list[IntakeItem]              # highest-version item per id
    superseded: list[IntakeItem]          # older versions (status=superseded)


def dedup(items: list[IntakeItem]) -> DedupResult:
    by_id: dict[str, list[IntakeItem]] = {}
    for it in items:
        by_id.setdefault(it.record.id, []).append(it)

    active: list[IntakeItem] = []
    superseded: list[IntakeItem] = []
    for _id, group in by_id.items():
        group.sort(key=lambda it: it.record.version)
        active.append(group[-1])
        superseded.extend(group[:-1])
    return DedupResult(active=active, superseded=superseded)
