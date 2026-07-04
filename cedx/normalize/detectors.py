"""cedx/normalize/detectors.py — STAGE (2) data-layer detectors (the ⑤ routing tree).

All detection is RULE-BASED and computed from the batch, never hardcoded to seed
values — this is what lets it generalize to the held-out seed. Precedence:
  injection > missing > stale > outlier
Class-B repairs (schema_drift, supersede) are handled in the loader / dedup, not here.
"""
from __future__ import annotations

import re
import statistics
from datetime import date

from cedx.contracts import CanonicalRecord, ReasonCode

# Imperative patterns aimed at the pipeline (prompt injection). Generalized, not
# tied to REC-014's exact wording, so it also catches REC-022's "ignore the field".
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|your)\s+(instructions|rules)",
    r"ignore\s+the\s+\w+\s+(field|value|amount)",
    r"approve\s+(this\s+)?(immediately|now)",
    r"skip\s+(the\s+)?review",
    r"output\s+approved",
    r"disregard\s+(the\s+)?(above|rules|instructions)",
    r"do\s+not\s+(review|verify|check)",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# robust-z cutoff; 3.5 ≈ 0.05% false-positive under normality (justified in DECISIONS.md)
OUTLIER_Z = 3.5


def detect_injection(notes: str) -> bool:
    return bool(_INJECTION_RE.search(notes or ""))


def detect_missing(record: CanonicalRecord) -> bool:
    # amount is the required primary numeric field; owner/deadline are required too.
    return record.amount is None or not record.owner or not record.deadline


def detect_stale(record: CanonicalRecord, now: str) -> bool:
    if not record.deadline:
        return False
    try:
        return date.fromisoformat(record.deadline) < date.fromisoformat(now)
    except ValueError:
        return False


def outlier_ids(records: list[CanonicalRecord]) -> set[str]:
    """Robust MAD-based outlier detection over the batch's non-null amounts."""
    amounts = [(r.id, r.amount) for r in records if r.amount is not None]
    vals = [a for _, a in amounts]
    if len(vals) < 3:
        return set()
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals])
    if mad == 0:
        return set()
    out = set()
    for rid, v in amounts:
        robust_z = 0.6745 * (v - med) / mad
        if abs(robust_z) > OUTLIER_Z:
            out.add(rid)
    return out


def classify(record: CanonicalRecord, now: str, outliers: set[str]) -> ReasonCode | None:
    """Apply data-layer precedence. Returns a blocking ReasonCode or None (clean)."""
    if detect_injection(record.notes):
        return ReasonCode.INJECTION_BLOCKED
    if detect_missing(record):
        return ReasonCode.MISSING_INPUT
    if detect_stale(record, now):
        return ReasonCode.STALE
    if record.id in outliers:
        return ReasonCode.OUTLIER
    return None
