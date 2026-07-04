"""Model router policy: cheap by default, escalate only when hard; budget ceiling."""
from cedx.agents import router
from cedx.contracts import RouterIn, Tier


def test_cheap_by_default(cfg):
    d = router.decide(cfg, RouterIn(record_id="R", amount=5000, budget_remaining_usd=1.0))
    assert d.tier == Tier.cheap and not d.budget_exceeded


def test_escalate_on_retry(cfg):
    d = router.decide(cfg, RouterIn(record_id="R", amount=5000, attempt=1,
                                    budget_remaining_usd=1.0))
    assert d.tier == Tier.strong


def test_escalate_on_verifier_flag(cfg):
    d = router.decide(cfg, RouterIn(record_id="R", amount=5000, verifier_flagged=True,
                                    budget_remaining_usd=1.0))
    assert d.tier == Tier.strong


def test_escalate_on_large_amount(cfg):
    d = router.decide(cfg, RouterIn(record_id="R", amount=200000, budget_remaining_usd=1.0))
    assert d.tier == Tier.strong


def test_budget_exceeded_no_remaining(cfg):
    d = router.decide(cfg, RouterIn(record_id="R", amount=5000, budget_remaining_usd=0.0))
    assert d.budget_exceeded


def test_budget_exceeded_steps(cfg):
    d = router.decide(cfg, RouterIn(record_id="R", amount=5000, budget_remaining_usd=1.0,
                                    steps_used=cfg.max_steps_per_record))
    assert d.budget_exceeded
