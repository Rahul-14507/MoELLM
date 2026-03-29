import React from 'react'

const PREFERENCE_EXAMPLE = 'I want a high-end gaming laptop, preferably ASUS, with an OLED screen.'
const CONSTRAINT_EXAMPLE = 'Budget is max $1,200. Must be available for store pickup today.'

export default function InputPanel({
  preference, constraints,
  onPreferenceChange, onConstraintsChange,
  onResolve, loading
}) {
  const fillExample = () => {
    onPreferenceChange(PREFERENCE_EXAMPLE)
    onConstraintsChange(CONSTRAINT_EXAMPLE)
  }

  return (
    <div className="input-panel">
      <div className="input-grid">
        <div className="input-box">
          <div className="input-box-header">
            <span className="box-label-num">A</span>
            <div>
              <p className="box-label">Your Preferences</p>
              <p className="box-hint">What you want — brand, features, type</p>
            </div>
          </div>
          <textarea
            value={preference}
            onChange={e => onPreferenceChange(e.target.value)}
            placeholder={PREFERENCE_EXAMPLE}
            rows={4}
            disabled={loading}
          />
        </div>

        <div className="input-box">
          <div className="input-box-header">
            <span className="box-label-num">B</span>
            <div>
              <p className="box-label">Your Constraints</p>
              <p className="box-hint">Hard limits — budget, timing, location</p>
            </div>
          </div>
          <textarea
            value={constraints}
            onChange={e => onConstraintsChange(e.target.value)}
            placeholder={CONSTRAINT_EXAMPLE}
            rows={4}
            disabled={loading}
          />
        </div>
      </div>

      <div className="input-actions">
        <button className="example-btn" onClick={fillExample} disabled={loading}>
          Try an example
        </button>
        <button
          className="resolve-btn"
          onClick={onResolve}
          disabled={loading || !preference.trim() || !constraints.trim()}
        >
          {loading ? (
            <><span className="spinner" /> Resolving…</>
          ) : (
            'Resolve Conflicts ↗'
          )}
        </button>
      </div>
    </div>
  )
}
