import React from 'react'
import type { Lang } from '../i18n/translations'
import { t } from '../i18n/translations'
import type { ChatMessage, ChatMetrics } from '../hooks/useChat'

interface Props {
  lang: Lang
  messages: ChatMessage[]
  metrics: ChatMetrics
}

type StatusLevel = 'ok' | 'warning' | 'error'

function computeStatusLevel(metrics: ChatMetrics, messages: ChatMessage[]): StatusLevel {
  const recent = messages.slice(0, 10)
  const total = recent.length
  const hallucinationCount = recent.filter(m => m.hallucination === true).length
  const qualityFailCount = recent.filter(m => m.quality_pass === false).length

  const hallucinationRate = total ? hallucinationCount / total : 0
  const qualityFailRate = total ? qualityFailCount / total : 0

  if (
    metrics.errorCount > 0 &&
    metrics.lastErrorAt &&
    (!metrics.lastSuccessAt || metrics.lastErrorAt > metrics.lastSuccessAt)
  ) {
    return 'error'
  }

  if (hallucinationRate > 0.25 || qualityFailRate > 0.25) {
    return 'warning'
  }

  return 'ok'
}

export const SystemStatus: React.FC<Props> = ({ lang, messages, metrics }) => {
  const level = computeStatusLevel(metrics, messages)

  const recent = messages.slice(0, 10)
  const total = recent.length
  const hallucinationCount = recent.filter(m => m.hallucination === true).length
  const qualityFailCount = recent.filter(m => m.quality_pass === false).length
  const hallucinationRate = total ? Math.round((hallucinationCount / total) * 100) : 0
  const qualityFailRate = total ? Math.round((qualityFailCount / total) * 100) : 0

  const statusLabel =
    level === 'ok'
      ? t(lang, 'statusHealthy')
      : level === 'warning'
      ? t(lang, 'statusWarning')
      : t(lang, 'statusError')

  const statusClass =
    level === 'ok'
      ? 'status-indicator status-indicator--ok'
      : level === 'warning'
      ? 'status-indicator status-indicator--warning'
      : 'status-indicator status-indicator--error'

  const avgDocsPerAnswer = messages.length
    ? messages.reduce((sum, m) => sum + (m.sources?.length || 0), 0) / messages.length
    : 0

  return (
    <div className="status-root">
      <div className="status-header">
        <h3 className="status-title">{t(lang, 'systemStatusTitle')}</h3>
        <div className={statusClass}>
          <span className="status-dot" />
          <span className="status-label">{statusLabel}</span>
        </div>
      </div>

      <div className="status-body">
        <div className="status-row">
          <span className="status-key">{t(lang, 'statusErrors')}</span>
          <span className="status-value">{metrics.errorCount}</span>
        </div>
        <div className="status-row">
          <span className="status-key">{t(lang, 'statusQualityIssues')}</span>
          <span className="status-value">
            {qualityFailCount} {qualityFailRate}%
          </span>
        </div>
        <div className="status-row">
          <span className="status-key">{t(lang, 'statusHallucinations')}</span>
          <span className="status-value">
            {hallucinationCount} {hallucinationRate}%
          </span>
        </div>
        <div className="status-row">
          <span className="status-key">{t(lang, 'statusDocsPerAnswer')}</span>
          <span className="status-value">{avgDocsPerAnswer.toFixed(1)}</span>
        </div>
        <div className="status-row">
          <span className="status-key">{t(lang, 'statusLastSuccess')}</span>
          <span className="status-value">
            {metrics.lastSuccessAt ? new Date(metrics.lastSuccessAt).toLocaleTimeString() : '-'}
          </span>
        </div>
        <div className="status-row">
          <span className="status-key">{t(lang, 'statusLastError')}</span>
          <span className="status-value">
            {metrics.lastErrorAt ? new Date(metrics.lastErrorAt).toLocaleTimeString() : '-'}
          </span>
        </div>
      </div>

      {metrics.errorLog.length > 0 ? (
        <div className="status-log">
          <div className="status-log-title">{t(lang, 'statusRecentErrors')}</div>
          <ul>
            {metrics.errorLog.map((entry, index) => (
              <li key={index}>{entry}</li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="status-no-data">{t(lang, 'statusNoData')}</div>
      )}
    </div>
  )
}

export default SystemStatus
