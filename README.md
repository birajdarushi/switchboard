# CEDX Tiny Agent Fleet

A small but genuinely working multi-agent pipeline: it ingests messy work-request
records (JSON + email + PDF), catches every bad record **and** every misbehaving agent,
delivers only clean + human-approved output, stays cheap, and is fully traceable and
replayable. One command runs it end-to-end offline.

## 1. Industry & Scope
- **Industry:** Invoice / AP financial operations (records = work-requests with owner,
  deadline, category, amount).
- **Tier:** see `SCOPE.md`.
- **CASE_ID:** runtime env var (placeholder `CEDX-7F3A`); drives the amendment (§9).
- **Records that reach delivery:** all clean records + Class-B (SCHEMA_DRIFT REC-016,
  latest-version SUPERSEDED REC-017 v2). 15 delivered, 7 exceptions, 1 superseded on the dev seed.

## 2. Agent topology
4 agents (roster in `audit.json.agents[]`), full diagram + file pointers in `ARCHITECTURE.md`:

| name | role | can_call | file |
|---|---|---|---|
| orchestrator | orchestrator | router, worker, verifier | `cedx/agents/orchestrator.py` |
| router | router | — | `cedx/agents/router.py` |
| worker | worker | — | `cedx/agents/worker.py` |
| verifier | verifier | — | `cedx/agents/verifier.py` |

Typed contracts in `cedx/contracts.py`. The Verifier is independent and **overrules** the
Worker (`cedx/agents/verifier.py`); the retry loop lives in the Orchestrator.

## 3. How to Run
```bash
# one command, offline, reproducible:
docker compose up            # builds, runs `make demo && make verify`

# or locally (Python 3.11+):
pip install -r requirements.txt
export CASE_ID=CEDX-7F3A
make demo && make verify
```
Writes `out/package.json`, `out/audit.json`, `out/exception_queue.json`.
Regenerate transcripts: `make record` (offline dev) or `REPLAY_LLM=false LLM_API_KEY=... make record` (real).

## 4. Controls (uniform probe CLI)
| Command | Result |
|---|---|
| `make demo` | full fleet, offline replay → package + audit + exception dump |
| `make verify` | `verify_audit.py` gate → **PASS** |
| `make trace ID=<id>` | full agent decision path for one record |
| `make replay ID=<id>` | data lineage (hashes + events) from the log alone |
| `make eval` | 12 golden cases + LLM-judge per agent → PASS |
| `make probe-approval` | non-approved / amendment-incomplete delivery refused |
| `make probe-agent-failure` | Verifier catches hallucinated worker output → routed |
| `make probe-budget` | over-ceiling record → `BUDGET_EXCEEDED`, routed |
| `make probe-append-only` | mutation/deletion of a past audit entry detected |
| `make probe-idempotency` | two runs identical, no double-delivery |

## 5. Planted-problem handling
**Data layer** (`cedx/normalize/detectors.py`, before any LLM):
STALE (REC-011), MISSING_INPUT (REC-012), OUTLIER (REC-013, robust MAD), INJECTION_BLOCKED
(REC-014 + REC-022 generalized), LOW_CONFIDENCE (REC-015, REC-021, worker abstains),
SCHEMA_DRIFT (REC-016, Value→amount, delivered), SUPERSEDED_VERSION (REC-017, keep v2),
UNVERIFIED_ANOMALY (catch-all for held-out unknowns).
**Agent layer** (`cedx/agents/verifier.py` + orchestrator): AGENT_HALLUCINATION,
AGENT_MALFORMED, AGENT_LOOP, BUDGET_EXCEEDED — never delivered, catch evidenced in the trace.

## 6. Generalization
Every detector is rule-based and batch-relative, not tied to seed values: the outlier
threshold is a per-batch MAD robust-z (adapts to any magnitude), injection is a pattern set
(catches REC-022's novel wording, not just REC-014), schema-drift is a declarative alias map,
supersede is version-based. Nothing is keyed to a specific id or amount, so the held-out seed
(different values, shuffled, new anomaly) routes the same way.

## 7. LLM / agent contract & eval
- `REPLAY_LLM=true` (default): replays committed `transcripts/<hex>.json` deterministically.
- `REPLAY_LLM=false` + `LLM_API_KEY`/`LLM_MODEL`/`LLM_BASE_URL`: real OpenAI-compatible call
  (gpt-4o-mini / claude-3-5-haiku / gemini-1.5-flash).
- `make eval`: 12 golden end-to-end cases + an LLM-judge per agent (worker/verifier/router),
  scoring grounding, verdict correctness, and tier appropriateness. Dev result: 12/12, all
  agents 1.00.

## 8. Cost & scale
Measured (offline replay, dev seed): **total $0.00085**, **avg $0.0000499/record**,
**p95 latency 0.012 ms** (replay; real-model latency dominates on the keyed path).
**Projected ~$0.50 / 10,000 records/day** at the cheap-model price for the two calls
(worker + verifier) per clean record; escalation to the strong model only on hard records.
Per-record ceiling raises `BUDGET_EXCEEDED` rather than overspend.

## 9. Amendment (CASE_ID-bound, maker-checker)
```
H = sha256(CASE_ID); R = [risk_officer,legal_counsel,compliance,finance_controller][int(H[0],16)%4]
T = 10000 + (int(H[1:3],16)%50)*1000
```
Prints `AMENDMENT: role=<R> threshold=<T>` at startup; recorded under `audit.amendment`.
Records with `amount >= T` need a second approval by role R (a *different* actor from the
operator) before delivery — enforced server-side in `cedx/delivery/deliver.py`.

## 10. AI usage / real-vs-faked
AI-assisted throughout (assumed and allowed). The system is real: intake, normalize,
detectors, router, state machine, hashing, and audit are all executing code. Only the raw
model text is replaced under `REPLAY_LLM=true`. Offline transcripts come from a deterministic
dev generator gated behind `ALLOW_FAKE_LLM` so it can never silently stand in for a real model
during grading; the graded real path uses a real key. See `DECISIONS.md`.

## 11. Tradeoffs & next week
- Serial single-process run — first thing to shard at 10k/day (agents are stateless per record).
- Verifier is a second LLM call; next step is a confidence gate to skip it on the safest records.
- `probe-crash` (resumability) is not yet implemented (bonus). Next: stage checkpoints so a
  SIGKILL mid-run resumes without re-delivering.
- Full design rationale + gate mapping is logged in `QA_LOG.md`.
