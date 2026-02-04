import React, { useState } from 'react'

const ChatInput = ({ onSend, isStreaming }) => {
  const [message, setMessage] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [temperature, setTemperature] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!message.trim()) return
    onSend({ message, systemPrompt, temperature })
    setMessage('')
  }

  return (
    <form className="chat-footer" onSubmit={handleSubmit}>
      <div className="input-row" style={{ marginBottom: 12 }}>
        <textarea
          placeholder="System prompt (optional)"
          value={systemPrompt}
          onChange={(event) => setSystemPrompt(event.target.value)}
          rows={2}
        />
        <input
          type="number"
          step="0.1"
          min="0"
          max="1"
          placeholder="Temp"
          value={temperature}
          onChange={(event) => setTemperature(event.target.value)}
          style={{ width: 90, borderRadius: 12, border: '1px solid #d0d7e2', padding: '12px 10px' }}
        />
      </div>
      <div className="input-row">
        <textarea
          placeholder="Type your message..."
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          rows={3}
          disabled={isStreaming}
        />
        <button type="submit" disabled={isStreaming}>
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </div>
    </form>
  )
}

export default ChatInput
