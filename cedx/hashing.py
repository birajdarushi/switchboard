"""cedx/hashing.py — canonical hashing.

MUST byte-match verify_audit.py's canon()/sha() (lines 62-67 of that file), or
delivered records fail gate checks 8 & 14. Do not "improve" the canonicalization.
"""
from __future__ import annotations
import hashlib
import json


def canon(obj) -> bytes:
    """Identical to verify_audit.py: sorted keys, no spaces, unicode preserved."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha(obj) -> str:
    """sha256 of the canonical JSON of a Python object, prefixed 'sha256:'."""
    return "sha256:" + hashlib.sha256(canon(obj)).hexdigest()


def sha_bytes(raw: bytes) -> str:
    """sha256 of raw bytes (used for source_version_hash of the original file)."""
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def hex_of(h: str) -> str:
    """'sha256:abc' -> 'abc'."""
    return h.split(":")[-1]
