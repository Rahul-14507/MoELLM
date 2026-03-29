import React, { useState, useRef, useEffect } from 'react'

const API = 'http://localhost:8000'

export default function ChatPanel({ conflicts, reasoning }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const newMessages = [...messages, { role: 'user', content: input.trim() }]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    const context = `
ORIGINAL CONFLICTS DATA:
${JSON.stringify(conflicts, null, 2)}

ORIGINAL REASONING AND BEST CHOICE:
${reasoning}
    `.trim()

    try {
      // Add empty assistant message placeholder to begin streaming
      setMessages([...newMessages, { role: 'assistant', content: '' }])
      
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
          context
        }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let assistantMsg = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n').filter(l => l.startsWith('data: '))

        for (const line of lines) {
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'token') {
              assistantMsg += event.content
              setMessages(msgs => {
                const updated = [...msgs]
                updated[updated.length - 1].content = assistantMsg
                return updated
              })
            } else if (event.type === 'error') {
               setMessages(msgs => {
                const updated = [...msgs]
                updated[updated.length - 1].content += `\n[Error: ${event.message}]`
                return updated
              })
              setLoading(false)
            } else if (event.type === 'done') {
              setLoading(false)
            }
          } catch (_) {}
        }
      }
    } catch (err) {
      setLoading(false)
    }
  }

  return (
    <div className="chat-panel section">
      <div className="section-header">
        <h2>Follow-up Questions</h2>
      </div>
      <div className="chat-container">
        <div className="chat-history">
          {messages.length === 0 && (
            <p className="chat-empty">Ask MOLLM about the best choice or alternatives.</p>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-bubble ${msg.role}`}>
              <div className="chat-bubble-content">{msg.content}</div>
            </div>
          ))}
          {loading && messages[messages.length - 1]?.content === '' && (
             <div className="chat-bubble assistant">
               <div className="chat-bubble-content"><span className="cursor">▋</span></div>
             </div>
          )}
          <div ref={chatEndRef} />
        </div>
        <form className="chat-input-area" onSubmit={handleSubmit}>
          <input 
            type="text" 
            placeholder="Why didn't you choose the alternatives?" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={!input.trim() || loading}>Send</button>
        </form>
      </div>
    </div>
  )
}
