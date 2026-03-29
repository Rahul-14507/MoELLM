import React from 'react'

const LATENCY_LABELS = ['< 1s', '2s', '5s', '10s', '20s+']
const COST_LABELS = ['$0.001', '$0.005', '$0.02', '$0.05', '$0.20']

export default function QueryPanel({ form, models, tasks, onChange, onRun, loading, error }) {
  return (
    <div className="panel panel-query">
      <div className="panel-header">
        <span className="panel-num">01</span>
        <h2>Inputs</h2>
      </div>

      <div className="field">
        <label>User query</label>
        <textarea
          rows={3}
          value={form.query}
          onChange={e => onChange('query', e.target.value)}
          placeholder="What is retrieval-augmented generation?"
        />
      </div>

      <div className="field">
        <label>Task type</label>
        <select value={form.task} onChange={e => onChange('task', e.target.value)}>
          {Object.entries(tasks).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      <div className="field">
        <label>Preferred model</label>
        <select value={form.user_preferred_model} onChange={e => onChange('user_preferred_model', e.target.value)}>
          {Object.entries(models).map(([k, m]) => (
            <option key={k} value={k}>{m.display_name}</option>
          ))}
        </select>
      </div>

      <div className="divider" />

      <p className="section-label">System constraints</p>

      <div className="slider-row">
        <label>Max latency</label>
        <input type="range" min={1} max={5} step={1} value={form.max_latency_tier}
          onChange={e => onChange('max_latency_tier', +e.target.value)} />
        <span className="slider-val">{LATENCY_LABELS[form.max_latency_tier - 1]}</span>
      </div>

      <div className="slider-row">
        <label>Max cost</label>
        <input type="range" min={1} max={5} step={1} value={form.max_cost_tier}
          onChange={e => onChange('max_cost_tier', +e.target.value)} />
        <span className="slider-val">{COST_LABELS[form.max_cost_tier - 1]}</span>
      </div>

      <div className="toggle-row">
        <label>Privacy mode</label>
        <button
          className={`toggle-btn ${form.privacy_required ? 'active' : ''}`}
          onClick={() => onChange('privacy_required', !form.privacy_required)}
        >
          {form.privacy_required ? 'ON' : 'OFF'}
        </button>
      </div>

      <div className="divider" />

      <p className="section-label">Priority weights</p>

      {[
        ['weight_accuracy', 'Accuracy'],
        ['weight_speed',    'Speed'],
        ['weight_cost',     'Cost'],
        ['weight_privacy',  'Privacy'],
      ].map(([key, label]) => (
        <div className="slider-row" key={key}>
          <label>{label}</label>
          <input type="range" min={0} max={10} step={1} value={form[key]}
            onChange={e => onChange(key, +e.target.value)} />
          <span className="slider-val">{form[key]}</span>
        </div>
      ))}

      {error && <p className="error-msg">{error}</p>}

      <button className="run-btn" onClick={onRun} disabled={loading}>
        {loading ? 'Resolving…' : 'Resolve & Run ↗'}
      </button>
    </div>
  )
}
