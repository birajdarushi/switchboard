"""cedx/review — STAGE (4). Approval chain state machine + CASE_ID amendment.

State machine: draft → in_review → approved → (delivered appended by delivery).
Amendment (maker-checker): if amount >= threshold T, a second approval by role R is
required IN ADDITION to the operator, and the two approvers must differ (maker≠checker).
The delivery gate (can_deliver) is enforced server-side, not in the CLI.
"""
from __future__ import annotations

from cedx.config import Config
from cedx.contracts import ApprovalEntry, ApprovalState

OPERATOR = "operator.default"


def run_review(rec_id: str, amount: float | None, cfg: Config, ts: str,
               approve: bool = True) -> list[ApprovalEntry]:
    trail = [
        ApprovalEntry(state=ApprovalState.draft, actor="system", ts=ts),
        ApprovalEntry(state=ApprovalState.in_review, actor="system", ts=ts),
    ]
    if not approve:
        return trail                                   # left in_review (probe-approval)

    trail.append(ApprovalEntry(state=ApprovalState.approved, actor=OPERATOR, ts=ts,
                               reason="operator approved"))
    if amount is not None and amount >= cfg.amendment_threshold:
        role = cfg.amendment_role
        trail.append(ApprovalEntry(
            state=ApprovalState.approved, actor=f"{role}.reviewer", ts=ts,
            reason=f"amendment: amount {amount} >= T {cfg.amendment_threshold} "
                   f"requires {role}"))
    return trail


def can_deliver(trail: list[ApprovalEntry], amount: float | None, cfg: Config) -> bool:
    """Server-side gate: approved reached, amendment satisfied, maker != checker."""
    approvers = [e.actor for e in trail if e.state == ApprovalState.approved]
    if not approvers:
        return False
    if amount is not None and amount >= cfg.amendment_threshold:
        role = cfg.amendment_role
        role_approvers = [a for a in approvers if a.startswith(role + ".")]
        other = [a for a in approvers if not a.startswith(role + ".")]
        if not role_approvers or not other:
            return False
        if set(role_approvers) == set(approvers):          # maker == checker
            return False
    return True
