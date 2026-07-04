"""Approval state machine + CASE_ID amendment (maker-checker)."""
from cedx.contracts import ApprovalState
from cedx.review.approval import can_deliver, run_review


def test_unapproved_refused(cfg):
    t = run_review("R", 100, cfg, "ts", approve=False)
    assert not can_deliver(t, 100, cfg)


def test_low_value_operator_ok(cfg):
    lo = cfg.amendment_threshold - 1
    t = run_review("R", lo, cfg, "ts")
    assert can_deliver(t, lo, cfg)


def test_high_value_full_approval_ok(cfg):
    hi = cfg.amendment_threshold + 1
    t = run_review("R", hi, cfg, "ts")
    assert can_deliver(t, hi, cfg)


def test_high_value_operator_only_refused(cfg):
    hi = cfg.amendment_threshold + 1
    full = run_review("R", hi, cfg, "ts")
    op_only = [e for e in full if not e.actor.startswith(cfg.amendment_role + ".")]
    assert not can_deliver(op_only, hi, cfg)


def test_high_value_roleR_only_refused(cfg):
    hi = cfg.amendment_threshold + 1
    full = run_review("R", hi, cfg, "ts")
    role_only = [e for e in full if e.state != ApprovalState.approved
                 or e.actor.startswith(cfg.amendment_role + ".")]
    assert not can_deliver(role_only, hi, cfg)
