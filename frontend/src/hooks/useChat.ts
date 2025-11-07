import { useState } from 'react'
import axios from 'axios'
import type { Lang } from '../i18n/translations'

export interface ChatMessage {
  id: string
  question: string
  answer: string
  language: string
  confidence: number
  sources: Array<{
    id: string | number
    score: number
    source: string
    lang: string
    type: string
  }>
  createdAt: number
}

interface SendOptions {
  collection: string
  sourcesFilter: string[] | null
}

export function useChat(lang: Lang) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function send(question: string, opts: SendOptions) {
    setLoading(true)
    setError(null)
    try {
      const payload: any = { question, collection: opts.collection }
      if (opts.sourcesFilter && opts.sourcesFilter.length) {
        payload.sources_filter = opts.sourcesFilter
      }
      const res = await axios.post('/api/v1/chatbot/query', payload)
      const data = res.data
      const msg: ChatMessage = {
        id: crypto.randomUUID(),
        question,
        answer: data.answer,
        language: data.language,
        confidence: data.confidence,
        sources: data.sources || [],
        createdAt: Date.now()
      }
      setMessages(m => [msg, ...m])
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return { messages, send, loading, error }
}
