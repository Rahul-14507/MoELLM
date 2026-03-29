import React, { useState } from 'react'
import InputPanel from './components/InputPanel.jsx'
import StepsPanel from './components/StepsPanel.jsx'
import OutputPanel from './components/OutputPanel.jsx'

const API = 'http://localhost:8000'

const INITIAL_STATE = {
  step: null,          // null | 'scraping' | 'conflicts' | 'resolving' | 'done' | 'error'
  stepMessage: '',
  products: [],
  conflicts: [],
  reasoning: '',
  error: '',
}

export default function App() {
  const [preference, setPreference] = useState('')
  const [constraints, setConstraints] = useState('')
  const [state, setState] = useState(INITIAL_STATE)
  const [loading, setLoading] = useState(false)

  const handleResolve = async () => {
    if (!preference.trim() || !constraints.trim()) return
    setLoading(true)
    setState(INITIAL_STATE)

    try {
      const res = await fetch(`${API}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preference, constraints }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n').filter(l => l.startsWith('data: '))

        for (const line of lines) {
          try {
            const event = JSON.parse(line.slice(6))

            if (event.type === 'step') {
              setState(s => ({ ...s, step: event.step, stepMessage: event.message }))
            } else if (event.type === 'products') {
              setState(s => ({ ...s, products: event.data }))
            } else if (event.type === 'conflicts') {
              setState(s => ({ ...s, conflicts: event.data }))
            } else if (event.type === 'token') {
              setState(s => ({ ...s, reasoning: s.reasoning + event.content }))
            } else if (event.type === 'done') {
              setState(s => ({ ...s, step: 'done' }))
              setLoading(false)
            } else if (event.type === 'error') {
              setState(s => ({ ...s, step: 'error', error: event.message }))
              setLoading(false)
            }
          } catch (_) {}
        }
      }
    } catch (e) {
      setState(s => ({ ...s, step: 'error', error: e.message }))
      setLoading(false)
    }
  }

  const hasOutput = state.conflicts.length > 0 || state.reasoning

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <span className="logo-tag">MELLM</span>
          <div>
            <h1>Multi-Context Conflict Resolver</h1>
            <p className="header-sub">Real preferences. Real market data. Real conflicts. Resolved.</p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <InputPanel
          preference={preference}
          constraints={constraints}
          onPreferenceChange={setPreference}
          onConstraintsChange={setConstraints}
          onResolve={handleResolve}
          loading={loading}
        />

        {(loading || state.step) && (
          <StepsPanel
            currentStep={state.step}
            stepMessage={state.stepMessage}
            productCount={state.products.length}
          />
        )}

        {hasOutput && (
          <OutputPanel
            conflicts={state.conflicts}
            reasoning={state.reasoning}
            loading={loading}
            done={state.step === 'done'}
            error={state.error}
          />
        )}
      </main>
    </div>
  )
}
