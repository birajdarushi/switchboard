"""cedx/agents/base.py — shared agent scaffolding + the roster.

Each agent is a small, separately testable unit. The roster below is what appears
in audit.agents[] and is validated by verify_audit.py check #10 (>=3 agents incl.
orchestrator + worker + verifier; every can_call target must be a real agent).
"""
from __future__ import annotations

import time

from cedx.config import Config
from cedx.contracts import AgentInfo, AgentRole, AgentSpan, SpanStatus, Tier, Verdict


def roster(cfg: Config) -> list[AgentInfo]:
    return [
        AgentInfo(name="orchestrator", role=AgentRole.orchestrator, models=[],
                  can_call=["router", "worker", "verifier"]),
        AgentInfo(name="router", role=AgentRole.router, models=[], can_call=[]),
        AgentInfo(name="worker", role=AgentRole.worker,
                  models=[cfg.cheap_model, cfg.strong_model],
                  prompt_version="worker_v1", can_call=[]),
        AgentInfo(name="verifier", role=AgentRole.verifier, models=[cfg.cheap_model],
                  prompt_version="verifier_v1", can_call=[]),
    ]


def price_per_1k(cfg: Config, tier: Tier) -> float:
    return cfg.price_strong_per_1k if tier == Tier.strong else cfg.price_cheap_per_1k


def cost_of(cfg: Config, tier: Tier, tokens_in: int, tokens_out: int) -> float:
    p = price_per_1k(cfg, tier)
    return round((tokens_in + tokens_out) / 1000.0 * p, 8)


def span(agent: str, status: SpanStatus, **kw) -> AgentSpan:
    return AgentSpan(agent=agent, status=status, **kw)


class _Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.ms = (time.perf_counter() - self.t0) * 1000.0
