import React, { useState, useEffect } from 'react'
import QueryPanel from './components/QueryPanel.jsx'
import ConflictPanel from './components/ConflictPanel.jsx'
import DecisionPanel from './components/DecisionPanel.jsx'
import StreamOutput from './components/StreamOutput.jsx'

const API = 'http://localhost:8000'

const DEFAULT_FORM = {
  query: '',
  task: 'rag',
  user_preferred_model: 'qwen-plus',
  max_latency_tier: 3,
  max_cost_tier: 3,
  privacy_required: false,
  weight_accuracy: 8,
  weight_speed: 6,
  weight_cost: 5,
  weight_privacy: 4,
}

export default function App() {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [models, setModels] = useState({})
  const [tasks, setTasks] = useState({})
  const [resolution, setResolution] = useState(null)
  const [streamTokens, setStreamTokens] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API}/models`).then(r => r.json()).then(setModels)
    fetch(`${API}/tasks`).then(r => r.json()).then(setTasks)
  }, [])

  const handleChange = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const handleRun = async () => {
    if (!form.query.trim()) { setError('Enter a query first'); return }
    setError('')
    setLoading(true)
    setResolution(null)
    setStreamTokens('')

    try {
      const res = await fetch(`${API}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '))
        for (const line of lines) {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'resolution') setResolution(event)
          else if (event.type === 'token') setStreamTokens(t => t + event.content)
        }
      }
    } catch (e) {
      setError('API error: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <span className="logo-tag">MELLM</span>
          <h1>Multi-Context Conflict Resolver</h1>
        </div>
        <div className="header-right">
          <span className="subtitle">Route intelligently. Justify every decision.</span>
        </div>
      </header>

      <main className="app-main">
        <div className="panel-grid">
          <QueryPanel
            form={form}
            models={models}
            tasks={tasks}
            onChange={handleChange}
            onRun={handleRun}
            loading={loading}
            error={error}
          />
          <ConflictPanel resolution={resolution} loading={loading} />
          <DecisionPanel resolution={resolution} loading={loading} />
        </div>

        {(streamTokens || (loading && resolution)) && (
          <StreamOutput
            tokens={streamTokens}
            modelName={resolution?.winner_name}
            loading={loading && !streamTokens}
          />
        )}
      </main>
    </div>
  )
}
