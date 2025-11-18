import { useState } from 'react'
import axios from 'axios'
import type { Lang } from '../i18n/translations'

// Déterminer l'URL API selon l'environnement
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

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
  // Evaluation metadata from the backend
  quality_pass?: boolean | null
  escalate?: boolean | null
  cites_ok?: boolean | null
  overlap_ratio?: number | null
  hallucination?: boolean | null
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
      const res = await axios.post(`${API_BASE}/api/v1/chatbot/query`, payload)
      const data = res.data
      const msg: ChatMessage = {
        id: crypto.randomUUID(),
        question,
        answer: data.answer,
        language: data.language,
        confidence: data.confidence,
        sources: data.sources || [],
        quality_pass: data.quality_pass ?? null,
        escalate: data.escalate ?? null,
        cites_ok: data.cites_ok ?? null,
        overlap_ratio: data.overlap_ratio ?? null,
        hallucination: data.hallucination ?? null,
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
