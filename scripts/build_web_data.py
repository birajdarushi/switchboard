#!/usr/bin/env python3
"""Generate web/app/audit-data.ts from the real out/audit.json.

    make demo            # produce out/audit.json
    python scripts/build_web_data.py

Keeps the Vercel dashboard driven by real pipeline output (deterministic replay),
not hand-authored sample data.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
audit = json.loads((ROOT / "out" / "audit.json").read_text())


def span(s):
    return {"agent": s["agent"], "status": s["status"], "model": s.get("model"),
            "cost_usd": s.get("cost_usd"), "verdict": s.get("verdict"),
            "retries": s.get("retries")}


def rec(r):
    df = r.get("delivered_fields") or {}
    return {
        "id": r["id"], "version": r.get("version", 1),
        "source_format": r["source_format"], "status": r["status"],
        "reason_code": r.get("reason_code"),
        "check_size": df.get("check_size"),
        "summary": df.get("summary"),
        "agent_trace": [span(s) for s in r.get("agent_trace", [])],
        "approval_trail": [{"state": a["state"], "actor": a["actor"],
                            "reason": a.get("reason")} for a in r.get("approval_trail", [])],
    }


data = {
    "case_id": audit["case_id"],
    "pipeline_version": audit["pipeline_version"],
    "amendment": audit["amendment"],
    "agents": [{"name": a["name"], "role": a["role"], "can_call": a["can_call"]}
               for a in audit["agents"]],
    "cost": audit["cost"],
    "events_count": len(audit["events"]),
    "records": [rec(r) for r in audit["records"]],
}

ts = """// AUTO-GENERATED from out/audit.json by scripts/build_web_data.py — do not edit.
export interface Span { agent: string; status: string; model?: string | null; cost_usd?: number | null; verdict?: string | null; retries?: number | null }
export interface Approval { state: string; actor: string; reason?: string | null }
export interface Rec { id: string; version: number; source_format: string; status: string; reason_code: string | null; check_size: number | null; summary?: string | null; agent_trace: Span[]; approval_trail: Approval[] }
export interface Audit { case_id: string; pipeline_version: string; amendment: { role: string; threshold: number }; agents: { name: string; role: string; can_call: string[] }[]; cost: { total_usd: number; records: number; avg_usd_per_record: number; p95_latency_ms?: number; projected_usd_per_10k: number }; events_count: number; records: Rec[] }

export const AUDIT: Audit = %s
""" % json.dumps(data, indent=2)

out = ROOT / "web" / "app" / "audit-data.ts"
out.write_text(ts, encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)} — {len(data['records'])} records, "
      f"case_id {data['case_id']}")
