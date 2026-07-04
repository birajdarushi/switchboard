"""cedx/config.py — runtime configuration from environment variables.

All knobs the run contract & grader use live here. Nothing about the amendment,
budgets, or seed location is hardcoded — it is all resolved at runtime so the
same code works on the held-out seed and with the live CASE_ID.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

# The four valid amendment roles, indexed by the CASE_ID hash (see TASK.md §8).
AMENDMENT_ROLES = ["risk_officer", "legal_counsel", "compliance", "finance_controller"]


def _bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    seed_dir: str
    case_id: str
    pipeline_now: str          # intake "now" for STALE detection
    replay_llm: bool
    industry: str
    brand: str
    # model router / budget ceilings
    cheap_model: str
    strong_model: str
    max_cost_usd_per_record: float
    max_steps_per_record: int
    # real-LLM path
    llm_api_key: str
    llm_model: str
    llm_base_url: str
    # rough per-1k-token prices for cost accounting (USD)
    price_cheap_per_1k: float
    price_strong_per_1k: float

    @property
    def amendment_role(self) -> str:
        h = hashlib.sha256(self.case_id.encode()).hexdigest()
        return AMENDMENT_ROLES[int(h[0], 16) % 4]

    @property
    def amendment_threshold(self) -> float:
        h = hashlib.sha256(self.case_id.encode()).hexdigest()
        return float(10000 + (int(h[1:3], 16) % 50) * 1000)


def load() -> Config:
    return Config(
        seed_dir=os.environ.get("SEED_DIR", "seed"),
        case_id=os.environ.get("CASE_ID", "CEDX-0000"),
        pipeline_now=os.environ.get("PIPELINE_NOW", "2026-06-26"),
        replay_llm=_bool("REPLAY_LLM", True),
        industry=os.environ.get("INDUSTRY", "Venture Capital — IC-ready memo pipeline"),
        brand=os.environ.get("BRAND", "Switchboard Capital"),
        cheap_model=os.environ.get("CHEAP_MODEL", "gpt-4o-mini"),
        strong_model=os.environ.get("STRONG_MODEL", "gpt-4o"),
        max_cost_usd_per_record=float(os.environ.get("MAX_COST_USD_PER_RECORD", "0.05")),
        max_steps_per_record=int(os.environ.get("MAX_STEPS_PER_RECORD", "6")),
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
        llm_model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        llm_base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        price_cheap_per_1k=float(os.environ.get("PRICE_CHEAP_PER_1K", "0.00015")),
        price_strong_per_1k=float(os.environ.get("PRICE_STRONG_PER_1K", "0.0025")),
    )
