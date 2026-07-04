"""cedx/delivery/deliver.py — the SERVER-SIDE delivery gate.

Nothing is delivered unless the approval chain (incl. CASE_ID amendment) is
satisfied. A refusal is logged, never silent. This is the single choke point that
`make probe-approval` exercises (verify_audit.py checks #6/#7 depend on it).
"""
from __future__ import annotations

from cedx.config import Config
from cedx.contracts import ApprovalEntry
from cedx.review.approval import can_deliver


def attempt_delivery(trail: list[ApprovalEntry], amount: float | None, cfg: Config,
                     rec_id: str, log, ts: str) -> bool:
    if can_deliver(trail, amount, cfg):
        log.append("system", "deliver", ts, rec_id)
        return True
    log.append("system", "delivery_refused_not_approved", ts, rec_id)
    return False
