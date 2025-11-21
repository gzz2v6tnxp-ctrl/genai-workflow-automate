import React from 'react'

interface ScoreDisplayProps {
  similarityScore: number
  confidenceScore: number
}

export const ScoreDisplay: React.FC<ScoreDisplayProps> = ({
  similarityScore,
  confidenceScore
}) => {
  const getScoreColor = (score: number): string => {
    if (score >= 0.6) return 'text-green-600 bg-green-50'
    if (score >= 0.45) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const simPercent = (similarityScore * 100).toFixed(1)
  const confPercent = (confidenceScore * 100).toFixed(1)

  return (
    <div className="flex items-center gap-3 text-xs mt-2">
      {/* Score de similarité */}
      <div className="flex items-center gap-1.5">
        <span className="text-gray-500 font-medium">Similarité:</span>
        <span
          className={`px-2 py-0.5 rounded-full font-semibold ${getScoreColor(
            similarityScore
          )}`}
        >
          {simPercent}%
        </span>
      </div>

      {/* Séparateur */}
      <span className="text-gray-300">•</span>

      {/* Score de confiance avec tooltip */}
      <div className="flex items-center gap-1.5 group relative">
        <span className="text-gray-500 font-medium">Confiance:</span>
        <span
          className={`px-2 py-0.5 rounded-full font-semibold ${getScoreColor(
            confidenceScore
          )}`}
        >
          {confPercent}%
        </span>

        {/* Info icon avec tooltip */}
        <svg 
          className="w-3.5 h-3.5 text-gray-400 cursor-help" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <circle cx="12" cy="12" r="10" strokeWidth="2" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 16v-4m0-4h.01" />
        </svg>
        <div className="invisible group-hover:visible absolute bottom-full left-0 mb-2 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg z-10 pointer-events-none">
          <p className="font-semibold mb-1">Score ajusté (×0.8)</p>
          <p className="text-gray-300">
            Pénalité appliquée pour tenir compte des risques d'hallucination du
            modèle.
          </p>
        </div>
      </div>
    </div>
  )
}
