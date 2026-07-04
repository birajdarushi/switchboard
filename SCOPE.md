# SCOPE — push this during the live call (tracer checkpoint)

> Rename to `SCOPE.md`, fill in, commit + push during the Zoom. We record your
> GitHub **push receive-time** server-side as your authorship anchor.

- **Candidate name:** Rushiraj Birajdar
- **CASE_ID (assigned live):** CEDX-2A3D34
- **Industry chosen (from cedxsystems.com/workflows):** Venture Capital Firms — IC-ready investment memo pipeline (branded "Switchboard Capital")
- **Tier:** _<tier from the workflows page>_
- **Stack / language:** Python 3.11 (pydantic, jsonschema, pypdf; stdlib urllib for LLM)

## Amendment (compute from your CASE_ID)
```
H = sha256(CASE_ID)
role R      = ["risk_officer","legal_counsel","compliance","finance_controller"][ int(H[0],16) % 4 ]
threshold T = 10000 + (int(H[1:3],16) % 50) * 1000
```
- **My role R:** risk_officer
- **My threshold T:** 54000

## What I will build (the 5 governed stages)
- [x] Sources/Intake (parse feed.json + inbox PDF/email)
- [x] Orchestration (declarative normalize + exception queue, all reason codes)
- [x] Assembly (LLM structured output + abstain path)
- [x] Review (operator surface + approval state machine + my CASE_ID amendment)
- [x] Delivery (branded package + append-only audit + replay)

## What I will deliberately NOT build (and why)
- **A web UI / frontend** — the operator surface is CLI, per the brief; UI would burn time
  with zero rubric value.
- **PDF OCR for scanned images** — out of scope; unparseable records route to the exception
  queue rather than being dropped.
- **Auto-approval of the human review step** — governance requires a recorded human decision;
  automating it would defeat the point.
