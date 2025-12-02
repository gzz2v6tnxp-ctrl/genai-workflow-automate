import React from 'react'
import { Target, Shield, Info } from 'lucide-react'

interface ScoreDisplayProps {
  similarityScore: number
  confidenceScore: number
}

export const ScoreDisplay: React.FC<ScoreDisplayProps> = ({
  similarityScore,
  confidenceScore
}) => {
  const getScoreColor = (score: number): string => {
    if (score >= 0.6) return 'text-green-400 bg-green-500/10 border-green-500/20'
    if (score >= 0.45) return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20'
    return 'text-red-400 bg-red-500/10 border-red-500/20'
  }

  const simPercent = (similarityScore * 100).toFixed(1)
  const confPercent = (confidenceScore * 100).toFixed(1)

  return (
    <div className="flex flex-wrap items-center gap-4 text-xs">
      {/* Score de similarité */}
      <div className="flex items-center gap-2">
        <Target className="w-4 h-4 text-gray-500" />
        <span className="text-gray-400 font-medium">Similarité :</span>
        <span
          className={`px-2.5 py-1 rounded-lg font-semibold border ${getScoreColor(similarityScore)}`}
        >
          {simPercent}%
        </span>
      </div>

      {/* Séparateur */}
      <span className="text-gray-600 hidden sm:inline">•</span>

      {/* Score de confiance avec tooltip */}
      <div className="flex items-center gap-2 group relative">
        <Shield className="w-4 h-4 text-gray-500" />
        <span className="text-gray-400 font-medium">Confiance :</span>
        <span
          className={`px-2.5 py-1 rounded-lg font-semibold border ${getScoreColor(confidenceScore)}`}
        >
          {confPercent}%
        </span>

        {/* Info icon avec tooltip */}
        <div className="relative">
          <Info className="w-4 h-4 text-gray-500 cursor-help" />
          <div className="invisible group-hover:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 border border-white/10 text-white text-xs rounded-lg shadow-xl z-10 pointer-events-none">
            <p className="font-semibold mb-1.5 text-purple-300">Score ajusté (×0.8)</p>
            <p className="text-gray-300 leading-relaxed">
              Pénalité appliquée pour tenir compte des risques d'hallucination du modèle.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
