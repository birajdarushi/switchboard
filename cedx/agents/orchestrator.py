"""cedx/agents/orchestrator.py — role: orchestrator. Owns the run.

It holds NO business logic of its own — it delegates to router/worker/verifier,
enforces the step + cost budget, runs the bounded retry loop, and routes every
record to delivery or the exception queue. This separation is what makes the
system a real fleet (verify_audit.py check #10) rather than a god-function.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from cedx.agents import router as router_agent
from cedx.agents import verifier as verifier_agent
from cedx.agents import worker as worker_agent
from cedx.agents.base import roster, span
from cedx.agents.worker import MalformedOutput
from cedx.config import Config
from cedx.contracts import (AgentSpan, ApprovalState, ApprovalEntry, CLASS_A, CLASS_B,
                            Record, RecordStatus, ReasonClass, ReasonCode, RouterIn,
                            SpanStatus, Tier, Verdict, VerifierIn, WorkerIn)
from cedx.audit.checkpoint import Checkpoint
from cedx.delivery.deliver import attempt_delivery
from cedx.hashing import sha
from cedx.intake import IntakeItem, load_records
from cedx.llm.replay import Replayer
from cedx.normalize import detectors
from cedx.normalize.dedup import dedup
from cedx.review.approval import run_review

MAX_RETRY = 1  # bounded retry before routing an agent failure to a human


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _class_of(code: ReasonCode) -> ReasonClass:
    if code in CLASS_B:
        return ReasonClass.B
    return ReasonClass.A  # CLASS_A + agent failures are all blocking


class Orchestrator:
    def __init__(self, cfg: Config, transcripts_dir: str = "transcripts"):
        self.cfg = cfg
        self.tdir = transcripts_dir
        self.replayer = Replayer(transcripts_dir) if cfg.replay_llm else None
        self.roster = roster(cfg)

    # ---- exception helper ----
    def _exception(self, item: IntakeItem, code: ReasonCode,
                   trace: list[AgentSpan], log) -> Record:
        rec = item.record
        log.append("orchestrator", f"route_exception:{code.value}", _now(), rec.id)
        return Record(id=rec.id, version=rec.version, source_format=rec.source_format,
                      source_version_hash=rec.source_version_hash,
                      status=RecordStatus.exception, reason_code=code,
                      reason_class=_class_of(code), agent_trace=trace,
                      approval_trail=[])

    # ---- process one active record ----
    def process(self, item: IntakeItem, outliers: set[str], log,
                delivered_items: list[dict]) -> Record:
        cfg, rec = self.cfg, item.record
        trace: list[AgentSpan] = [span("orchestrator", SpanStatus.ok)]
        log.append("orchestrator", "intake_record", _now(), rec.id)

        # --- data-layer detection (before any LLM) ---
        code = detectors.classify(rec, cfg.pipeline_now, outliers)
        if code is not None:
            trace[0] = span("orchestrator", SpanStatus.routed)
            return self._exception(item, code, trace, log)

        # --- assembly: router -> worker -> verifier, with bounded retry ---
        spent = 0.0
        attempt = 0
        verifier_flagged = False
        while attempt <= MAX_RETRY:
            ri = RouterIn(record_id=rec.id, amount=rec.amount,
                          notes_len=len(rec.notes or ""), attempt=attempt,
                          verifier_flagged=verifier_flagged,
                          budget_remaining_usd=cfg.max_cost_usd_per_record - spent,
                          steps_used=len(trace))
            rdec = router_agent.decide(cfg, ri)
            trace.append(span("router", SpanStatus.routed, model=rdec.model,
                              cost_usd=0.0, retries=attempt))
            if rdec.budget_exceeded:
                trace[-1] = span("router", SpanStatus.killed, model=rdec.model)
                return self._exception(item, ReasonCode.BUDGET_EXCEEDED, trace, log)

            # worker (bounded retry on malformed)
            try:
                wout, wspan = worker_agent.draft(
                    cfg, WorkerIn(record=rec, model=rdec.model,
                                  prompt_version="worker_v1"),
                    rdec.tier, self.replayer, self.tdir)
            except MalformedOutput:
                attempt += 1
                trace.append(span("worker", SpanStatus.retried, model=rdec.model,
                                  retries=attempt))
                if attempt > MAX_RETRY:
                    return self._exception(item, ReasonCode.AGENT_MALFORMED, trace, log)
                continue
            wspan.retries = attempt
            trace.append(wspan)
            spent += wspan.cost_usd or 0.0

            if wout.abstain:
                return self._exception(item, ReasonCode.LOW_CONFIDENCE, trace, log)

            # verifier
            vout, vspan = verifier_agent.check(
                cfg, VerifierIn(source=rec, draft=wout, model=cfg.cheap_model,
                                prompt_version="verifier_v1"),
                Tier.cheap, self.replayer, self.tdir)
            trace.append(vspan)
            spent += vspan.cost_usd or 0.0

            if vout.verdict == Verdict.passed:
                return self._deliver(item, wout, trace, log, delivered_items)

            # verdict fail/needs_human → escalate + retry, else hallucination route
            verifier_flagged = True
            attempt += 1
            if attempt > MAX_RETRY:
                return self._exception(item, ReasonCode.AGENT_HALLUCINATION, trace, log)

        return self._exception(item, ReasonCode.AGENT_HALLUCINATION, trace, log)

    # ---- deliver a verified record ----
    def _deliver(self, item: IntakeItem, wout, trace, log, delivered_items) -> Record:
        cfg, rec = self.cfg, item.record
        ts = _now()
        trail = run_review(rec.id, rec.amount, cfg, ts, approve=True)
        ok = attempt_delivery(trail, rec.amount, cfg, rec.id, log, ts)
        if not ok:
            return self._exception(item, ReasonCode.LOW_CONFIDENCE, trace, log)
        trail.append(ApprovalEntry(state=ApprovalState.delivered, actor="system", ts=ts))

        code = ReasonCode.SCHEMA_DRIFT if item.schema_drift else None
        rclass = ReasonClass.B if item.schema_drift else None
        delivered_items.append({"id": rec.id, **wout.delivered_fields})
        return Record(
            id=rec.id, version=rec.version, source_format=rec.source_format,
            source_version_hash=rec.source_version_hash,
            status=RecordStatus.delivered, reason_code=code, reason_class=rclass,
            transcript_hash=wout.transcript_hash,
            delivered_fields=wout.delivered_fields,
            delivered_fields_hash=sha(wout.delivered_fields),
            agent_trace=trace, approval_trail=trail)

    # ---- superseded (Class B) ----
    def _superseded(self, item: IntakeItem, log) -> Record:
        rec = item.record
        log.append("orchestrator", "superseded", _now(), rec.id)
        return Record(id=rec.id, version=rec.version, source_format=rec.source_format,
                      source_version_hash=rec.source_version_hash,
                      status=RecordStatus.superseded,
                      reason_code=ReasonCode.SUPERSEDED_VERSION, reason_class=ReasonClass.B,
                      agent_trace=[], approval_trail=[])

    def _rebuild_delivered(self, records: list[Record]) -> list[dict]:
        items = []
        for r in records:
            if r.status == RecordStatus.delivered and r.delivered_fields:
                items.append({"id": r.id, **r.delivered_fields})
        return items

    # ---- full run (crash-safe when checkpoint_path is given) ----
    def run(self, log, checkpoint_path: str | None = None) -> tuple[list[Record], list[dict]]:
        items = load_records(self.cfg.seed_dir)
        dd = dedup(items)
        outliers = detectors.outlier_ids([it.record for it in dd.active])
        ckpt = Checkpoint(checkpoint_path)
        # test-only crash simulation: os._exit after N newly-processed records
        crash_after = int(os.environ.get("CRASH_AFTER_N", "0"))
        new_done = 0

        records: list[Record] = []
        delivered_items: list[dict] = []

        def _record(it: IntakeItem, produce):
            nonlocal new_done
            cached = ckpt.get_by_id(it.record.id, it.record.version)
            if cached is not None:                       # already done in a prior run
                records.append(cached)
                return
            rec = produce()
            records.append(rec)
            ckpt.append(rec)
            new_done += 1
            if crash_after and new_done >= crash_after:
                os._exit(137)                            # simulate SIGKILL mid-run

        for it in sorted(dd.active, key=lambda x: x.record.id):
            _record(it, lambda it=it: self.process(it, outliers, log, []))
        for it in dd.superseded:
            _record(it, lambda it=it: self._superseded(it, log))

        delivered_items = self._rebuild_delivered(records)
        ckpt.clear()                                     # success → clear for next fresh run
        return records, delivered_items
