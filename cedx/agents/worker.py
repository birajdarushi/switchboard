"""cedx/agents/worker.py — role: worker. The LLM-heavy Assembly draft.

Produces the load-bearing transcript (tagged agent='worker') that verify_audit.py
checks #8 & #14 hash against. On malformed model output it raises MalformedOutput
so the orchestrator can bound-retry then route to AGENT_MALFORMED.
"""
from __future__ import annotations

import json
from pathlib import Path

from cedx.agents.base import cost_of, span, _Timer
from cedx.config import Config
from cedx.contracts import AgentSpan, SpanStatus, Tier, WorkerIn, WorkerOut
from cedx.hashing import sha
from cedx.llm import client
from cedx.llm.replay import Replayer, write_transcript

_PROMPT = (Path(__file__).parent.parent / "prompts" / "worker_v1.txt").read_text()
PROMPT_VERSION = "worker_v1"


class MalformedOutput(Exception):
    pass


def draft(cfg: Config, wi: WorkerIn, tier: Tier, replayer: Replayer | None,
          transcripts_dir: str = "transcripts") -> tuple[WorkerOut, AgentSpan]:
    rec = wi.record
    payload = {
        "record": {"id": rec.id, "owner": rec.owner, "deadline": rec.deadline,
                   "category": rec.category, "amount": rec.amount, "notes": rec.notes},
        "brand": cfg.brand, "industry": cfg.industry,
    }
    request = client.build_request(wi.model, PROMPT_VERSION, _PROMPT, payload)

    with _Timer() as t:
        response = client.complete(cfg, "worker", request, replayer)

    try:
        parsed = json.loads(response["content"])
        delivered_fields = dict(parsed["delivered_fields"])
        confidence = float(parsed["confidence"])
        abstain = bool(parsed.get("abstain", False))
    except (KeyError, ValueError, TypeError) as e:
        raise MalformedOutput(f"worker output not valid: {e}")

    usage = response.get("usage", {})
    tin, tout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

    rh = sha(response)
    dfh = sha(delivered_fields)
    if not cfg.replay_llm:                    # record fixtures on real / fake paths
        write_transcript(transcripts_dir, "worker", wi.model, PROMPT_VERSION,
                         request, response, delivered_fields)

    out = WorkerOut(record_id=rec.id, delivered_fields=delivered_fields,
                    confidence=confidence, abstain=abstain, transcript_hash=rh)
    sp = span("worker", SpanStatus.abstained if abstain else SpanStatus.ok,
              model=wi.model, prompt_version=PROMPT_VERSION,
              tokens_in=tin, tokens_out=tout, cost_usd=cost_of(cfg, tier, tin, tout),
              latency_ms=round(t.ms, 3), retries=0, transcript_hash=rh)
    return out, sp
