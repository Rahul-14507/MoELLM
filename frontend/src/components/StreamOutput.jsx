import React, { useRef, useEffect } from 'react'

export default function StreamOutput({ tokens, modelName, loading }) {
  const ref = useRef(null)

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [tokens])

  return (
    <div className="stream-panel">
      <div className="stream-header">
        <span className="stream-model">{modelName || '—'}</span>
        <span className="stream-label">Model response</span>
        {loading && <span className="blink-dot" />}
      </div>
      <div className="stream-body" ref={ref}>
        {loading && !tokens && <span className="stream-placeholder">Waiting for response…</span>}
        <span className="stream-text">{tokens}</span>
        {loading && tokens && <span className="cursor">▋</span>}
      </div>
    </div>
  )
}
