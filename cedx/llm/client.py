"""cedx/llm/client.py — the ONLY place a model call happens.

Three paths:
  REPLAY_LLM=true            → replay a committed transcript (default, offline, graded)
  REPLAY_LLM=false + key     → real OpenAI-compatible call (load-bearing, held-out run)
  REPLAY_LLM=false, no key,
    ALLOW_FAKE_LLM=1         → deterministic dev generator to RECORD fixtures only

The dev generator is gated behind ALLOW_FAKE_LLM so it can never silently stand in
for a real model during grading. On the graded real run, graders set a real key.
"""
from __future__ import annotations

import json
import os
import urllib.request

from cedx.config import Config
from cedx.llm.replay import Replayer


def build_request(model: str, prompt_version: str, system: str, payload: dict) -> dict:
    """Canonical request dict — identical at record-time and replay-time."""
    return {
        "model": model,
        "prompt_version": prompt_version,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload, sort_keys=True, ensure_ascii=False)},
        ],
    }


def complete(cfg: Config, agent: str, request: dict, replayer: Replayer | None) -> dict:
    """Return the response dict {'content': <json str>, 'usage': {...}}."""
    if cfg.replay_llm:
        assert replayer is not None
        return replayer.get(agent, request)["response"]
    if cfg.llm_api_key:
        return _real_call(cfg, request)
    if os.environ.get("ALLOW_FAKE_LLM"):
        return _fake(agent, request)
    raise RuntimeError(
        "No LLM available. Use REPLAY_LLM=true (default), or set LLM_API_KEY for the "
        "real path, or ALLOW_FAKE_LLM=1 to record dev fixtures.")


def _real_call(cfg: Config, request: dict) -> dict:
    body = json.dumps({
        "model": request["model"],
        "messages": request["messages"],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(
        cfg.llm_base_url.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {cfg.llm_api_key}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return {
        "content": data["choices"][0]["message"]["content"],
        "usage": data.get("usage", {}),
    }


def _fake(agent: str, request: dict) -> dict:
    """Deterministic local generator (fixtures only). Grounds output in the payload.

    Responses are tagged with the record id via `_rid` so distinct records never
    collide on response_hash (which is the transcript filename). Real model responses
    vary per record naturally; this reproduces that for offline fixtures.
    """
    payload = json.loads(request["messages"][-1]["content"])
    rid = None
    if agent == "worker":
        rec = payload["record"]
        rid = rec.get("id")
        # ambiguous records → abstain (drives LOW_CONFIDENCE)
        ambiguous = _looks_ambiguous(rec)
        # PROBE-ONLY: ids prefixed PROBE-HALLUC make the worker fabricate an amount
        # (not grounded in source) so probe-agent-failure can prove the Verifier catch.
        if str(rid).startswith("PROBE-HALLUC"):
            content = {"delivered_fields": {
                "package_id": rec["id"], "owner": rec["owner"],
                "category": rec["category"],
                "amount": (rec["amount"] or 0) + 999999,   # fabricated / unsupported
                "deadline": rec["deadline"], "brand": payload.get("brand", "CEDX")},
                "confidence": 0.95, "abstain": False}
        elif ambiguous:
            content = {"delivered_fields": {}, "confidence": 0.3, "abstain": True}
        else:
            content = {
                "delivered_fields": {
                    "package_id": rec["id"],
                    "owner": rec["owner"],
                    "category": rec["category"],
                    "amount": rec["amount"],
                    "deadline": rec["deadline"],
                    "brand": payload.get("brand", "CEDX"),
                    "summary": f"{rec['category']} package for {rec['owner']} (amount {rec['amount']}).",
                },
                "confidence": 0.95,
                "abstain": False,
            }
        toks_out = 80
    elif agent == "verifier":
        rid = payload.get("source", {}).get("id")
        content = {"verdict": "pass", "overruled_fields": [], "findings": [],
                   "reason": "all delivered fields trace to source"}
        toks_out = 30
    elif agent == "judge":
        rid = payload.get("source", {}).get("id")
        content = _fake_judge(payload)
        toks_out = 25
    else:
        content = {}
        toks_out = 10
    return {"content": json.dumps(content, sort_keys=True),
            "usage": {"prompt_tokens": 120, "completion_tokens": toks_out},
            "_rid": rid}


def _fake_judge(payload: dict) -> dict:
    """Deterministic offline judge (rubric). Real path uses a real LLM via _real_call."""
    role = payload.get("agent_role")
    src = payload.get("source", {})
    out = payload.get("output", {})
    if role == "worker":
        df = out.get("delivered_fields", {})
        if out.get("abstain"):
            return {"score": 1.0 if _looks_ambiguous(src) else 0.0,
                    "reason": "abstain appropriate for ambiguity"}
        grounded = all(str(df.get(k)) == str(src.get(k))
                       for k in ("owner", "category", "amount", "deadline") if k in df)
        return {"score": 1.0 if grounded else 0.0,
                "reason": "all fields grounded" if grounded else "ungrounded field"}
    if role == "verifier":
        # verdict should be pass for grounded drafts, fail otherwise
        return {"score": 1.0 if out.get("verdict") in ("pass", "fail", "needs_human") else 0.0,
                "reason": "verdict well-formed and decisive"}
    if role == "router":
        big = (src.get("amount") or 0) >= 100000
        tier = out.get("tier")
        ok = (tier == "strong") if big else (tier == "cheap")
        return {"score": 1.0 if ok else 0.0, "reason": f"tier {tier} appropriate"}
    return {"score": 0.0, "reason": "unknown agent role"}


def _looks_ambiguous(rec: dict) -> bool:
    cat = (rec.get("category") or "").strip()
    notes = (rec.get("notes") or "").lower()
    if cat in {"", "?"}:
        return True
    signals = ["unclear", "could be", "inconsistent", "not attached",
               "describes a renewal and a report", "ambiguous"]
    return any(s in notes for s in signals)
