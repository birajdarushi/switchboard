"""cedx/intake — STAGE (1). Parse BOTH formats into CanonicalRecords.

Reads SEED_DIR/feed.json + SEED_DIR/inbox/*.{eml,pdf}. No hardcoded in-memory
arrays: everything comes from the seed files. Emits a flat list of IntakeItem,
each carrying the canonical record + a schema_drift flag (set when a source used
a renamed field alias, e.g. `Value:` for amount).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cedx.contracts import CanonicalRecord, SourceFormat
from cedx.hashing import canon, sha_bytes
from cedx.normalize.field_map import canonical_key, is_drifted
from cedx.intake import eml as eml_mod
from cedx.intake import pdf as pdf_mod


@dataclass
class IntakeItem:
    record: CanonicalRecord
    schema_drift: bool


def _to_canonical(raw: dict, source_format: SourceFormat, svh: str,
                  fallback_id: str = "") -> IntakeItem:
    canon_fields: dict = {}
    drift = False
    for k, v in raw.items():
        ck = canonical_key(k)
        if ck is None:
            continue
        canon_fields[ck] = v
        if is_drifted(k):
            drift = True

    amount = canon_fields.get("amount")
    if isinstance(amount, str):
        try:
            amount = float(amount.replace(",", "").strip())
        except ValueError:
            amount = None
    elif amount is not None:
        amount = float(amount)

    version = canon_fields.get("version", 1)
    try:
        version = int(version)
    except (TypeError, ValueError):
        version = 1

    # If a source (esp. a corrupt/unparseable PDF/eml) yields no id, fall back to the
    # filename so the record stays traceable in the exception queue instead of blank.
    rec_id = str(canon_fields.get("id", "")).strip() or fallback_id
    rec = CanonicalRecord(
        id=rec_id,
        version=version,
        owner=canon_fields.get("owner"),
        deadline=canon_fields.get("deadline"),
        category=canon_fields.get("category"),
        amount=amount,
        notes=str(canon_fields.get("notes", "") or ""),
        source_format=source_format,
        source_version_hash=svh,
    )
    return IntakeItem(record=rec, schema_drift=drift)


def load_records(seed_dir: str) -> list[IntakeItem]:
    root = Path(seed_dir)
    items: list[IntakeItem] = []

    feed = root / "feed.json"
    if feed.exists():
        for raw in json.loads(feed.read_text(encoding="utf-8")):
            svh = sha_bytes(canon(raw))
            items.append(_to_canonical(raw, SourceFormat.feed, svh))

    inbox = root / "inbox"
    if inbox.exists():
        for f in sorted(inbox.iterdir()):
            raw_bytes = f.read_bytes()
            svh = sha_bytes(raw_bytes)
            if f.suffix == ".eml":
                items.append(_to_canonical(eml_mod.parse(raw_bytes), SourceFormat.eml, svh,
                                           fallback_id=f.stem))
            elif f.suffix == ".pdf":
                items.append(_to_canonical(pdf_mod.parse(raw_bytes), SourceFormat.pdf, svh,
                                           fallback_id=f.stem))

    return items
