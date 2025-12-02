import React from 'react'
import { Shield, CheckCircle, XCircle, AlertTriangle, Zap } from 'lucide-react'
import type { Lang } from '../i18n/translations'
import { t } from '../i18n/translations'

interface VerificationInfo {
  claim: string
  is_verified: boolean
  confidence: number
  evidence?: string | null
  correction?: string | null
}

interface Props {
  coveEnabled?: boolean
  hallucinationDetected?: boolean
  correctionsMode?: number
  verifications?: VerificationInfo[]
  initialAnswer?: string | null
  lang: Lang
}

export const COVEMetrics: React.FC<Props> = ({
  coveEnabled,
  hallucinationDetected,
  correctionsMode,
  verifications,
  initialAnswer,
  lang
}) => {
  if (!coveEnabled) {
    return null
  }

  const hasCorrections = correctionsMode && correctionsMode > 0
  const hasVerifications = verifications && verifications.length > 0

  return (
    <div className="mt-6 space-y-4">
      {/* CoVE Status Badge */}
      <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 rounded-xl">
        <div className="flex-shrink-0">
          <Shield className="w-6 h-6 text-purple-400" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-purple-300">
              Chain-of-Verification (CoVE)
            </span>
            <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-300 rounded-full border border-green-500/30">
              Active
            </span>
          </div>
          <p className="text-xs text-gray-400">
            {lang === 'fr' 
              ? 'Réponse vérifiée contre les sources pour éviter les hallucinations'
              : 'Answer verified against sources to prevent hallucinations'}
          </p>
        </div>
      </div>

      {/* Hallucination Detection */}
      {hallucinationDetected !== undefined && (
        <div className={`p-4 rounded-xl border flex items-start gap-3 ${
          hallucinationDetected
            ? 'bg-orange-500/10 border-orange-500/30'
            : 'bg-green-500/10 border-green-500/30'
        }`}>
          <div className="flex-shrink-0 mt-0.5">
            {hallucinationDetected ? (
              <AlertTriangle className="w-5 h-5 text-orange-400" />
            ) : (
              <CheckCircle className="w-5 h-5 text-green-400" />
            )}
          </div>
          <div className="flex-1">
            <div className="font-medium text-sm mb-1">
              {hallucinationDetected ? (
                <span className="text-orange-300">
                  {lang === 'fr' ? 'Hallucination détectée' : 'Hallucination Detected'}
                </span>
              ) : (
                <span className="text-green-300">
                  {lang === 'fr' ? 'Aucune hallucination détectée' : 'No Hallucination Detected'}
                </span>
              )}
            </div>
            {hallucinationDetected && hasCorrections && (
              <p className="text-xs text-gray-400">
                {lang === 'fr'
                  ? `${correctionsMode} correction(s) appliquée(s) automatiquement`
                  : `${correctionsMode} correction(s) applied automatically`}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Verifications Details */}
      {hasVerifications && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              {lang === 'fr' ? 'Vérifications' : 'Verifications'}
              <span className="text-xs text-gray-500">
                ({verifications!.filter(v => v.is_verified).length}/{verifications!.length})
              </span>
            </h4>
          </div>

          <div className="space-y-2">
            {verifications!.slice(0, 3).map((verification, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border text-xs ${
                  verification.is_verified
                    ? 'bg-green-500/5 border-green-500/20'
                    : 'bg-red-500/5 border-red-500/20'
                }`}
              >
                <div className="flex items-start gap-2 mb-2">
                  {verification.is_verified ? (
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className="text-gray-300 leading-relaxed">
                      "{verification.claim.slice(0, 100)}{verification.claim.length > 100 ? '...' : ''}"
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-xs text-gray-500 pl-6">
                  <span className="flex items-center gap-1">
                    {lang === 'fr' ? 'Confiance' : 'Confidence'}:
                    <span className={`font-mono font-semibold ${
                      verification.confidence >= 0.7 ? 'text-green-400' :
                      verification.confidence >= 0.5 ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {(verification.confidence * 100).toFixed(0)}%
                    </span>
                  </span>
                </div>

                {verification.correction && (
                  <div className="mt-2 pl-6 pt-2 border-t border-white/5">
                    <p className="text-xs text-gray-400">
                      <span className="text-orange-300 font-medium">
                        {lang === 'fr' ? 'Correction :' : 'Correction:'}
                      </span>{' '}
                      {verification.correction}
                    </p>
                  </div>
                )}

                {verification.evidence && !verification.correction && (
                  <div className="mt-2 pl-6 pt-2 border-t border-white/5">
                    <p className="text-xs text-gray-500 italic">
                      {verification.evidence.slice(0, 150)}
                      {verification.evidence.length > 150 ? '...' : ''}
                    </p>
                  </div>
                )}
              </div>
            ))}

            {verifications!.length > 3 && (
              <button className="w-full py-2 text-xs text-purple-400 hover:text-purple-300 transition-colors">
                {lang === 'fr' 
                  ? `Voir ${verifications!.length - 3} vérifications de plus`
                  : `Show ${verifications!.length - 3} more verifications`}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Initial Answer Comparison */}
      {initialAnswer && initialAnswer.trim() !== '' && hasCorrections && (
        <details className="group">
          <summary className="cursor-pointer p-3 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors text-sm text-gray-400 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-400" />
              {lang === 'fr' ? 'Voir la réponse avant correction' : 'View answer before correction'}
            </span>
            <span className="text-xs group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="mt-2 p-4 bg-orange-500/5 border border-orange-500/20 rounded-lg text-xs text-gray-400 leading-relaxed">
            {initialAnswer}
          </div>
        </details>
      )}
    </div>
  )
}

export default COVEMetrics
