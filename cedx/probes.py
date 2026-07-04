"""cedx/probes.py — the adversarial probe harness.

Each probe returns exit 0 ONLY if the system behaves safely under attack, matching
the Makefile contract. These are diagnostics (not the graded demo), so the agent
failures are induced deterministically via the dev fake path / crafted records.
"""
from __future__ import annotations

import copy
import dataclasses
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cedx.agents.orchestrator import Orchestrator
from cedx.audit.log import EventLog, verify_chain
from cedx.config import Config
from cedx.contracts import CanonicalRecord, RecordStatus, ReasonCode, SourceFormat, Verdict
from cedx.hashing import sha
from cedx.intake import IntakeItem
from cedx.review.approval import can_deliver, run_review


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _item(rid: str, amount, cfg: Config) -> IntakeItem:
    rec = CanonicalRecord(id=rid, version=1, owner="probe.owner",
                          deadline="2026-08-01", category="REPORT", amount=amount,
                          notes="probe record", source_format=SourceFormat.feed,
                          source_version_hash=sha(rid))
    return IntakeItem(record=rec, schema_drift=False)


def _fake_cfg(cfg: Config, **over) -> Config:
    os.environ["ALLOW_FAKE_LLM"] = "1"
    return dataclasses.replace(cfg, replay_llm=False, **over)


def _ok(name: str, msg: str) -> int:
    print(f"PASS [{name}] {msg}")
    return 0


def _fail(name: str, msg: str) -> int:
    print(f"FAIL [{name}] {msg}")
    return 1


# ---------------------------------------------------------------- approval
def probe_approval(cfg: Config) -> int:
    n = "probe-approval"
    # 1) not approved (stopped at in_review) → must be refused
    unapproved = run_review("R1", 5000, cfg, _ts(), approve=False)
    if can_deliver(unapproved, 5000, cfg):
        return _fail(n, "a NON-approved item would be delivered")

    # 2) high-value approved by operator ONLY (amendment role R missing) → refused
    hi = cfg.amendment_threshold + 1
    op_only = run_review("R2", hi, cfg, _ts(), approve=True)
    # strip the role-R approval to simulate operator-only
    op_only = [e for e in op_only if not e.actor.startswith(cfg.amendment_role + ".")]
    if can_deliver(op_only, hi, cfg):
        return _fail(n, "high-value item delivered without role-R amendment approval")

    # 3) properly approved (operator + role R) → allowed (sanity)
    full = run_review("R3", hi, cfg, _ts(), approve=True)
    if not can_deliver(full, hi, cfg):
        return _fail(n, "a fully-approved high-value item was wrongly refused")

    return _ok(n, f"non-approved refused; amendment (role={cfg.amendment_role} "
                  f"T={cfg.amendment_threshold}) enforced; valid delivery allowed")


# ---------------------------------------------------------------- agent failure
def probe_agent_failure(cfg: Config) -> int:
    n = "probe-agent-failure"
    cfg2 = _fake_cfg(cfg)
    with tempfile.TemporaryDirectory() as td:
        orch = Orchestrator(cfg2, transcripts_dir=td)
        log = EventLog()
        rec = orch.process(_item("PROBE-HALLUC-1", 5000, cfg2), set(), log, [])
    if rec.status == RecordStatus.delivered:
        return _fail(n, "hallucinated worker output was DELIVERED")
    if rec.reason_code != ReasonCode.AGENT_HALLUCINATION:
        return _fail(n, f"expected AGENT_HALLUCINATION, got {rec.reason_code}")
    caught = any(s.verdict == Verdict.fail or s.status.value in
                 {"rejected", "overruled"} for s in rec.agent_trace)
    if not caught:
        return _fail(n, "no verifier rejection/overrule evidenced in trace")
    return _ok(n, "verifier caught fabricated field, routed to AGENT_HALLUCINATION, not delivered")


# ---------------------------------------------------------------- budget
def probe_budget(cfg: Config) -> int:
    n = "probe-budget"
    cfg2 = _fake_cfg(cfg, max_cost_usd_per_record=0.0)
    with tempfile.TemporaryDirectory() as td:
        orch = Orchestrator(cfg2, transcripts_dir=td)
        log = EventLog()
        rec = orch.process(_item("PROBE-BUDGET-1", 5000, cfg2), set(), log, [])
    if rec.status == RecordStatus.delivered:
        return _fail(n, "record over the cost ceiling was silently delivered")
    if rec.reason_code != ReasonCode.BUDGET_EXCEEDED:
        return _fail(n, f"expected BUDGET_EXCEEDED, got {rec.reason_code}")
    return _ok(n, "over-budget record raised BUDGET_EXCEEDED and was routed, not overspent")


