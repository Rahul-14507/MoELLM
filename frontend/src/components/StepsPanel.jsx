import React from 'react'

const STEPS = [
  { id: 'scraping',   label: 'Scraping live market data',   icon: '⬡' },
  { id: 'conflicts',  label: 'Detecting conflicts',          icon: '⬡' },
  { id: 'resolving',  label: 'Resolving with Qwen AI',       icon: '⬡' },
  { id: 'done',       label: 'Resolution complete',          icon: '⬡' },
]

export default function StepsPanel({ currentStep, stepMessage, productCount }) {
  const currentIndex = STEPS.findIndex(s => s.id === currentStep)

  return (
    <div className="steps-panel">
      <div className="steps-track">
        {STEPS.map((step, i) => {
          const isDone = i < currentIndex || currentStep === 'done'
          const isActive = step.id === currentStep
          return (
            <div key={step.id} className={`step-item ${isDone ? 'done' : ''} ${isActive ? 'active' : ''}`}>
              <div className="step-dot">
                {isDone ? '✓' : isActive ? <span className="step-pulse" /> : '·'}
              </div>
              <span className="step-label">{step.label}</span>
              {i < STEPS.length - 1 && <div className={`step-line ${isDone ? 'done' : ''}`} />}
            </div>
          )
        })}
      </div>
      {stepMessage && (
        <p className="step-message">
          {stepMessage}
          {productCount > 0 && currentStep === 'conflicts' && ` Evaluating ${productCount} products.`}
        </p>
      )}
    </div>
  )
}
