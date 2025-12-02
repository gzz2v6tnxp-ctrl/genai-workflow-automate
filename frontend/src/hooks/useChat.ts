import { useState, useEffect } from 'react'
import axios from 'axios'
import type { Lang } from '../i18n/translations'

// Déterminer l'URL API selon l'environnement
// En production (GitHub Pages), utiliser l'URL Render si VITE_API_BASE n'est pas défini
const isProduction = window.location.hostname !== 'localhost'
const productionFallback = 'https://genai-workflow-backend.onrender.com'
const API_BASE =
  import.meta.env.VITE_API_BASE || (isProduction ? productionFallback : 'http://localhost:8000')

// Debug: log de l'URL API utilisée
console.log('API Configuration:', {
  hostname: window.location.hostname,
  isProduction,
  VITE_API_BASE: import.meta.env.VITE_API_BASE,
  finalAPIBase: API_BASE
})

export interface VerificationInfo {
  claim: string
  is_verified: boolean
  confidence: number
  evidence?: string | null
  correction?: string | null
}

export interface ChatMessage {
  id: string
  question: string
  answer: string
  language: string
  similarity_score: number  // Score de similarité brut
  confidence_score: number  // Score de confiance ajusté
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
  collection: string
  sourcesFilter?: string[] | null
  latencyMs?: number | null
  createdAt: number
  // COV-RAG specific fields
  cove_enabled?: boolean
  hallucination_detected?: boolean
  corrections_made?: number
  verifications?: VerificationInfo[]
  initial_answer?: string | null
}

interface SendOptions {
  collection: string
  sourcesFilter: string[] | null
}

export interface ChatMetrics {
  requestCount: number
  errorCount: number
  lastError: string | null
  lastErrorAt: number | null
  lastSuccessAt: number | null
  lastLatencyMs: number | null
  errorLog: string[]
}

export function useChat(lang: Lang) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [requestCount, setRequestCount] = useState(0)
  const [errorCount, setErrorCount] = useState(0)
  const [lastError, setLastError] = useState<string | null>(null)
  const [lastErrorAt, setLastErrorAt] = useState<number | null>(null)
  const [lastSuccessAt, setLastSuccessAt] = useState<number | null>(null)
  const [lastLatencyMs, setLastLatencyMs] = useState<number | null>(null)
  const [errorLog, setErrorLog] = useState<string[]>([])

  // Heartbeat léger pour garder le backend Render "chaud" en production
  useEffect(() => {
    if (!isProduction) return

    let cancelled = false

    const ping = async () => {
      try {
        await axios.get(`${API_BASE}/health`, { timeout: 3000 })
      } catch {
        // on ignore les erreurs ici: le statut détaillé est géré par useChat/send
      }
    }

    // premier ping immédiat au montage
    ping()
    const id = window.setInterval(() => {
      if (!cancelled) {
        void ping()
      }
    }, 30000)

    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  async function send(question: string, opts: SendOptions) {
    setLoading(true)
    setError(null)
    setRequestCount(c => c + 1)
    const start = performance.now()

    try {
      const payload: any = { question, collection: opts.collection }
      if (opts.sourcesFilter && opts.sourcesFilter.length) {
        payload.sources_filter = opts.sourcesFilter
      }
      const res = await axios.post(`${API_BASE}/api/v1/chatbot/query`, payload)
      const data = res.data
      const latency = performance.now() - start

      const msg: ChatMessage = {
        id: crypto.randomUUID(),
        question,
        answer: data.answer,
        language: data.language,
        similarity_score: data.similarity_score || 0,
        confidence_score: data.confidence_score || 0,
        sources: data.sources || [],
        quality_pass: data.quality_pass ?? null,
        escalate: data.escalate ?? null,
        cites_ok: data.cites_ok ?? null,
        overlap_ratio: data.overlap_ratio ?? null,
        hallucination: data.hallucination ?? null,
        collection: opts.collection,
        sourcesFilter: opts.sourcesFilter,
        latencyMs: latency,
        createdAt: Date.now(),
        // COV-RAG fields
        cove_enabled: data.cove_enabled ?? false,
        hallucination_detected: data.hallucination_detected ?? null,
        corrections_made: data.corrections_made ?? 0,
        verifications: data.verifications ?? null,
        initial_answer: data.initial_answer ?? null
      }
      setMessages(m => [msg, ...m])
      setLastLatencyMs(latency)
      setLastSuccessAt(Date.now())
    } catch (e: any) {
      const message = e?.response?.data?.detail || e.message || 'Unknown error'
      setError(message)
      setErrorCount(c => c + 1)
      setLastError(message)
      setLastErrorAt(Date.now())
      setErrorLog(prev => {
        const next = [...prev, `${new Date().toLocaleTimeString()} - ${message}`]
        return next.slice(-5)
      })
    } finally {
      setLoading(false)
    }
  }

  const metrics: ChatMetrics = {
    requestCount,
    errorCount,
    lastError,
    lastErrorAt,
    lastSuccessAt,
    lastLatencyMs,
    errorLog
  }

  return { messages, send, loading, error, metrics }
}
