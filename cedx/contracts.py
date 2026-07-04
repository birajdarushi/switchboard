"""cedx/contracts.py — every typed message in the fleet. Single source of truth.

Enums mirror audit.schema.json EXACTLY, so pydantic validation lines up with
verify_audit.py check #1 (schema conformance).
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------- enums (must match audit.schema.json) ----------
class SourceFormat(str, Enum):
    feed = "feed"
    eml = "eml"
    pdf = "pdf"


class RecordStatus(str, Enum):
    delivered = "delivered"
    exception = "exception"
    superseded = "superseded"


class ReasonClass(str, Enum):
    A = "A"
    B = "B"


class AgentRole(str, Enum):
    orchestrator = "orchestrator"
    worker = "worker"
    verifier = "verifier"
    router = "router"
    operator = "operator"
    other = "other"


class AmendmentRole(str, Enum):
    # NOTE: distinct from AgentRole — these are the audit.schema.json amendment roles.
    risk_officer = "risk_officer"
    legal_counsel = "legal_counsel"
    compliance = "compliance"
    finance_controller = "finance_controller"


class Tier(str, Enum):
    cheap = "cheap"
    strong = "strong"


class SpanStatus(str, Enum):
    ok = "ok"
    retried = "retried"
    rejected = "rejected"
    overruled = "overruled"
    routed = "routed"
    abstained = "abstained"
    killed = "killed"


class Verdict(str, Enum):
    # member is `passed` because `pass` is a Python keyword; VALUE is "pass".
    passed = "pass"
    fail = "fail"
    needs_human = "needs_human"


class ApprovalState(str, Enum):
    draft = "draft"
    in_review = "in_review"
    changes_requested = "changes_requested"
    approved = "approved"
    delivered = "delivered"
    blocked = "blocked"


class ReasonCode(str, Enum):
    STALE = "STALE"
    MISSING_INPUT = "MISSING_INPUT"
    OUTLIER = "OUTLIER"
    INJECTION_BLOCKED = "INJECTION_BLOCKED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNVERIFIED_ANOMALY = "UNVERIFIED_ANOMALY"
    AGENT_HALLUCINATION = "AGENT_HALLUCINATION"
    AGENT_LOOP = "AGENT_LOOP"
    AGENT_MALFORMED = "AGENT_MALFORMED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    SCHEMA_DRIFT = "SCHEMA_DRIFT"
    SUPERSEDED_VERSION = "SUPERSEDED_VERSION"


# reason-code groupings (mirror verify_audit.py)
CLASS_A = {ReasonCode.STALE, ReasonCode.MISSING_INPUT, ReasonCode.OUTLIER,
           ReasonCode.INJECTION_BLOCKED, ReasonCode.LOW_CONFIDENCE,
           ReasonCode.UNVERIFIED_ANOMALY}
AGENT_FAIL = {ReasonCode.AGENT_HALLUCINATION, ReasonCode.AGENT_LOOP,
              ReasonCode.AGENT_MALFORMED, ReasonCode.BUDGET_EXCEEDED}
CLASS_B = {ReasonCode.SCHEMA_DRIFT, ReasonCode.SUPERSEDED_VERSION}
BLOCKING = CLASS_A | AGENT_FAIL


# ---------- (1) shared canonical record: intake output ----------
class CanonicalRecord(BaseModel):
    id: str
    version: int = 1
    owner: Optional[str] = None
    deadline: Optional[str] = None          # ISO date string; None if absent
    category: Optional[str] = None
    amount: Optional[float] = None          # None => MISSING_INPUT candidate
    notes: str = ""
    source_format: SourceFormat
    source_version_hash: str                # sha256 of the raw source bytes


# ---------- (3) agent I/O contracts ----------
class RouterIn(BaseModel):
    record_id: str
    amount: Optional[float] = None
    notes_len: int = 0
    attempt: int = 0
    verifier_flagged: bool = False
    budget_remaining_usd: float
    steps_used: int = 0


class RouterOut(BaseModel):
    model: str
    tier: Tier
    reason: str
    est_cost_usd: float
    budget_exceeded: bool = False


class WorkerIn(BaseModel):
    record: CanonicalRecord
    model: str
    prompt_version: str


class WorkerOut(BaseModel):
    record_id: str
    delivered_fields: dict                  # THE dict that gets hashed
    confidence: float
    abstain: bool = False
    transcript_hash: Optional[str] = None    # "sha256:<hex>", set after recording


class VerifierIn(BaseModel):
    source: CanonicalRecord
    draft: WorkerOut
    model: str
    prompt_version: str


class VerifierOut(BaseModel):
    record_id: str
    verdict: Verdict
    overruled_fields: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    reason: str = ""


# ---------- artifacts the gate reads ----------
class AgentSpan(BaseModel):                  # -> record.agent_trace[]
    agent: str
    model: Optional[str] = None
    prompt_version: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[float] = None
    retries: Optional[int] = None
    transcript_hash: Optional[str] = None
    status: SpanStatus
    verdict: Optional[Verdict] = None        # set only on verifier spans


class ApprovalEntry(BaseModel):              # -> record.approval_trail[]
    state: ApprovalState
    actor: str
    ts: str
    reason: Optional[str] = None


class Record(BaseModel):                     # -> audit.records[]
    id: str
    version: Optional[int] = None
    source_format: SourceFormat
    source_version_hash: Optional[str] = None
    status: RecordStatus
    reason_code: Optional[ReasonCode] = None
    reason_class: Optional[ReasonClass] = None
    transcript_hash: Optional[str] = None
    delivered_fields: Optional[dict] = None
    delivered_fields_hash: Optional[str] = None
    agent_trace: list[AgentSpan] = Field(default_factory=list)
    approval_trail: list[ApprovalEntry] = Field(default_factory=list)


# ---------- top-level audit bundle ----------
class AgentInfo(BaseModel):                  # -> audit.agents[]
    name: str
    role: AgentRole
    models: list[str] = Field(default_factory=list)
    prompt_version: Optional[str] = None
    can_call: list[str] = Field(default_factory=list)


class CostSummary(BaseModel):
    total_usd: float
    records: int
    avg_usd_per_record: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    projected_usd_per_10k: Optional[float] = None


class Event(BaseModel):                      # -> audit.events[] (append-only, seq 0..n-1)
    seq: int
    ts: str
    actor: str
    action: str
    record_id: Optional[str] = None
    prev: Optional[str] = None               # hash of previous event (tamper-evident chain)
    hash: Optional[str] = None               # hash of this event incl. prev


class Amendment(BaseModel):
    role: AmendmentRole
    threshold: float


class Audit(BaseModel):                      # -> out/audit.json (top level)
    case_id: str
    pipeline_version: str
    generated_at: str
    seed_dir: str
    pipeline_now: Optional[str] = None
    amendment: Amendment
    agents: list[AgentInfo]
    cost: CostSummary
    output_package_hash: str
    records: list[Record]
    events: list[Event]
