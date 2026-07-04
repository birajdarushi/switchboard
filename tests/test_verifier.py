"""Agent-checks-agent: Verifier passes grounded drafts, overrules hallucinations."""
import tempfile

from cedx.agents import verifier
from cedx.contracts import (CanonicalRecord, SourceFormat, Tier, Verdict, VerifierIn,
                            WorkerOut)


def _src(amount=5000.0):
    return CanonicalRecord(id="R", owner="o", deadline="2026-07-15", category="C",
                           amount=amount, notes="", source_format=SourceFormat.feed,
                           source_version_hash="sha256:x")


def _check(cfg_fake, source, delivered_fields):
    wo = WorkerOut(record_id="R", delivered_fields=delivered_fields, confidence=0.9)
    with tempfile.TemporaryDirectory() as td:
        return verifier.check(cfg_fake,
                              VerifierIn(source=source, draft=wo, model=cfg_fake.cheap_model,
                                         prompt_version="verifier_v1"),
                              Tier.cheap, None, td)


def test_grounded_draft_passes(cfg_fake):
    s = _src()
    df = {"owner": s.owner, "category": s.category, "amount": s.amount, "deadline": s.deadline}
    out, sp = _check(cfg_fake, s, df)
    assert out.verdict == Verdict.passed


def test_hallucinated_amount_overruled(cfg_fake):
    s = _src()
    df = {"owner": s.owner, "category": s.category, "amount": s.amount + 999999,
          "deadline": s.deadline}
    out, sp = _check(cfg_fake, s, df)
    assert out.verdict == Verdict.fail
    assert "amount" in out.overruled_fields
    assert sp.status.value in {"overruled", "rejected"}
