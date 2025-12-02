import React from 'react'
import { 
  Activity, 
  TrendingUp, 
  TrendingDown,
  Clock,
  Target,
  Shield,
  AlertCircle,
  CheckCircle2
} from 'lucide-react'
import type { Lang } from '../i18n/translations'
import type { ChatMessage } from '../hooks/useChat'

interface Props {
  messages: ChatMessage[]
  lang: Lang
}

export const AdvancedMetricsPanel: React.FC<Props> = ({ messages, lang }) => {
  if (messages.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p className="text-sm">
          {lang === 'fr' 
            ? 'Les métriques apparaîtront après la première requête'
            : 'Metrics will appear after the first request'}
        </p>
      </div>
    )
  }

  // Calculs des métriques avancées
  const totalMessages = messages.length

  // Confiance
  const avgConfidence = messages.reduce((sum, m) => sum + (m.confidence_score || 0), 0) / totalMessages
  const confidenceTrend = messages.length >= 2 
    ? (messages[0].confidence_score || 0) - (messages[1].confidence_score || 0)
    : 0

  // Latence
  const messagesWithLatency = messages.filter(m => typeof m.latencyMs === 'number')
  const avgLatency = messagesWithLatency.length > 0
    ? messagesWithLatency.reduce((sum, m) => sum + (m.latencyMs || 0), 0) / messagesWithLatency.length
    : 0

  // Qualité
  const qualityPassCount = messages.filter(m => m.quality_pass === true).length
  const qualityPassRate = (qualityPassCount / totalMessages) * 100
  const escalateCount = messages.filter(m => m.escalate === true).length

  // Hallucinations (COV-RAG)
  const hallucinationCount = messages.filter(m => m.hallucination === true).length
  const hallucinationRate = (hallucinationCount / totalMessages) * 100

  // Citations
  const citesOkCount = messages.filter(m => m.cites_ok === true).length
  const citationRate = (citesOkCount / totalMessages) * 100

  // Sources
  const totalSources = messages.reduce((sum, m) => sum + (m.sources?.length || 0), 0)
  const avgSourcesPerQuery = totalSources / totalMessages

  const avgSourceScore = messages.reduce((sum, m) => {
    const sources = m.sources || []
    const avgScore = sources.length > 0
      ? sources.reduce((s, src) => s + src.score, 0) / sources.length
      : 0
    return sum + avgScore
  }, 0) / totalMessages

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-400" />
          {lang === 'fr' ? 'Métriques Avancées' : 'Advanced Metrics'}
        </h3>
        <span className="text-xs text-gray-500">
          {totalMessages} {lang === 'fr' ? 'requêtes' : 'queries'}
        </span>
      </div>

      {/* Métriques Grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Confiance */}
        <div className="p-4 bg-gradient-to-br from-purple-500/10 to-purple-500/5 rounded-xl border border-purple-500/20">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-4 h-4 text-purple-400" />
            {confidenceTrend !== 0 && (
              confidenceTrend > 0 ? (
                <TrendingUp className="w-3 h-3 text-green-400" />
              ) : (
                <TrendingDown className="w-3 h-3 text-red-400" />
              )
            )}
          </div>
          <div className="text-2xl font-bold text-white mb-1">
            {(avgConfidence * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-400">
            {lang === 'fr' ? 'Confiance Moyenne' : 'Avg Confidence'}
          </div>
        </div>

        {/* Latence */}
        <div className="p-4 bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-xl border border-blue-500/20">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white mb-1">
            {avgLatency.toFixed(0)}
            <span className="text-sm text-gray-400 ml-1">ms</span>
          </div>
          <div className="text-xs text-gray-400">
            {lang === 'fr' ? 'Latence Moyenne' : 'Avg Latency'}
          </div>
        </div>

        {/* Taux de Qualité */}
        <div className="p-4 bg-gradient-to-br from-green-500/10 to-green-500/5 rounded-xl border border-green-500/20">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle2 className="w-4 h-4 text-green-400" />
          </div>
          <div className="text-2xl font-bold text-white mb-1">
            {qualityPassRate.toFixed(0)}%
          </div>
          <div className="text-xs text-gray-400">
            {lang === 'fr' ? 'Taux de Qualité' : 'Quality Rate'}
          </div>
          {escalateCount > 0 && (
            <div className="mt-2 text-xs text-orange-400 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {escalateCount} {lang === 'fr' ? 'escaladé(s)' : 'escalated'}
            </div>
          )}
        </div>

        {/* Hallucinations */}
        <div className={`p-4 rounded-xl border ${
          hallucinationRate === 0 
            ? 'bg-gradient-to-br from-green-500/10 to-green-500/5 border-green-500/20'
            : 'bg-gradient-to-br from-orange-500/10 to-orange-500/5 border-orange-500/20'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <Shield className={hallucinationRate === 0 ? 'w-4 h-4 text-green-400' : 'w-4 h-4 text-orange-400'} />
          </div>
          <div className="text-2xl font-bold text-white mb-1">
            {hallucinationRate.toFixed(0)}%
          </div>
          <div className="text-xs text-gray-400">
            {lang === 'fr' ? 'Taux Hallucination' : 'Hallucination Rate'}
          </div>
        </div>
      </div>

      {/* Métriques Secondaires */}
      <div className="space-y-2 pt-2 border-t border-white/5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">
            {lang === 'fr' ? 'Citations valides' : 'Valid citations'}
          </span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
                style={{ width: `${citationRate}%` }}
              />
            </div>
            <span className="text-gray-300 font-mono font-semibold w-10 text-right">
              {citationRate.toFixed(0)}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">
            {lang === 'fr' ? 'Sources/requête' : 'Sources/query'}
          </span>
          <span className="text-gray-300 font-mono font-semibold">
            {avgSourcesPerQuery.toFixed(1)}
          </span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">
            {lang === 'fr' ? 'Score sources moy.' : 'Avg source score'}
          </span>
          <span className="text-gray-300 font-mono font-semibold">
            {(avgSourceScore * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  )
}

export default AdvancedMetricsPanel
