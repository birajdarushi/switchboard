"""cedx/llm/replay.py — committed-transcript IO for deterministic offline replay.

Filenames are keyed by response_hash (gate requirement, verify_audit.py check #8),
but the in-memory replay index is keyed by sha(request) so a given agent call maps
to its stored response. Both derive from the same committed files — no conflict.
"""
from __future__ import annotations

import json
from pathlib import Path

from cedx.hashing import sha, hex_of


class Replayer:
    def __init__(self, tdir: str):
        self.tdir = Path(tdir)
        self.by_request: dict[str, dict] = {}
        if self.tdir.exists():
            for tf in self.tdir.glob("*.json"):
                try:
                    t = json.loads(tf.read_text(encoding="utf-8"))
                except Exception:
                    continue
                self.by_request[sha(t["request"])] = t

    def get(self, agent: str, request: dict) -> dict:
        t = self.by_request.get(sha(request))
        if t is None:
            raise KeyError(f"no committed transcript for a {agent} request "
                           f"(run `make record` to generate fixtures)")
        if t.get("agent") != agent:
            raise KeyError(f"transcript agent {t.get('agent')!r} != caller {agent!r}")
        return t


def write_transcript(tdir: str, agent: str, model: str, prompt_version: str,
                     request: dict, response: dict, delivered_fields: dict) -> tuple[str, str]:
    """Persist one transcript as transcripts/<response_hex>.json. Returns (rh, dfh)."""
    rh = sha(response)
    dfh = sha(delivered_fields)
    t = {
        "agent": agent,
        "model": model,
        "prompt_version": prompt_version,
        "request": request,
        "response": response,
        "response_hash": rh,
        "delivered_fields_hash": dfh,
    }
    p = Path(tdir)
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{hex_of(rh)}.json").write_text(
        json.dumps(t, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return rh, dfh
