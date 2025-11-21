import React from 'react'
import type { Lang } from '../i18n/translations'
import { t } from '../i18n/translations'
import type { ChatMessage, ChatMetrics } from '../hooks/useChat'

interface Props {
  lang: Lang
  messages: ChatMessage[]
  metrics: ChatMetrics
}

export const MetricsDashboard: React.FC<Props> = ({ lang, messages, metrics }) => {
  const totalMessages = messages.length

  if (!metrics.requestCount && totalMessages === 0) {
    return (
      <div className="metrics-root">
        <h3 className="metrics-title">{t(lang, 'metricsTitle')}</h3>
        <p className="metrics-empty">{t(lang, 'metricsEmpty')}</p>
      </div>
    )
  }

  const avgConfidence = totalMessages
    ? messages.reduce((sum, m) => sum + (m.confidence_score || 0), 0) / totalMessages
    : 0

  const messagesWithLatency = messages.filter(m => typeof m.latencyMs === 'number')
  const avgLatencyMs =
    messagesWithLatency.length > 0
      ? messagesWithLatency.reduce((sum, m) => sum + (m.latencyMs || 0), 0) /
        messagesWithLatency.length
      : null

  const hallucinationCount = messages.filter(m => m.hallucination === true).length
  const qualityFailCount = messages.filter(m => m.quality_pass === false).length
  const hallucinationRate = totalMessages ? (hallucinationCount / totalMessages) * 100 : 0

  const totalDocs = messages.reduce((sum, m) => sum + (m.sources?.length || 0), 0)
  const avgDocsPerAnswer = totalMessages ? totalDocs / totalMessages : 0

  const collectionCounts: Record<string, number> = {}
  messages.forEach(m => {
    if (!m.collection) return
    collectionCounts[m.collection] = (collectionCounts[m.collection] || 0) + 1
  })
  const topCollections = Object.entries(collectionCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)

  const sourceCounts: Record<string, number> = {}
  messages.forEach(m => {
    m.sources?.forEach(s => {
      if (!s.source) return
      sourceCounts[s.source] = (sourceCounts[s.source] || 0) + 1
    })
  })
  const topSources = Object.entries(sourceCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)

  return (
    <div className="metrics-root">
      <h3 className="metrics-title">{t(lang, 'metricsTitle')}</h3>
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">{t(lang, 'metricTotalRequests')}</div>
          <div className="metric-value">{metrics.requestCount}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">{t(lang, 'metricAvgConfidence')}</div>
          <div className="metric-value">
            {totalMessages ? `${(avgConfidence * 100).toFixed(1)}%` : '-'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">{t(lang, 'metricAvgLatency')}</div>
          <div className="metric-value">
            {avgLatencyMs != null ? `${avgLatencyMs.toFixed(0)} ms` : '-'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">{t(lang, 'metricHallucinationRate')}</div>
          <div className="metric-value">
            {totalMessages ? `${hallucinationRate.toFixed(0)}%` : '-'}
          </div>
        </div>
      </div>
      <div className="metrics-secondary">
        <div className="metric-chip-group">
          <div className="metric-chip-label">{t(lang, 'metricCollections')}</div>
          <div className="metric-chip-row">
            {topCollections.length === 0 ? (
              <span className="metric-chip metric-chip-empty">-</span>
            ) : (
              topCollections.map(([name, count]) => (
                <span key={name} className="metric-chip">
                  {name} {count}
                </span>
              ))
            )}
          </div>
        </div>
        <div className="metric-chip-group">
          <div className="metric-chip-label">{t(lang, 'metricSources')}</div>
          <div className="metric-chip-row">
            {topSources.length === 0 ? (
              <span className="metric-chip metric-chip-empty">-</span>
            ) : (
              topSources.map(([name, count]) => (
                <span key={name} className="metric-chip">
                  {name} {count}
                </span>
              ))
            )}
          </div>
        </div>
      </div>
      <div className="metric-footnote">
        {t(lang, 'metricsFootnote')} {t(lang, 'statusDocsPerAnswer')} {avgDocsPerAnswer.toFixed(1)}
      </div>
    </div>
  )
}

export default MetricsDashboard
