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

  const avgDocsPerAnswer =
    messages.length > 0
      ? messages.reduce((sum, m) => sum + (m.sources?.length || 0), 0) / messages.length
      : 0

  const statusColor =
    level === 'ok'
      ? 'bg-green-500/20 text-green-300 border-green-500/30'
      : level === 'warning'
      ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
      : 'bg-red-500/20 text-red-300 border-red-500/30'

  const statusDotColor =
    level === 'ok'
      ? 'bg-green-400'
      : level === 'warning'
      ? 'bg-yellow-400'
      : 'bg-red-400'

  return (
    <div className="space-y-4">
      {/* Header avec statut */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300">{t(lang, 'systemStatusTitle')}</h3>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${statusColor}`}>
          <span className={`w-2 h-2 rounded-full ${statusDotColor} animate-pulse`} />
          <span className="text-xs font-medium">{statusLabel}</span>
        </div>
      </div>

      {/* Métriques */}
      <div className="space-y-3">
        <div className="flex items-center justify-between py-2 border-b border-white/5">
          <span className="text-sm text-gray-400">{t(lang, 'statusErrors')}</span>
          <span className="text-sm font-semibold text-white">{metrics.errorCount}</span>
        </div>
        
        <div className="flex items-center justify-between py-2 border-b border-white/5">
          <span className="text-sm text-gray-400">{t(lang, 'statusQualityIssues')}</span>
          <span className="text-sm font-semibold text-white">
            {qualityFailCount} <span className="text-gray-500">({qualityFailRate}%)</span>
          </span>
        </div>
        
        <div className="flex items-center justify-between py-2 border-b border-white/5">
          <span className="text-sm text-gray-400">{t(lang, 'statusHallucinations')}</span>
          <span className="text-sm font-semibold text-white">
            {hallucinationCount} <span className="text-gray-500">({hallucinationRate}%)</span>
          </span>
        </div>
        
        <div className="flex items-center justify-between py-2 border-b border-white/5">
          <span className="text-sm text-gray-400">{t(lang, 'statusDocsPerAnswer')}</span>
          <span className="text-sm font-semibold text-white font-mono">{avgDocsPerAnswer.toFixed(1)}</span>
        </div>
        
        <div className="flex items-center justify-between py-2 border-b border-white/5">
          <span className="text-sm text-gray-400">{t(lang, 'statusLastSuccess')}</span>
          <span className="text-xs font-mono text-green-400">
            {metrics.lastSuccessAt ? new Date(metrics.lastSuccessAt).toLocaleTimeString() : '-'}
          </span>
        </div>
        
        <div className="flex items-center justify-between py-2">
          <span className="text-sm text-gray-400">{t(lang, 'statusLastError')}</span>
          <span className="text-xs font-mono text-red-400">
            {metrics.lastErrorAt ? new Date(metrics.lastErrorAt).toLocaleTimeString() : '-'}
          </span>
        </div>
      </div>

      {/* Log des erreurs */}
      {metrics.errorLog.length > 0 ? (
        <div className="mt-4 pt-4 border-t border-white/10">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            {t(lang, 'statusRecentErrors')}
          </div>
          <div className="space-y-2">
            {metrics.errorLog.map((entry, index) => (
              <div 
                key={index}
                className="p-2 bg-red-500/5 border border-red-500/20 rounded text-xs text-red-200 font-mono leading-relaxed"
              >
                {entry}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-4 pt-4 border-t border-white/10 text-center text-xs text-gray-500">
          {t(lang, 'statusNoData')}
        </div>
      )}
    </div>
  )
}

export default SystemStatus
