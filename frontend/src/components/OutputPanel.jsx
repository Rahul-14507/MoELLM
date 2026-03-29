import React, { useRef, useEffect, useState } from 'react'
import ChatPanel from './ChatPanel.jsx'

const SEVERITY_COLOR = { hard: '#E24B4A', soft: '#EF9F27' }
const CONSTRAINT_LABELS = {
  budget: '💰 Budget',
  availability: '📍 Availability',
  brand: '🏷 Brand',
  screen: '🖥 Screen',
}

export default function OutputPanel({ conflicts, reasoning, loading, done, error }) {
  const reasonRef = useRef(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (reasonRef.current) reasonRef.current.scrollTop = reasonRef.current.scrollHeight
  }, [reasoning])

  const hardConflictCount = conflicts.reduce((sum, ev) =>
    sum + ev.conflicts.filter(c => c.severity === 'hard').length, 0)

  // Detect winning product from "BEST CHOICE:" in reasoning
  const winnerMatch = reasoning.match(/BEST CHOICE:\s*(.+)/i)
  const winnerName = winnerMatch ? winnerMatch[1].trim().toLowerCase() : null

  const copyVerdict = () => {
    if (!reasoning) return
    navigator.clipboard.writeText(reasoning).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="output-panel">

      {/* Conflict breakdown */}
      {conflicts.length > 0 && (
        <div className="section">
          <div className="section-header">
            <h2>Detected Conflicts</h2>
            {hardConflictCount > 0 && (
              <span className="badge-hard">{hardConflictCount} hard conflict{hardConflictCount > 1 ? 's' : ''}</span>
            )}
          </div>

          <div className="conflicts-grid">
            {conflicts.map((ev, i) => {
              const isWinner = done && winnerName && ev.product_title.toLowerCase().includes(winnerName.slice(0, 20))
              return (
                <div key={i} className={`product-card ${ev.passes ? 'passes' : 'fails'} ${isWinner ? 'winner' : ''}`}>
                  <div className="product-card-header">
                    <span className={`pass-badge ${ev.passes ? 'pass' : 'fail'}`}>
                      {ev.passes ? '✓ Viable' : '✗ Blocked'}
                    </span>
                    {isWinner && <span className="winner-badge">★ Recommended</span>}
                    <span className="product-score">Match: {Math.round(ev.match_score)}%</span>
                  </div>
                  <p className="product-title">{ev.product_title}</p>
                  <p className="product-price">${ev.product_price?.toFixed(2)}</p>

                  {ev.conflicts.length === 0 ? (
                    <p className="no-conflict-msg">No conflicts — satisfies all constraints</p>
                  ) : (
                    <div className="conflict-list">
                      {ev.conflicts.map((c, j) => (
                        <div key={j} className="conflict-row">
                          <span className="conflict-dot" style={{ background: SEVERITY_COLOR[c.severity] }} />
                          <div>
                            <span className="conflict-label">
                              {CONSTRAINT_LABELS[c.constraint] || c.constraint}
                            </span>
                            <span className={`sev-tag ${c.severity}`}>{c.severity}</span>
                            <p className="conflict-desc">{c.description}</p>
                            <p className="conflict-detail">
                              Expected: <em>{c.expected}</em> → Got: <em>{c.actual}</em>
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* LLM Reasoning stream */}
      {(reasoning || loading) && (
        <div className="section">
          <div className="section-header">
            <h2>Resolution Reasoning</h2>
            <span className="model-tag">Qwen2.5-7B-Instruct</span>
            {loading && <span className="live-dot" />}
            {done && reasoning && (
              <button className="copy-btn" onClick={copyVerdict}>
                {copied ? '✓ Copied' : 'Copy verdict'}
              </button>
            )}
          </div>
          <div className="reasoning-box" ref={reasonRef}>
            {!reasoning && loading && (
              <span className="reasoning-placeholder">Waiting for Qwen…</span>
            )}
            <div className="reasoning-text">
              {reasoning.split('\n').map((line, i) => {
                const isBestChoice = line.toUpperCase().startsWith('BEST CHOICE:')
                
                let productUrl = null
                if (isBestChoice && winnerName) {
                  const winningConflict = conflicts.find(ev => ev.product_title.toLowerCase().includes(winnerName.slice(0, 20)))
                  productUrl = winningConflict?.product_url
                }

                return (
                  <div key={i} className={isBestChoice ? 'best-choice-highlight' : 'reasoning-line'}>
                    {isBestChoice && productUrl && productUrl !== '#' ? (
                      <>
                        BEST CHOICE: <a href={productUrl} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>{line.replace(/^BEST CHOICE:\s*/i, '')}</a>
                      </>
                    ) : (
                      line
                    )}
                  </div>
                )
              })}
            </div>
            {loading && reasoning && <span className="cursor">▋</span>}
          </div>
        </div>
      )}

      {error && (
        <div className="error-box">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Follow-up Chatbot */}
      {done && reasoning && !error && (
        <ChatPanel conflicts={conflicts} reasoning={reasoning} />
      )}
    </div>
  )
}
