"""cedx/intake/eml.py — parse a .eml work-request into raw key/value pairs.

The body is simple `Key: Value` lines. We return the raw dict; canonical mapping
(and SCHEMA_DRIFT flagging) happens in the loader via field_map.
"""
from __future__ import annotations

from email import policy
from email.parser import BytesParser


def parse(raw: bytes) -> dict[str, str]:
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    body = msg.get_body(preferencelist=("plain",))
    text = body.get_content() if body else msg.get_content()
    return _kv_lines(text)


def _kv_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if k and v:
                out[k] = v
    return out
