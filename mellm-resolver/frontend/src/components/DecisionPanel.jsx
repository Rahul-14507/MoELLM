import React from 'react'

export default function DecisionPanel({ resolution, loading }) {
  if (!resolution && !loading) return (
    <div className="panel panel-decision">
      <div className="panel-header">
        <span className="panel-num">03</span>
        <h2>Resolution</h2>
      </div>
      <div className="placeholder-text">Decision appears here after resolve.</div>
    </div>
  )

  return (
    <div className="panel panel-decision">
      <div className="panel-header">
        <span className="panel-num">03</span>
        <h2>Resolution</h2>
      </div>

      {loading && !resolution && <div className="placeholder-text">Computing…</div>}

      {resolution && (
        <>
          <div className="decision-winner">
            <p className="decision-label">MELLM routes to</p>
            <p className="decision-model">{resolution.winner_name}</p>
            <div className="conf-row">
              <span className="conf-label">Confidence {resolution.confidence}%</span>
              <span className={`pref-badge ${resolution.preference_honoured ? 'honoured' : 'overridden'}`}>
                {resolution.preference_honoured ? 'Preference honoured' : 'Preference overridden'}
              </span>
            </div>
            <div className="conf-bar-bg">
              <div className="conf-bar-fill" style={{ width: resolution.confidence + '%' }} />
            </div>
          </div>

          <div className="why-section">
            <p className="section-label">Why this constraint mattered more</p>
            {resolution.dimension_scores.map(d => {
              const maxWS = Math.max(...resolution.dimension_scores.map(x => x.weighted_score))
              const pct = Math.round((d.weighted_score / maxWS) * 100)
              return (
                <div className="why-row" key={d.name}>
                  <span className="why-name">{d.name}</span>
                  <div className="why-bar-bg">
                    <div className="why-bar-fill" style={{ width: pct + '%', background: d.color }} />
                  </div>
                  <span className="why-score">{Math.round(d.weighted_score)}</span>
                </div>
              )
            })}
          </div>

          <div className="verdict-box">
            <p>{resolution.verdict}</p>
          </div>
        </>
      )}
    </div>
  )
}
