# ARCHITECTURE — CEDX Tiny Agent Fleet

## Agent topology

```
                    Intake + Normalize  (deterministic, no LLM)
                    feed.json + inbox/*.{eml,pdf} -> CanonicalRecord
                                   |
                                   v
        +======================================================+
        |                 ORCHESTRATOR (role: orchestrator)    |
        |  owns the run, enforces step+cost budget, runs the   |
        |  bounded retry loop, routes every record.            |
        |  can_call = [router, worker, verifier]               |
        +======================================================+
             | 1 decide model     | 2 draft         | 3 check
             v                    v                  v
   ROUTER (router)        WORKER (worker)     VERIFIER (verifier)
   deterministic          LLM assembly draft  independent LLM check
   cheap|strong +         -> load-bearing     verdict pass|fail|
   BUDGET_EXCEEDED        transcript          needs_human; OVERRULES
   can_call = []          can_call = []       worker.  can_call = []
             \                    |                  /
              \                   v                 /
               +--> Orchestrator routes to: ------+
                    - DELIVERY (verdict pass + approved)
                    - EXCEPTION QUEUE (blocking / agent failure)
```

**Why it is a real fleet, not a god-function:** only the Orchestrator has a non-empty
`can_call`. Router/Worker/Verifier are leaf agents in separate modules
(`cedx/agents/*.py`), each independently testable. The retry loop lives in the
Orchestrator so the Verifier stays **independent** — it only judges, it never drives
control flow.

## Typed contracts (see `cedx/contracts.py`)

| Agent | Input | Output | Module |
|---|---|---|---|
| orchestrator | `CanonicalRecord[]` | `Record[]` | `cedx/agents/orchestrator.py` |
| router | `RouterIn` | `RouterOut{model,tier,budget_exceeded}` | `cedx/agents/router.py` |
| worker | `WorkerIn{record,model}` | `WorkerOut{delivered_fields,confidence,abstain}` | `cedx/agents/worker.py` |
| verifier | `VerifierIn{source,draft}` | `VerifierOut{verdict,overruled_fields}` | `cedx/agents/verifier.py` |

The roster in `audit.json.agents[]` declares each agent's `role`, `models`, and
`can_call` — validated by `verify_audit.py` check #10.

## Where the key decisions live

- **Verifier overrules Worker:** `cedx/agents/verifier.py` — after reading the model
  verdict, a deterministic cross-check compares every delivered field to the source;
  any mismatch forces `verdict=fail` + `status=overruled`, logged with both sides.
  The Orchestrator then bounded-retries and, if still bad, routes `AGENT_HALLUCINATION`.
- **Budget / router decisions:** `cedx/agents/router.py` (tier choice + `BUDGET_EXCEEDED`)
  and `cedx/agents/orchestrator.py` (accumulates spend, enforces the ceiling).
- **Approval + amendment:** `cedx/review/approval.py` (state machine + maker-checker),
  enforced server-side in `cedx/delivery/deliver.py`.
- **Observability:** every agent step appends an `AgentSpan` to `record.agent_trace`;
  `cedx/audit/log.py` writes the append-only, hash-chained event log + cost summary.

## The load-bearing hash chain (`cedx/hashing.py`, byte-identical to the gate)

```
worker response  --sha256-->  response_hash  == record.transcript_hash
                                            == transcripts/<hex>.json filename
worker delivered_fields --sha256--> delivered_fields_hash (on record AND transcript)
transcript.agent == "worker"   (proves the load-bearing call came from a worker)
```

## The thin industry layer (`cedx/branding.py`)

The architecture is domain-agnostic (the rubric rewards depth over domain). The **only**
industry-specific code is `cedx/branding.py`: `MEMO_FIELDS` (which delivered memo field
maps to which source attribute) + `build_memo()`. The Worker drafts with it, the Verifier
grounds against it, and the eval judge scores against it — one source of truth. Switching
lanes (or the live-extension "change the output" ask) is a one-file edit here.

## The 5 governed stages -> modules

| Stage | Module(s) |
|---|---|
| ① Intake | `cedx/intake/{feed,eml,pdf}.py` |
| ② Orchestration (normalize + exceptions) | `cedx/normalize/{field_map,dedup,detectors}.py` |
| ③ Assembly (fleet) | `cedx/agents/*.py`, `cedx/llm/*.py` |
| ④ Review | `cedx/review/approval.py` |
| ⑤ Delivery + Audit | `cedx/delivery/*.py`, `cedx/audit/*.py` |
