"""cedx/agents/verifier.py — role: verifier. Independent agent-checks-agent gate.

It did NOT write the draft. It re-derives the verdict from the source and can
OVERRULE the worker. Beyond trusting the model's verdict, it runs a deterministic
cross-check: any delivered field that contradicts the source forces a 'fail'
(this is what catches AGENT_HALLUCINATION, verify_audit.py check #15).
"""
from __future__ import annotations

import json
from pathlib import Path

from cedx.agents.base import cost_of, span
from cedx.config import Config
from cedx.contracts import AgentSpan, SpanStatus, Tier, Verdict, VerifierIn, VerifierOut
from cedx.llm import client
from cedx.llm.replay import Replayer, write_transcript

_PROMPT = (Path(__file__).parent.parent / "prompts" / "verifier_v1.txt").read_text()
PROMPT_VERSION = "verifier_v1"

# delivered memo field -> source attribute it must agree with (single source of truth)
from cedx.branding import MEMO_FIELDS as _GROUNDED


def check(cfg: Config, vi: VerifierIn, tier: Tier, replayer: Replayer | None,
          transcripts_dir: str = "transcripts") -> tuple[VerifierOut, AgentSpan]:
    src = vi.source
    df = vi.draft.delivered_fields
    payload = {
        "source": {"id": src.id, "owner": src.owner, "deadline": src.deadline,
                   "category": src.category, "amount": src.amount, "notes": src.notes},
        "draft": df,
    }
    request = client.build_request(vi.model, PROMPT_VERSION, _PROMPT, payload)
    response = client.complete(cfg, "verifier", request, replayer)
    if not cfg.replay_llm:          # record verifier transcript so replay is deterministic
        write_transcript(transcripts_dir, "verifier", vi.model, PROMPT_VERSION,
                         request, response, {})

    try:
        parsed = json.loads(response["content"])
        verdict = Verdict(parsed["verdict"])
        findings = list(parsed.get("findings", []))
        overruled = list(parsed.get("overruled_fields", []))
        reason = parsed.get("reason", "")
    except (KeyError, ValueError, TypeError):
        verdict, findings, overruled, reason = (
            Verdict.needs_human, ["verifier output unparseable"], [], "malformed verifier output")

    # deterministic hallucination cross-check (overrules a too-lenient model)
    grounding_fail = []
    for k, src_attr in _GROUNDED.items():
        if k in df:
            src_val = getattr(src, src_attr)
            if src_val is not None and str(df[k]) != str(src_val):
                grounding_fail.append(k)
    if grounding_fail:
        verdict = Verdict.fail
        overruled = sorted(set(overruled) | set(grounding_fail))
        findings.append(f"unsupported/contradicted fields: {grounding_fail}")
        reason = "verifier overruled worker: delivered fields not grounded in source"

    usage = response.get("usage", {})
    tin, tout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

    status = SpanStatus.ok if verdict == Verdict.passed else (
        SpanStatus.overruled if grounding_fail else SpanStatus.rejected)
    sp = span("verifier", status, model=vi.model, prompt_version=PROMPT_VERSION,
              tokens_in=tin, tokens_out=tout, cost_usd=cost_of(cfg, tier, tin, tout),
              retries=0, verdict=verdict)
    out = VerifierOut(record_id=src.id, verdict=verdict, overruled_fields=overruled,
                      findings=findings, reason=reason)
    return out, sp
