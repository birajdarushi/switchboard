// AUTO-GENERATED from out/audit.json by scripts/build_web_data.py — do not edit.
export interface Span { agent: string; status: string; model?: string | null; cost_usd?: number | null; verdict?: string | null; retries?: number | null }
export interface Approval { state: string; actor: string; reason?: string | null }
export interface Rec { id: string; version: number; source_format: string; status: string; reason_code: string | null; check_size: number | null; summary?: string | null; agent_trace: Span[]; approval_trail: Approval[] }
export interface Audit { case_id: string; pipeline_version: string; amendment: { role: string; threshold: number }; agents: { name: string; role: string; can_call: string[] }[]; cost: { total_usd: number; records: number; avg_usd_per_record: number; p95_latency_ms?: number; projected_usd_per_10k: number }; events_count: number; records: Rec[] }

export const AUDIT: Audit = {
  "case_id": "CEDX-2A3D34",
  "pipeline_version": "cedx-fleet-1.0",
  "amendment": {
    "role": "risk_officer",
    "threshold": 54000.0
  },
  "agents": [
    {
      "name": "orchestrator",
      "role": "orchestrator",
      "can_call": [
        "router",
        "worker",
        "verifier"
      ]
    },
    {
      "name": "router",
      "role": "router",
      "can_call": []
    },
    {
      "name": "worker",
      "role": "worker",
      "can_call": []
    },
    {
      "name": "verifier",
      "role": "verifier",
      "can_call": []
    }
  ],
  "cost": {
    "total_usd": 0.0008475,
    "records": 23,
    "avg_usd_per_record": 4.985e-05,
    "p95_latency_ms": 0.013,
    "projected_usd_per_10k": 0.4985
  },
  "events_count": 45,
  "records": [
    {
      "id": "REC-001",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 4800.0,
      "summary": "IC memo \u2014 ONBOARDING deal led by a.shah, check size 4800.0, IC by 2026-07-15.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-002",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 5200.0,
      "summary": "IC memo \u2014 RENEWAL deal led by b.ortiz, check size 5200.0, IC by 2026-07-20.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-003",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 3900.0,
      "summary": "IC memo \u2014 REVIEW deal led by c.nguyen, check size 3900.0, IC by 2026-07-10.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-004",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 6100.0,
      "summary": "IC memo \u2014 REPORT deal led by d.kapoor, check size 6100.0, IC by 2026-08-01.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-005",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 4500.0,
      "summary": "IC memo \u2014 INTAKE deal led by e.moreau, check size 4500.0, IC by 2026-07-28.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-006",
      "version": 1,
      "source_format": "eml",
      "status": "delivered",
      "reason_code": null,
      "check_size": 5300.0,
      "summary": "IC memo \u2014 RENEWAL deal led by f.haddad, check size 5300.0, IC by 2026-07-18.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-007",
      "version": 1,
      "source_format": "pdf",
      "status": "delivered",
      "reason_code": null,
      "check_size": 4700.0,
      "summary": "IC memo \u2014 REVIEW deal led by g.silva, check size 4700.0, IC by 2026-07-22.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-008",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 5000.0,
      "summary": "IC memo \u2014 REPORT deal led by h.iqbal, check size 5000.0, IC by 2026-08-05.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-009",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 4600.0,
      "summary": "IC memo \u2014 ONBOARDING deal led by i.rossi, check size 4600.0, IC by 2026-07-30.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-010",
      "version": 1,
      "source_format": "pdf",
      "status": "delivered",
      "reason_code": null,
      "check_size": 5100.0,
      "summary": "IC memo \u2014 INTAKE deal led by j.cohen, check size 5100.0, IC by 2026-07-25.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-011",
      "version": 1,
      "source_format": "feed",
      "status": "exception",
      "reason_code": "STALE",
      "check_size": null,
      "summary": null,
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "routed",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        }
      ],
      "approval_trail": []
    },
    {
      "id": "REC-012",
      "version": 1,
      "source_format": "feed",
      "status": "exception",
      "reason_code": "MISSING_INPUT",
      "check_size": null,
      "summary": null,
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "routed",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        }
      ],
      "approval_trail": []
    },
    {
      "id": "REC-013",
      "version": 1,
      "source_format": "feed",
      "status": "exception",
      "reason_code": "OUTLIER",
      "check_size": null,
      "summary": null,
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "routed",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        }
      ],
      "approval_trail": []
    },
    {
      "id": "REC-014",
      "version": 1,
      "source_format": "eml",
      "status": "exception",
      "reason_code": "INJECTION_BLOCKED",
      "check_size": null,
      "summary": null,
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "routed",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        }
      ],
      "approval_trail": []
    },
    {
      "id": "REC-015",
      "version": 1,
      "source_format": "pdf",
      "status": "exception",
      "reason_code": "LOW_CONFIDENCE",
      "check_size": null,
      "summary": null,
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "abstained",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        }
      ],
      "approval_trail": []
    },
    {
      "id": "REC-016",
      "version": 1,
      "source_format": "eml",
      "status": "delivered",
      "reason_code": "SCHEMA_DRIFT",
      "check_size": 4750.0,
      "summary": "IC memo \u2014 RENEWAL deal led by p.larsen, check size 4750.0, IC by 2026-07-23.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-017",
      "version": 2,
      "source_format": "pdf",
      "status": "delivered",
      "reason_code": null,
      "check_size": 4650.0,
      "summary": "IC memo \u2014 REPORT deal led by q.abate, check size 4650.0, IC by 2026-07-24.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-018",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 5150.0,
      "summary": "IC memo \u2014 REVIEW deal led by r.ferreira, check size 5150.0, IC by 2026-08-03.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-019",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 4850.0,
      "summary": "IC memo \u2014 ONBOARDING deal led by s.haque, check size 4850.0, IC by 2026-07-27.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-020",
      "version": 1,
      "source_format": "feed",
      "status": "delivered",
      "reason_code": null,
      "check_size": 5250.0,
      "summary": "IC memo \u2014 REPORT deal led by t.novak, check size 5250.0, IC by 2026-08-02.",
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "verifier",
          "status": "ok",
          "model": "gpt-4o-mini",
          "cost_usd": 2.25e-05,
          "verdict": "pass",
          "retries": 0
        }
      ],
      "approval_trail": [
        {
          "state": "draft",
          "actor": "system",
          "reason": null
        },
        {
          "state": "in_review",
          "actor": "system",
          "reason": null
        },
        {
          "state": "approved",
          "actor": "operator.default",
          "reason": "operator approved"
        },
        {
          "state": "delivered",
          "actor": "system",
          "reason": null
        }
      ]
    },
    {
      "id": "REC-021",
      "version": 1,
      "source_format": "feed",
      "status": "exception",
      "reason_code": "LOW_CONFIDENCE",
      "check_size": null,
      "summary": null,
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "ok",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        },
        {
          "agent": "router",
          "status": "routed",
          "model": "gpt-4o-mini",
          "cost_usd": 0.0,
          "verdict": null,
          "retries": 0
        },
        {
          "agent": "worker",
          "status": "abstained",
          "model": "gpt-4o-mini",
          "cost_usd": 3e-05,
          "verdict": null,
          "retries": 0
        }
      ],
      "approval_trail": []
    },
    {
      "id": "REC-022",
      "version": 1,
      "source_format": "feed",
      "status": "exception",
      "reason_code": "INJECTION_BLOCKED",
      "check_size": null,
      "summary": null,
      "agent_trace": [
        {
          "agent": "orchestrator",
          "status": "routed",
          "model": null,
          "cost_usd": null,
          "verdict": null,
          "retries": null
        }
      ],
      "approval_trail": []
    },
    {
      "id": "REC-017",
      "version": 1,
      "source_format": "feed",
      "status": "superseded",
      "reason_code": "SUPERSEDED_VERSION",
      "check_size": null,
      "summary": null,
      "agent_trace": [],
      "approval_trail": []
    }
  ]
}
