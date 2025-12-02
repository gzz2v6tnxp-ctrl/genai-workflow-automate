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
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-gray-300">{t(lang, 'metricsTitle')}</h3>
        <p className="text-xs text-gray-500 text-center py-4">{t(lang, 'metricsEmpty')}</p>
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
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">{t(lang, 'metricsTitle')}</h3>
      
      {/* Métriques principales en grille */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-gradient-to-br from-purple-500/10 to-purple-500/5 rounded-lg border border-purple-500/20">
          <div className="text-xs text-gray-400 mb-1">{t(lang, 'metricTotalRequests')}</div>
          <div className="text-xl font-bold text-white">{metrics.requestCount}</div>
        </div>
        
        <div className="p-3 bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-lg border border-blue-500/20">
          <div className="text-xs text-gray-400 mb-1">{t(lang, 'metricAvgConfidence')}</div>
          <div className="text-xl font-bold text-white">
            {totalMessages ? `${(avgConfidence * 100).toFixed(1)}%` : '-'}
          </div>
        </div>
        
        <div className="p-3 bg-gradient-to-br from-green-500/10 to-green-500/5 rounded-lg border border-green-500/20">
          <div className="text-xs text-gray-400 mb-1">{t(lang, 'metricAvgLatency')}</div>
          <div className="text-xl font-bold text-white">
            {avgLatencyMs != null ? (
              <>
                {avgLatencyMs.toFixed(0)}
                <span className="text-sm text-gray-400 ml-1">ms</span>
              </>
            ) : '-'}
          </div>
        </div>
        
        <div className="p-3 bg-gradient-to-br from-orange-500/10 to-orange-500/5 rounded-lg border border-orange-500/20">
          <div className="text-xs text-gray-400 mb-1">{t(lang, 'metricHallucinationRate')}</div>
          <div className="text-xl font-bold text-white">
            {totalMessages ? `${hallucinationRate.toFixed(0)}%` : '-'}
          </div>
        </div>
      </div>
      
      {/* Métriques secondaires */}
      <div className="space-y-3 pt-3 border-t border-white/10">
        <div>
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
            {t(lang, 'metricCollections')}
          </div>
          <div className="flex flex-wrap gap-2">
            {topCollections.length === 0 ? (
              <span className="text-xs text-gray-500">-</span>
            ) : (
              topCollections.map(([name, count]) => (
                <span 
                  key={name} 
                  className="px-2.5 py-1 text-xs bg-white/5 border border-white/10 rounded-md text-gray-300 font-medium"
                >
                  {name} <span className="text-purple-400">({count})</span>
                </span>
              ))
            )}
          </div>
        </div>
        
        <div>
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
            {t(lang, 'metricSources')}
          </div>
          <div className="flex flex-wrap gap-2">
            {topSources.length === 0 ? (
              <span className="text-xs text-gray-500">-</span>
            ) : (
              topSources.map(([name, count]) => (
                <span 
                  key={name} 
                  className="px-2.5 py-1 text-xs bg-white/5 border border-white/10 rounded-md text-gray-300 font-medium"
                >
                  {name} <span className="text-blue-400">({count})</span>
                </span>
              ))
            )}
          </div>
        </div>
      </div>
      
      {/* Note de bas de page */}
      <div className="pt-3 mt-2 border-t border-white/5 text-xs text-gray-500">
        {t(lang, 'metricsFootnote')} • {t(lang, 'statusDocsPerAnswer')} : <span className="text-gray-400 font-mono">{avgDocsPerAnswer.toFixed(1)}</span>
      </div>
    </div>
  )
}

export default MetricsDashboard
