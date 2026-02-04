import React, { useEffect, useRef } from 'react'
import ChatInput from './components/ChatInput.jsx'
import MessageList from './components/MessageList.jsx'
import TypingIndicator from './components/TypingIndicator.jsx'
import { useChat } from './hooks/useChat.js'

const App = () => {
  const { messages, sendMessage, resetConversation, isStreaming, error, statusText } = useChat()
  const chatBodyRef = useRef(null)

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight
    }
  }, [messages, isStreaming])

  return (
    <div className="app-shell">
      <header className="header">
        <div>
          <div className="header-title">AI Chatbot</div>
          <div className="status-bar">{statusText}</div>
        </div>
        <button className="secondary-button" type="button" onClick={resetConversation}>
          Reset
        </button>
      </header>
      <main className="content">
        <div className="chat-container">
          {error && <div className="error-banner">{error}</div>}
          <div className="chat-body" ref={chatBodyRef}>
            <MessageList messages={messages} />
            {isStreaming && <TypingIndicator />}
          </div>
          <ChatInput onSend={sendMessage} isStreaming={isStreaming} />
        </div>
      </main>
    </div>
  )
}

export default App
