"""cedx/branding.py — the thin, industry-specific layer.

Lane: Venture Capital — IC-ready investment memos. The ARCHITECTURE is domain-agnostic;
only the delivered-output shape and its grounding live here. MEMO_FIELDS maps each
delivered memo field to the source record attribute it must be grounded to — used by
the Worker (to draft), the Verifier (to catch hallucinations), and the eval judge.
Changing the output shape is a one-file edit (handy for the live-extension call).
"""
from __future__ import annotations

# delivered memo field -> source CanonicalRecord attribute it must trace to
MEMO_FIELDS: dict[str, str] = {
    "deal_lead": "owner",       # partner/analyst sourcing the deal
    "deal_type": "category",    # deal stage/type
    "check_size": "amount",     # proposed check / round size
    "ic_date": "deadline",      # investment-committee date
}


def build_memo(rec: dict, firm: str) -> dict:
    """Assemble an IC-ready memo draft grounded entirely in the source record."""
    return {
        "memo_id": rec["id"],
        "deal_lead": rec["owner"],
        "deal_type": rec["category"],
        "check_size": rec["amount"],
        "ic_date": rec["deadline"],
        "firm": firm,
        "summary": (f"IC memo — {rec['category']} deal led by {rec['owner']}, "
                    f"check size {rec['amount']}, IC by {rec['deadline']}."),
    }
