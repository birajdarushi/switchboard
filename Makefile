# Uniform probe interface — graders invoke THESE targets identically on every repo,
# whatever language you build in. Wire each to your implementation. Exit codes matter.
# v2: adds agent-fleet targets (trace, eval, probe-agent-failure, probe-budget).
SEED_DIR ?= seed
# PY lets local dev use the venv (make demo PY=./.venv/bin/python); Docker uses python3.
PY ?= python3

.PHONY: demo record verify trace eval replay probe-approval probe-agent-failure probe-budget \
        probe-append-only probe-idempotency probe-crash clean

# Full multi-agent pipeline, offline replay, on $(SEED_DIR). Writes out/package.json,
# out/audit.json (agents roster + per-record agent_trace + cost), out/exception_queue.json.
demo:
	REPLAY_LLM=true SEED_DIR=$(SEED_DIR) $(PY) -m cedx demo

# Regenerate committed transcripts from the deterministic dev generator (offline, no key).
# For the REAL path use: REPLAY_LLM=false LLM_API_KEY=... make record
record:
	REPLAY_LLM=false ALLOW_FAKE_LLM=1 SEED_DIR=$(SEED_DIR) $(PY) -m cedx record

# Run the PROVIDED gate on your audit bundle. Do not modify verify_audit.py.
verify:
	$(PY) verify_audit.py --audit out/audit.json --transcripts transcripts --schema audit.schema.json

# Print one record's FULL agent decision path from the log alone.
trace:
	$(PY) -m cedx trace $(ID)

# Run your agent eval harness: >=10 golden cases + an LLM-judge per agent. Print per-agent scores.
eval:
	$(PY) -m cedx eval

# Reconstruct one delivered output's DATA lineage from the append-only log alone.
replay:
	$(PY) -m cedx replay $(ID)

# Exit 0 ONLY if delivery of a NON-approved item (incl. CASE_ID amendment role) is refused + logged.
probe-approval:
	$(PY) -m cedx probe approval

# Exit 0 ONLY if a hallucinated/malformed WORKER output is caught by the Verifier and routed
# (AGENT_HALLUCINATION / AGENT_MALFORMED) — never delivered.
probe-agent-failure:
	$(PY) -m cedx probe agent-failure

# Exit 0 ONLY if a record exceeding the per-record cost/step ceiling raises BUDGET_EXCEEDED
# and is downgraded or routed — never silently overspent.
probe-budget:
	$(PY) -m cedx probe budget

# Exit 0 ONLY if mutating/deleting a past audit entry is refused.
probe-append-only:
	$(PY) -m cedx probe append-only

# Exit 0 ONLY if running demo twice produces no duplicate outputs/exceptions/approvals.
probe-idempotency:
	$(PY) -m cedx probe idempotency

# BONUS. Exit 0 if the pipeline resumes from the last completed stage after a SIGKILL.
probe-crash:
	$(PY) -m cedx probe crash

clean:
	rm -rf out
