import React from 'react'

const SEVERITY_COLOR = { hard: '#E24B4A', soft: '#EF9F27' }
const DIM_ICONS = {
  latency: '⏱',
  privacy: '🔒',
  task_fit: '⚙',
  cost: '$',
}

export default function ConflictPanel({ resolution, loading }) {
  return (
    <div className="panel panel-conflicts">
      <div className="panel-header">
        <span className="panel-num">02</span>
        <h2>Detected conflicts</h2>
      </div>

      {loading && !resolution && (
        <div className="placeholder-text">Analyzing conflicts…</div>
      )}

      {!resolution && !loading && (
        <div className="placeholder-text">Conflicts appear here after you submit a query.</div>
      )}

      {resolution && resolution.conflicts.length === 0 && (
        <div className="no-conflict">
          <span className="dot" style={{ background: '#639922' }} />
          No major conflicts — preference aligns with all constraints.
        </div>
      )}

      {resolution && resolution.conflicts.map((c, i) => (
        <div className="conflict-card" key={i}>
          <div className="conflict-header">
            <span className="conflict-dot" style={{ background: SEVERITY_COLOR[c.severity] }} />
            <span className="conflict-dim">{DIM_ICONS[c.dimension] || '!'} {c.dimension.replace('_', ' ')}</span>
            <span className={`severity-badge ${c.severity}`}>{c.severity}</span>
          </div>
          <p className="conflict-desc">{c.description}</p>
          {c.penalty > 0 && (
            <p className="conflict-penalty">− {c.penalty} pts penalty applied</p>
          )}
        </div>
      ))}

      {resolution && (
        <div className="all-scores">
          <p className="section-label">All model scores</p>
          {Object.entries(resolution.all_scores || {})
            .sort((a, b) => b[1] - a[1])
            .map(([id, score]) => {
              const maxScore = Math.max(...Object.values(resolution.all_scores))
              const pct = Math.round((score / maxScore) * 100)
              return (
                <div className="score-row" key={id}>
                  <span className="score-name">{id}</span>
                  <div className="score-bar-bg">
                    <div className="score-bar-fill" style={{ width: pct + '%', background: id === resolution.winner_id ? '#378ADD' : '#888780' }} />
                  </div>
                  <span className="score-val">{score}</span>
                </div>
              )
            })}
        </div>
      )}
    </div>
  )
}
