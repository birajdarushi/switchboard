# Running the fleet on YOUR OWN data

The pipeline reads whatever directory `SEED_DIR` points at. `examples/mydata/` is a
ready-to-edit sample. Copy it, change the records, and run.

## 1. Where to put input

```
examples/mydata/
├── feed.json          # required: JSON array of records
└── inbox/             # optional: one .eml or .pdf per record
    ├── MY-009.eml     # uses "Value:" instead of "Amount:" -> SCHEMA_DRIFT
    └── MY-003_v2.eml  # same id as a feed record, higher version -> SUPERSEDED_VERSION
```

### feed.json record shape
```json
{ "id": "MY-001", "owner": "alice", "deadline": "2026-07-15",
  "category": "ONBOARDING", "amount": 5000, "notes": "…", "version": 1 }
```

### .eml / .pdf shape
A body of `Key: Value` lines: `Id, Owner, Deadline, Amount` (or `Value`), `Category,
Version, Notes`.

## 2. What triggers each outcome (so you can craft test cases)
| To get… | Do this in a record |
|---|---|
| delivered | valid record, amount in a normal range |
| STALE | `deadline` before `PIPELINE_NOW` (default 2026-06-26) |
| MISSING_INPUT | `amount: null` (or no owner/deadline) |
| OUTLIER | one `amount` far from the rest (needs ≥3 records) |
| INJECTION_BLOCKED | imperative in `notes` ("ignore previous instructions", "approve now") |
| LOW_CONFIDENCE | ambiguous `category` ("?") or contradictory notes |
| SCHEMA_DRIFT | use `Value:` instead of `Amount:` in an .eml/.pdf |
| SUPERSEDED_VERSION | same `id` twice with a higher `version` |

## 3. Steps to run

```bash
export CASE_ID=CEDX-2A3D34                      # your live-assigned id
D=examples/mydata

# (a) first time on NEW data: generate replay transcripts (offline, no key)
SEED_DIR=$D make record

# (b) run the fleet + gate
SEED_DIR=$D make demo
SEED_DIR=$D make verify

# (c) inspect a single record end-to-end
make trace  ID=MY-006      # the outlier
make replay ID=MY-001      # a delivered record's data lineage
```

Real LLM instead of replay (needs a key):
```bash
REPLAY_LLM=false LLM_API_KEY=sk-... LLM_MODEL=gpt-4o-mini SEED_DIR=$D make demo
```

## 4. Where the output goes
```
out/package.json           # branded deliverables (all delivered records)
out/audit.json             # full audit: agents, per-record agent_trace, cost, events
out/exception_queue.json   # every routed record + reason_code
```

> Tip: `make record` and `make demo` must use the SAME `SEED_DIR`. Replay only has
> transcripts for records it has already seen, so re-run `make record` whenever you
> change the input data (or use the real-LLM path).

## 5. Note on `make verify` with custom data
`verify_audit.py` defaults to requiring the dev-seed reason codes (incl.
`LOW_CONFIDENCE`). If your dataset doesn't contain, say, an ambiguous record, `verify`
will report `required reason codes not present` — that's the gate's required-set check,
not a pipeline error. Either include one record per code you want to prove (this sample
does), or override the required set:
```bash
python verify_audit.py --audit out/audit.json --transcripts transcripts \
  --schema audit.schema.json --require STALE MISSING_INPUT OUTLIER INJECTION_BLOCKED
```
