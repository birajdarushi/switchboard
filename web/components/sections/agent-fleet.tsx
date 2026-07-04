'use client'

import { useState } from 'react'
import {
  Button,
  Grid,
  Column,
  Tile,
  Tag,
} from '@carbon/react'
import { PlayFilled } from '@carbon/icons-react'
import { AUDIT, type Rec } from '@/app/audit-data'
import styles from './agent-fleet.module.scss'

const STAGES = ['Intake', 'Orchestration', 'Assembly', 'Review', 'Delivery']

const records: Rec[] = [...AUDIT.records].sort(
  (a, b) => a.id.localeCompare(b.id) || a.version - b.version,
)

function statusTag(status: string) {
  const type = status === 'delivered' ? 'green' : status === 'superseded' ? 'cool-gray' : 'red'
  return <Tag type={type} size="sm">{status}</Tag>
}

function stagesReached(r: Rec) {
  if (r.status === 'exception') return 2
  if (r.status === 'superseded') return 1
  return 5
}

export function AgentFleet() {
  const [running, setRunning] = useState(false)
  const [stageCounts, setStageCounts] = useState([0, 0, 0, 0, 0])
  const [activeStage, setActiveStage] = useState<number | null>(null)
  const [revealed, setRevealed] = useState(records.length)
  const [selected, setSelected] = useState<number | null>(null)

  const delivered = records.filter((r) => r.status === 'delivered').length
  const exceptions = records.filter((r) => r.status === 'exception').length

  const metrics = [
    { value: delivered, label: 'IC memos delivered', highlight: true },
    { value: records.length, label: 'Deals screened' },
    { value: exceptions, label: 'Exceptions caught' },
    { value: AUDIT.events_count, label: 'Audit events' },
    { value: '0 hrs', label: 'Manual data entry' },
    { value: `$${AUDIT.cost.total_usd.toFixed(4)}`, label: 'Total run cost' },
    { value: `$${AUDIT.cost.projected_usd_per_10k.toFixed(2)}`, label: 'Projected / 10k deals' },
  ]

  const handleRun = async () => {
    setRunning(true)
    setSelected(null)
    setStageCounts([0, 0, 0, 0, 0])
    setRevealed(0)
    const counts = [0, 0, 0, 0, 0]
    for (let i = 0; i < records.length; i++) {
      await new Promise((r) => setTimeout(r, 130))
      const reached = stagesReached(records[i])
      for (let s = 0; s < reached; s++) counts[s]++
      setStageCounts([...counts])
      setActiveStage(reached - 1)
      setRevealed(i + 1)
    }
    setActiveStage(null)
    setRunning(false)
  }

  const roleTag = (role: string) => {
    const map: Record<string, 'purple' | 'teal' | 'cyan' | 'green'> = {
      orchestrator: 'purple', router: 'teal', worker: 'cyan', verifier: 'green',
    }
    return <Tag type={map[role] ?? 'gray'} size="sm">{role}</Tag>
  }

  return (
    <div className={styles.container}>
      <Grid>
        <Column lg={16} md={8} sm={4} className={styles.header}>
          <div className={styles.brandSection}>
            <div className={styles.logo}>SC</div>
            <div>
              <h1 className={styles.h1}>Switchboard Capital</h1>
              <p className={styles.subtitle}>Multi-agent IC-memo pipeline · CEDX Tiny Agent Fleet</p>
              <div className={styles.chips}>
                <Tag type="gray" size="sm">CASE_ID <span className={styles.chipValue}>{AUDIT.case_id}</span></Tag>
                <Tag type="gray" size="sm">amendment <span className={styles.chipValue}>{AUDIT.amendment.role} @ {AUDIT.amendment.threshold.toLocaleString()}</span></Tag>
                <Tag type="gray" size="sm">pipeline <span className={styles.chipValue}>{AUDIT.pipeline_version}</span></Tag>
              </div>
            </div>
          </div>
          <Button kind="primary" size="lg" disabled={running} onClick={handleRun} renderIcon={PlayFilled}>
            {running ? 'Running…' : 'Run pipeline'}
          </Button>
        </Column>

        {metrics.map((m, idx) => (
          <Column key={idx} lg={4} md={4} sm={2} className={styles.metricCol}>
            <Tile className={`${styles.metricTile} ${m.highlight ? styles.highlight : ''}`}>
              <div className={styles.metricValue}>{m.value}</div>
              <div className={styles.metricLabel}>{m.label}</div>
            </Tile>
          </Column>
        ))}

        <Column lg={16} md={8} sm={4}>
          <Tile className={styles.stagesTile}>
            <h3 className={styles.tileHeading}>5-stage governed pipeline</h3>
            <div className={styles.stages}>
              {STAGES.map((stage, idx) => (
                <div key={idx} className={`${styles.stage} ${activeStage === idx ? styles.stageActive : ''}`}>
                  <div className={styles.stageNum}>{idx + 1} · {stage}</div>
                  <div className={styles.stageCount}>{stageCounts[idx]}</div>
                </div>
              ))}
            </div>
          </Tile>
        </Column>

        <Column lg={16} md={8} sm={4}>
          <Tile className={styles.agentsTile}>
            <h3 className={styles.tileHeading}>Agent fleet</h3>
            <div className={styles.agents}>
              {AUDIT.agents.map((a) => (
                <div key={a.name} className={styles.agentCard}>
                  {roleTag(a.role)}
                  <div className={styles.agentName}>{a.name}</div>
                  <div className={styles.agentDesc}>
                    {a.can_call.length ? `can call: ${a.can_call.join(', ')}` : 'leaf agent'}
                  </div>
                </div>
              ))}
            </div>
          </Tile>
        </Column>

        <Column lg={10} md={8} sm={4}>
          <Tile className={styles.dataTile}>
            <h3 className={styles.tileHeading}>Deal records</h3>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Deal</th><th>Source</th><th>Status</th><th>Reason</th><th>Check size</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r, idx) => (
                  <tr
                    key={`${r.id}-${r.version}`}
                    className={`${styles.row} ${selected === idx ? styles.selectedRow : ''}`}
                    style={{ opacity: idx < revealed ? 1 : 0.15 }}
                    onClick={() => setSelected(idx)}
                  >
                    <td><strong>{r.id}</strong>{r.version > 1 ? ` v${r.version}` : ''}</td>
                    <td className={styles.mono}>{r.source_format}</td>
                    <td>{statusTag(r.status)}</td>
                    <td className={styles.mono}>{r.reason_code ?? '—'}</td>
                    <td>{r.check_size != null ? `$${r.check_size.toLocaleString()}` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Tile>
        </Column>

        <Column lg={6} md={8} sm={4}>
          <Tile className={styles.traceTile}>
            <h3 className={styles.tileHeading}>Agent trace</h3>
            {selected !== null ? (
              <div className={styles.trace}>
                <div className={styles.traceHead}>
                  <strong>{records[selected].id}</strong> {statusTag(records[selected].status)}{' '}
                  <span className={styles.mono}>{records[selected].reason_code ?? ''}</span>
                </div>
                {records[selected].agent_trace.map((s, i) => (
                  <div key={i} className={styles.traceStep}>
                    <div className={`${styles.dot} ${styles['dot_' + s.status] ?? ''}`}></div>
                    <div className={styles.traceContent}>
                      <div><strong>{s.agent}</strong> <span className={styles.status}>{s.status}</span>
                        {s.verdict && <span className={styles.verdict}> · verdict <strong>{s.verdict}</strong></span>}
                      </div>
                      <div className={styles.mono}>{s.model ?? '—'}{s.cost_usd ? ` · $${s.cost_usd.toFixed(6)}` : ''}</div>
                    </div>
                  </div>
                ))}
                {records[selected].approval_trail.length > 0 && (
                  <div className={styles.approvals}>
                    <div className={styles.mono}>approval chain</div>
                    {records[selected].approval_trail.map((a, i) => (
                      <div key={i} className={styles.appr}>→ <strong>{a.state}</strong> by {a.actor}{a.reason ? ` · ${a.reason}` : ''}</div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className={styles.empty}>Select a deal to see its full agent decision path.</div>
            )}
          </Tile>
        </Column>
      </Grid>
    </div>
  )
}
