"""cedx.__main__ — CLI dispatch. The Makefile targets shell into this.

    python -m cedx demo      full fleet on SEED_DIR -> out/{package,audit,exception_queue}
    python -m cedx trace ID  print one record's full agent decision path
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from cedx import config
from cedx.agents.base import roster
from cedx.agents.orchestrator import Orchestrator
from cedx.audit.log import EventLog, build_audit, write_audit
from cedx.contracts import RecordStatus
from cedx.delivery.package import build_package


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_demo(cfg, out_dir="out", transcripts_dir="transcripts") -> int:
    print(f"AMENDMENT: role={cfg.amendment_role} threshold={cfg.amendment_threshold}")
    print(f"[demo] SEED_DIR={cfg.seed_dir} REPLAY_LLM={cfg.replay_llm} "
          f"CASE_ID={cfg.case_id}")

    log = EventLog()
    orch = Orchestrator(cfg, transcripts_dir)
    records, delivered_items = orch.run(log, checkpoint_path=f"{out_dir}/.checkpoint.jsonl")

    package_hash = build_package(cfg, delivered_items, out_dir)
    audit = build_audit(cfg, roster(cfg), records, log.events, package_hash, _now())
    write_audit(audit, out_dir)

    exceptions = [r for r in records if r.status == RecordStatus.exception]
    Path(out_dir, "exception_queue.json").write_text(
        json.dumps([{"id": r.id, "reason_code": r.reason_code.value if r.reason_code else None,
                     "reason_class": r.reason_class.value if r.reason_class else None}
                    for r in exceptions], indent=2), encoding="utf-8")

    delivered = [r for r in records if r.status == RecordStatus.delivered]
    superseded = [r for r in records if r.status == RecordStatus.superseded]
    print(f"[demo] {len(records)} records: {len(delivered)} delivered, "
          f"{len(exceptions)} exceptions, {len(superseded)} superseded")
    for r in sorted(exceptions, key=lambda x: x.id):
        print(f"        EXC {r.id}: {r.reason_code.value}")
    print(f"[demo] wrote {out_dir}/package.json, audit.json, exception_queue.json")
    return 0


def cmd_trace(cfg, rec_id: str, out_dir="out") -> int:
    audit = json.loads(Path(out_dir, "audit.json").read_text())
    rec = next((r for r in audit["records"] if r["id"] == rec_id), None)
    if rec is None:
        print(f"no record {rec_id}")
        return 1
    print(f"=== trace {rec_id} — status={rec['status']} "
          f"reason={rec.get('reason_code')} ===")
    for i, sp in enumerate(rec.get("agent_trace", [])):
        v = f" verdict={sp['verdict']}" if sp.get("verdict") else ""
        print(f"  [{i}] {sp['agent']:12} status={sp['status']:9} "
              f"model={sp.get('model')} cost=${sp.get('cost_usd') or 0:.6f}{v}")
    for a in rec.get("approval_trail", []):
        print(f"  approval: {a['state']:10} by {a['actor']} — {a.get('reason') or ''}")
    return 0


def cmd_replay(cfg, rec_id: str, out_dir="out") -> int:
    """Reconstruct a delivered record's DATA lineage from the append-only log alone."""
    audit = json.loads(Path(out_dir, "audit.json").read_text())
    rec = next((r for r in audit["records"] if r["id"] == rec_id), None)
    if rec is None:
        print(f"no record {rec_id}")
        return 1
    print(f"=== lineage {rec_id} ===")
    print(f"  source_format:        {rec.get('source_format')}")
    print(f"  source_version_hash:  {rec.get('source_version_hash')}")
    print(f"  status:               {rec.get('status')}  reason={rec.get('reason_code')}")
    print(f"  transcript_hash:      {rec.get('transcript_hash')}")
    print(f"  delivered_fields_hash:{rec.get('delivered_fields_hash')}")
    if rec.get("delivered_fields"):
        print(f"  delivered_fields:     {json.dumps(rec['delivered_fields'])}")
    ev = [e for e in audit["events"] if e.get("record_id") == rec_id]
    print(f"  events ({len(ev)}):")
    for e in ev:
        print(f"     seq={e['seq']:3} {e['action']} by {e['actor']}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cedx")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    sub.add_parser("record")  # same as demo; env (REPLAY_LLM=false) drives recording
    tp = sub.add_parser("trace")
    tp.add_argument("id")
    rp = sub.add_parser("replay")
    rp.add_argument("id")
    pp = sub.add_parser("probe")
    pp.add_argument("name")
    sub.add_parser("eval")
    args = ap.parse_args(argv)

    cfg = config.load()
    if args.cmd in ("demo", "record"):
        return cmd_demo(cfg)
    if args.cmd == "trace":
        return cmd_trace(cfg, args.id)
    if args.cmd == "replay":
        return cmd_replay(cfg, args.id)
    if args.cmd == "probe":
        from cedx import probes
        return probes.run(args.name, cfg)
    if args.cmd == "eval":
        from cedx import evaluation
        return evaluation.run(cfg)
    return 2


if __name__ == "__main__":
    sys.exit(main())
