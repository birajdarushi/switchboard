"""Agent-checks-agent: Verifier passes grounded drafts, overrules hallucinations."""
import tempfile

from cedx.agents import verifier
from cedx.branding import build_memo
from cedx.contracts import (CanonicalRecord, SourceFormat, Tier, Verdict, VerifierIn,
                            WorkerOut)


def _src(amount=5000.0):
    return CanonicalRecord(id="R", owner="o", deadline="2026-07-15", category="C",
                           amount=amount, notes="", source_format=SourceFormat.feed,
                           source_version_hash="sha256:x")


def _memo(s):
    return build_memo({"id": s.id, "owner": s.owner, "category": s.category,
                       "amount": s.amount, "deadline": s.deadline}, "Switchboard Capital")


def _check(cfg_fake, source, delivered_fields):
    wo = WorkerOut(record_id="R", delivered_fields=delivered_fields, confidence=0.9)
    with tempfile.TemporaryDirectory() as td:
        return verifier.check(cfg_fake,
                              VerifierIn(source=source, draft=wo, model=cfg_fake.cheap_model,
                                         prompt_version="verifier_v1"),
                              Tier.cheap, None, td)


def test_grounded_draft_passes(cfg_fake):
    s = _src()
    out, sp = _check(cfg_fake, s, _memo(s))
    assert out.verdict == Verdict.passed


def test_hallucinated_check_size_overruled(cfg_fake):
    s = _src()
    df = _memo(s)
    df["check_size"] = s.amount + 999999          # fabricated, not grounded in source
    out, sp = _check(cfg_fake, s, df)
    assert out.verdict == Verdict.fail
    assert "check_size" in out.overruled_fields
    assert sp.status.value in {"overruled", "rejected"}
