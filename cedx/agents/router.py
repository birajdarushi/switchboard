"""cedx/agents/router.py — role: router. Deterministic model selection + budget.

Policy (justified in DECISIONS.md): default to the CHEAP model; escalate to STRONG
only when the record is hard — a retry, a verifier-flagged record, or an unusually
large amount. Raise BUDGET_EXCEEDED if even the cheap attempt would blow the ceiling.
No LLM call here — this agent is pure logic, so it is trivially testable and cheap.
"""
from __future__ import annotations

from cedx.config import Config
from cedx.contracts import RouterIn, RouterOut, Tier


def decide(cfg: Config, ri: RouterIn) -> RouterOut:
    escalate = ri.verifier_flagged or ri.attempt > 0 or (ri.amount or 0) >= 100000
    tier = Tier.strong if escalate else Tier.cheap
    model = cfg.strong_model if escalate else cfg.cheap_model
    price = cfg.price_strong_per_1k if escalate else cfg.price_cheap_per_1k

    # rough estimate: ~200 tokens/call at this price
    est = round(200 / 1000.0 * price, 8)

    reason = ("escalate: " + ",".join(
        [s for s, c in [("retry", ri.attempt > 0),
                        ("verifier_flag", ri.verifier_flagged),
                        ("large_amount", (ri.amount or 0) >= 100000)] if c])
    ) if escalate else "default cheap model"

    budget_exceeded = (ri.steps_used >= cfg.max_steps_per_record
                       or est > ri.budget_remaining_usd)

    return RouterOut(model=model, tier=tier, reason=reason,
                     est_cost_usd=est, budget_exceeded=budget_exceeded)
