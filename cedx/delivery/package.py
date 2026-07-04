"""cedx/delivery/package.py — build the branded output package + its hash.

The package is the customer-facing artifact (all delivered records). Its sha256 is
recorded as audit.output_package_hash (verify_audit.py check #3).
"""
from __future__ import annotations

import json
from pathlib import Path

from cedx.config import Config
from cedx.hashing import sha


def build_package(cfg: Config, delivered: list[dict], out_dir: str) -> str:
    package = {
        "brand": cfg.brand,
        "industry": cfg.industry,
        "case_id": cfg.case_id,
        "items": delivered,
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "package.json").write_text(
        json.dumps(package, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return sha(package)
