"""cedx/evaluation.py — `make eval`. Golden cases + an LLM-judge per agent.

Golden cases: deterministic end-to-end assertions on known dev-seed outcomes.
LLM-judge: scores each agent's output quality via the judge prompt (a real LLM on
the keyed path; a deterministic rubric offline). Prints per-agent scores.
"""
from __future__ import annotations

import dataclasses
import json
import os
import tempfile
from pathlib import Path

from cedx.agents import router as router_agent
from cedx.agents import verifier as verifier_agent
from cedx.agents import worker as worker_agent
from cedx.agents.base import roster
from cedx.agents.orchestrator import Orchestrator
from cedx.audit.log import EventLog
from cedx.config import Config
from cedx.contracts import RouterIn, Tier, VerifierIn, WorkerIn
from cedx.intake import load_records
from cedx.llm import client

_JUDGE = (Path(__file__).parent / "prompts" / "judge_v1.txt").read_text()

# ---- golden cases: (record_id, expected_status, expected_reason_code|None) ----
GOLDEN = [
    ("REC-001", "delivered", None),
    ("REC-002", "delivered", None),
    ("REC-007", "delivered", None),          # from PDF
    ("REC-016", "delivered", "SCHEMA_DRIFT"),
    ("REC-017", "delivered", None),          # v2 delivered
    ("REC-011", "exception", "STALE"),
    ("REC-012", "exception", "MISSING_INPUT"),
    ("REC-013", "exception", "OUTLIER"),
    ("REC-014", "exception", "INJECTION_BLOCKED"),
    ("REC-015", "exception", "LOW_CONFIDENCE"),
    ("REC-021", "exception", "LOW_CONFIDENCE"),
    ("REC-022", "exception", "INJECTION_BLOCKED"),
]


def _fake_cfg(cfg: Config) -> Config:
    os.environ["ALLOW_FAKE_LLM"] = "1"
    return dataclasses.replace(cfg, replay_llm=False)


def run_golden(cfg: Config):
    records, _ = Orchestrator(cfg).run(EventLog())
    # for a duplicated id (superseded+delivered) prefer the delivered/exception one
    by_id = {}
    for r in records:
        if r.id not in by_id or r.status.value != "superseded":
            by_id[r.id] = r
    passed, failures = 0, []
    for rid, exp_status, exp_reason in GOLDEN:
        r = by_id.get(rid)
        got_reason = r.reason_code.value if (r and r.reason_code) else None
        if r and r.status.value == exp_status and got_reason == exp_reason:
            passed += 1
        else:
            failures.append((rid, exp_status, exp_reason,
                             r.status.value if r else "MISSING", got_reason))
    return passed, len(GOLDEN), failures


def _judge(cfg_fake: Config, role: str, source: dict, output: dict) -> float:
    payload = {"agent_role": role, "source": source, "output": output}
    req = client.build_request(cfg_fake.cheap_model, "judge_v1", _JUDGE, payload)
    resp = client.complete(cfg_fake, "judge", req, None)
    try:
        return float(json.loads(resp["content"])["score"])
    except Exception:
        return 0.0


def run_judges(cfg: Config):
    cfg_fake = _fake_cfg(cfg)
    items = {it.record.id: it for it in load_records(cfg.seed_dir)}
    scores = {"worker": [], "verifier": [], "router": []}

    with tempfile.TemporaryDirectory() as td:
        for rid in ("REC-001", "REC-002", "REC-007", "REC-021"):   # incl. an ambiguous one
            rec = items[rid].record
            src = {"id": rec.id, "owner": rec.owner, "deadline": rec.deadline,
                   "category": rec.category, "amount": rec.amount, "notes": rec.notes}
            wout, _ = worker_agent.draft(
                cfg_fake, WorkerIn(record=rec, model=cfg.cheap_model,
                                   prompt_version="worker_v1"), Tier.cheap, None, td)
            scores["worker"].append(_judge(cfg_fake, "worker", src,
                {"delivered_fields": wout.delivered_fields, "abstain": wout.abstain}))
            if not wout.abstain:
                vout, _ = verifier_agent.check(
                    cfg_fake, VerifierIn(source=rec, draft=wout,
                                         model=cfg.cheap_model, prompt_version="verifier_v1"),
                    Tier.cheap, None, td)
                scores["verifier"].append(_judge(cfg_fake, "verifier", src,
                    {"verdict": vout.verdict.value}))

        for rid, amount in (("REC-001", 4800), ("REC-013", 250000)):    # cheap vs strong
            rdec = router_agent.decide(cfg, RouterIn(record_id=rid, amount=amount,
                budget_remaining_usd=cfg.max_cost_usd_per_record))
            scores["router"].append(_judge(cfg_fake, "router",
                {"id": rid, "amount": amount}, {"tier": rdec.tier.value}))

    return {k: (sum(v) / len(v) if v else 0.0) for k, v in scores.items()}


def run(cfg: Config) -> int:
    print("=== CEDX agent eval harness ===")
    passed, total, failures = run_golden(cfg)
    print(f"[golden] {passed}/{total} cases passed")
    for rid, es, er, gs, gr in failures:
        print(f"   FAIL {rid}: expected {es}/{er}, got {gs}/{gr}")

    judges = run_judges(cfg)
    print("[LLM-judge per agent]")
    for role, sc in judges.items():
        print(f"   {role:10} score={sc:.2f}")

    all_ok = (passed == total) and all(s >= 0.8 for s in judges.values())
    print("=== RESULT:", "PASS ===" if all_ok else "FAIL ===")
    return 0 if all_ok else 1
