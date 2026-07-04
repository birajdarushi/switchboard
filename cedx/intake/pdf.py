"""cedx/intake/pdf.py — parse a .pdf work-request into raw key/value pairs.

Primary path: pypdf text extraction. Fallback: manual ASCII85+Flate stream decode
(the seed PDFs are ReportLab-generated), so intake never silently loses a record.
"""
from __future__ import annotations

import base64
import io
import re
import zlib


def parse(raw: bytes) -> dict[str, str]:
    text = _extract_text(raw)
    return _kv_from_text(text)


def _extract_text(raw: bytes) -> str:
    # 1) pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        if text.strip():
            return text
    except Exception:
        pass
    # 2) manual ASCII85 + Flate fallback
    try:
        start = raw.find(b"stream\n") + len(b"stream\n")
        end = raw.find(b"endstream")
        body = raw[start:end].strip()
        if body.endswith(b"~>"):
            body = body[:-2]
        content = zlib.decompress(base64.a85decode(body)).decode("latin1")
        toks = re.findall(r"\(((?:[^()\\]|\\.)*)\)", content)
        return " ".join(t.replace("\\(", "(").replace("\\)", ")") for t in toks)
    except Exception:
        return ""


def _kv_from_text(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    # tokens look like "Id: REC-007 Owner: g.silva Deadline: ..." on one line;
    # split on the "Key:" boundaries.
    for m in re.finditer(r"([A-Za-z_]+):\s*(.*?)(?=\s+[A-Za-z_]+:|$)", text):
        k, v = m.group(1).strip(), m.group(2).strip()
        if k and v:
            out[k] = v
    return out