# ---------------------------------------------------------------- append-only
def probe_append_only(cfg: Config) -> int:
    n = "probe-append-only"
    log = EventLog()
    for i in range(4):
        log.append("system", f"action_{i}", _ts(), f"REC-{i}")
    events = [e.model_dump(mode="json") for e in log.events]

    ok, _ = verify_chain(events)
    if not ok:
        return _fail(n, "clean chain failed to verify (bug in chaining)")

    # attempt MUTATION of a past entry
    tampered = copy.deepcopy(events)
    tampered[1]["action"] = "action_TAMPERED"
    if verify_chain(tampered)[0]:
        return _fail(n, "mutation of a past audit entry was NOT detected")

    # attempt DELETION of a past entry
    deleted = [e for e in copy.deepcopy(events) if e["seq"] != 1]
    if verify_chain(deleted)[0]:
        return _fail(n, "deletion of a past audit entry was NOT detected")

    return _ok(n, "past-entry mutation AND deletion both detected (append-only enforced)")


# ---------------------------------------------------------------- idempotency
def probe_idempotency(cfg: Config) -> int:
    n = "probe-idempotency"
    r1, d1 = Orchestrator(cfg).run(EventLog())
    r2, d2 = Orchestrator(cfg).run(EventLog())

    # no id may be DELIVERED more than once (superseded+active sharing an id is fine)
    del1 = sorted(x["id"] for x in d1)
    del2 = sorted(x["id"] for x in d2)
    if len(del1) != len(set(del1)):
        return _fail(n, "an id was delivered more than once in a single run")

    # run 2 must be identical to run 1 (deterministic rebuild = idempotent)
    def sig(recs):
        return sorted((r.id, r.version, r.status.value,
                       r.reason_code.value if r.reason_code else None) for r in recs)
    if sig(r1) != sig(r2) or del1 != del2:
        return _fail(n, "run 2 differs from run 1 (not idempotent)")
    return _ok(n, f"two runs identical: {len(r1)} records, {len(del1)} delivered, no dup deliveries")


# ---------------------------------------------------------------- crash / resume (bonus)
def probe_crash(cfg: Config) -> int:
    n = "probe-crash"
    ckpt = Path("out/.checkpoint.jsonl")
    if ckpt.exists():
        ckpt.unlink()
    env = dict(os.environ)

    # 1) run demo but SIGKILL-simulate after 5 records
    env["CRASH_AFTER_N"] = "5"
    r1 = subprocess.run([sys.executable, "-m", "cedx", "demo"],
                        env=env, capture_output=True, text=True)
    if r1.returncode == 0:
        return _fail(n, "crash run exited 0 (did not crash as expected)")
    partial = len(ckpt.read_text().splitlines()) if ckpt.exists() else 0
    if partial < 1:
        return _fail(n, "no checkpoint written before crash (cannot resume)")

    # 2) re-run demo → must resume and complete
    env["CRASH_AFTER_N"] = "0"
    r2 = subprocess.run([sys.executable, "-m", "cedx", "demo"],
                        env=env, capture_output=True, text=True)
    if r2.returncode != 0:
        return _fail(n, f"resume run failed: {r2.stderr[-300:]}")

    audit = json.loads(Path("out/audit.json").read_text())
    delivered = [r["id"] for r in audit["records"] if r["status"] == "delivered"]
    if len(delivered) != len(set(delivered)):
        return _fail(n, "duplicate deliveries after resume")
    if len(audit["records"]) != 23:
        return _fail(n, f"resumed run has {len(audit['records'])} records, expected 23")
    return _ok(n, f"crashed after {partial} records, resumed to full "
                  f"{len(audit['records'])} records, {len(delivered)} delivered, no dupes")


PROBES = {
    "approval": probe_approval,
    "agent-failure": probe_agent_failure,
    "budget": probe_budget,
    "append-only": probe_append_only,
    "idempotency": probe_idempotency,
    "crash": probe_crash,
}


def run(name: str, cfg: Config) -> int:
    fn = PROBES.get(name)
    if fn is None:
        print(f"unknown probe: {name}")
        return 2
    return fn(cfg)
