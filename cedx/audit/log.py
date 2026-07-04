"""cedx/audit/log.py — append-only event log + audit.json writer.

ALL serialization goes through here with model_dump(mode="json") so pydantic enums
become their string VALUES (e.g. Verdict.passed -> "pass"). Any other serialization
path risks writing enum reprs and failing verify_audit.py checks #1/#13.
"""
from __future__ import annotations

import json
from pathlib import Path

from cedx.config import Config
from cedx.contracts import (Amendment, AgentInfo, Audit, AmendmentRole, CostSummary,
                            Event, Record)
from cedx.hashing import sha


def _event_hash(seq, ts, actor, action, record_id, prev) -> str:
    return sha({"seq": seq, "ts": ts, "actor": actor, "action": action,
                "record_id": record_id, "prev": prev})


class EventLog:
    """Strictly append-only, seq 0..n-1 (verify_audit.py check #9).

    Each event is chained: hash = sha(fields + prev_hash). Any mutation or deletion
    of a past entry breaks the chain and is caught by verify_chain() — this backs
    `make probe-append-only`.
    """

    def __init__(self):
        self._events: list[Event] = []

    def append(self, actor: str, action: str, ts: str, record_id: str | None = None) -> None:
        seq = len(self._events)
        prev = self._events[-1].hash if self._events else ""
        h = _event_hash(seq, ts, actor, action, record_id, prev)
        self._events.append(Event(seq=seq, ts=ts, actor=actor, action=action,
                                  record_id=record_id, prev=prev, hash=h))

    @property
    def events(self) -> list[Event]:
        return self._events


def verify_chain(events: list[dict]) -> tuple[bool, int]:
    """Return (ok, bad_seq). Detects mutation/deletion of any past event."""
    prev = ""
    for i, e in enumerate(events):
        if e.get("seq") != i:
            return False, i
        expect = _event_hash(e["seq"], e["ts"], e["actor"], e["action"],
                             e.get("record_id"), prev)
        if e.get("hash") != expect or e.get("prev") != prev:
            return False, i
        prev = e["hash"]
    return True, -1


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]


def summarize_cost(records: list[Record]) -> CostSummary:
    total = 0.0
    latencies: list[float] = []
    processed = 0
    for r in records:
        touched = False
        for sp in r.agent_trace:
            if sp.cost_usd:
                total += sp.cost_usd
                touched = True
            if sp.latency_ms:
                latencies.append(sp.latency_ms)
        if touched:
            processed += 1
    total = round(total, 8)
    avg = round(total / processed, 8) if processed else 0.0
    return CostSummary(
        total_usd=total, records=len(records),
        avg_usd_per_record=avg,
        p95_latency_ms=round(_percentile(latencies, 95), 3),
        projected_usd_per_10k=round(avg * 10000, 4),
    )


def build_audit(cfg: Config, roster: list[AgentInfo], records: list[Record],
                events: list[Event], output_package_hash: str, generated_at: str) -> Audit:
    return Audit(
        case_id=cfg.case_id,
        pipeline_version="cedx-fleet-1.0",
        generated_at=generated_at,
        seed_dir=cfg.seed_dir,
        pipeline_now=cfg.pipeline_now,
        amendment=Amendment(role=AmendmentRole(cfg.amendment_role),
                            threshold=cfg.amendment_threshold),
        agents=roster,
        cost=summarize_cost(records),
        output_package_hash=output_package_hash,
        records=records,
        events=events,
    )


def write_audit(audit: Audit, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # exclude_none: drop optional null keys (e.g. router prompt_version) so they
    # don't violate non-nullable schema types. Required fields are never None.
    (out / "audit.json").write_text(
        json.dumps(audit.model_dump(mode="json", exclude_none=True),
                   indent=2, ensure_ascii=False),
        encoding="utf-8")
