import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const storageKey = 'ai-chat-session'

const createSession = async () => {
  const response = await fetch(`${API_BASE_URL}/api/session`)
  if (!response.ok) {
    throw new Error('Unable to create session.')
  }
  return response.json()
}

const fetchHistory = async (sessionId) => {
  const response = await fetch(`${API_BASE_URL}/api/history/${sessionId}`)
  if (!response.ok) {
    throw new Error('Unable to load history.')
  }
  return response.json()
}

const resetSession = async (sessionId) => {
  await fetch(`${API_BASE_URL}/api/reset/${sessionId}`, { method: 'POST' })
}

const parseSseChunk = (chunk) => {
  const lines = chunk.split('\n')
  const dataLines = lines.filter((line) => line.startsWith('data: '))
  return dataLines.map((line) => line.replace('data: ', '').trim())
}

export const useChat = () => {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState('')
  const [usage, setUsage] = useState(null)
  const assistantBufferRef = useRef('')
  const abortControllerRef = useRef(null)

  const initialize = useCallback(async () => {
    setError('')
    const saved = localStorage.getItem(storageKey)
    try {
      if (saved) {
        const { sessionId: storedId } = JSON.parse(saved)
        setSessionId(storedId)
        const history = await fetchHistory(storedId)
        setMessages(history.messages || [])
        return
      }
      const session = await createSession()
      setSessionId(session.session_id)
      localStorage.setItem(storageKey, JSON.stringify({ sessionId: session.session_id }))
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    initialize()
  }, [initialize])

  const sendMessage = useCallback(
    async ({ message, systemPrompt, temperature }) => {
      if (!sessionId || !message.trim()) {
        return
      }
      setError('')
      setUsage(null)
      setIsStreaming(true)
      assistantBufferRef.current = ''
      abortControllerRef.current?.abort()
      const abortController = new AbortController()
      abortControllerRef.current = abortController
      setMessages((prev) => [...prev, { role: 'user', content: message }])

      try {
        const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: abortController.signal,
          body: JSON.stringify({
            session_id: sessionId,
            message,
            system_prompt: systemPrompt || undefined,
            temperature: temperature ? Number(temperature) : undefined
          })
        })

        if (!response.ok || !response.body) {
          const errorText = await response.text()
          throw new Error(errorText || 'Unable to stream response.')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let buffer = ''
        let assistantIndex = null

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const parts = buffer.split('\n\n')
          buffer = parts.pop() || ''

          parts.forEach((part) => {
            parseSseChunk(part).forEach((jsonString) => {
              if (!jsonString) return
              let payload
              try {
                payload = JSON.parse(jsonString)
              } catch (parseError) {
                return
              }
              if (payload.type === 'chunk') {
                assistantBufferRef.current += payload.content
                setMessages((prev) => {
                  const next = [...prev]
                  if (assistantIndex === null) {
                    assistantIndex = next.length
                    next.push({ role: 'assistant', content: payload.content })
                  } else {
                    next[assistantIndex] = {
                      role: 'assistant',
                      content: assistantBufferRef.current
                    }
                  }
                  return next
                })
              }
              if (payload.type === 'end') {
                setUsage(payload.usage)
              }
              if (payload.type === 'error') {
                setError(payload.message)
              }
            })
          })
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Unexpected error.')
        }
      } finally {
        setIsStreaming(false)
      }
    },
    [sessionId]
  )

  const resetConversation = useCallback(async () => {
    if (!sessionId) return
    setError('')
    setUsage(null)
    setMessages([])
    abortControllerRef.current?.abort()
    try {
      await resetSession(sessionId)
    } catch (err) {
      setError(err.message)
    }
  }, [sessionId])

  const statusText = useMemo(() => {
    if (isStreaming) return 'Assistant is typing...'
    if (usage) {
      return `Last response: ~${usage.approx_output_tokens} tokens`
    }
    return 'Ready'
  }, [isStreaming, usage])

  return {
    sessionId,
    messages,
    sendMessage,
    resetConversation,
    isStreaming,
    error,
    statusText
  }
}
