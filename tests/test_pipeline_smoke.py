"""End-to-end guard: full run on the dev seed routes every record correctly."""
from cedx.agents.orchestrator import Orchestrator
from cedx.audit.log import EventLog


def test_full_seed_run(cfg):
    records, delivered_items = Orchestrator(cfg).run(EventLog())

    by = {}
    for r in records:
        if r.id not in by or r.status.value != "superseded":
            by[r.id] = r

    delivered = [r for r in records if r.status.value == "delivered"]
    exceptions = [r for r in records if r.status.value == "exception"]
    assert len(delivered) == 15
    assert len(exceptions) == 7

    codes = {r.reason_code.value for r in records if r.reason_code}
    for c in ["STALE", "MISSING_INPUT", "OUTLIER", "INJECTION_BLOCKED",
              "LOW_CONFIDENCE", "SCHEMA_DRIFT", "SUPERSEDED_VERSION"]:
        assert c in codes, c

    assert by["REC-011"].reason_code.value == "STALE"
    assert by["REC-013"].reason_code.value == "OUTLIER"
    assert by["REC-014"].reason_code.value == "INJECTION_BLOCKED"
    assert by["REC-016"].reason_code.value == "SCHEMA_DRIFT"
    assert by["REC-016"].status.value == "delivered"


def test_delivered_have_verifier_pass(cfg):
    records, _ = Orchestrator(cfg).run(EventLog())
    for r in records:
        if r.status.value == "delivered":
            vspans = [s for s in r.agent_trace if s.agent == "verifier"]
            assert any(s.verdict and s.verdict.value == "pass" for s in vspans), r.id
