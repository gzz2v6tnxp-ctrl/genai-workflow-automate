import React from 'react'
import type { Lang } from '../i18n/translations'
import { Play } from 'lucide-react'

interface Props {
  lang: Lang
  onRun: (question: string, opts?: { collection?: string; sourcesFilter?: string[] | null }) => Promise<void>
}

const SAMPLES: Array<{ q: string; labelFr: string; labelEn: string; collection?: string; sources?: string[] }> = [
  { 
    q: "What was Enron's exact revenue in 2000?", 
    labelFr: "Quel était le chiffre d'affaires exact d'Enron en 2000 ?",
    labelEn: "What was Enron's exact revenue in 2000?",
    collection: 'knowledge_base_main', 
    sources: ['enron'] 
  },
  { 
    q: 'How to dispute an unauthorized charge on my credit card?', 
    labelFr: 'Comment contester un débit non autorisé sur ma carte ?',
    labelEn: 'How to dispute an unauthorized charge on my credit card?',
    collection: 'knowledge_base_main', 
    sources: ['cfpb'] 
  },
  { 
    q: "Ma carte bancaire est bloquée, que dois-je faire ?", 
    labelFr: 'Ma carte bancaire est bloquée, que faire ?',
    labelEn: 'My bank card is blocked, what should I do?',
    collection: 'knowledge_base_main', 
    sources: ['synth'] 
  },
]

export const SampleQueries: React.FC<Props> = ({ lang, onRun }) => {
  return (
    <div className="space-y-3">
      <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
        {lang === 'fr' ? 'Exemples de requêtes' : 'Sample Queries'}
      </div>
      <div className="flex flex-col gap-2">
        {SAMPLES.map((s, idx) => (
          <button
            key={idx}
            className="group flex items-center gap-3 w-full text-left px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-purple-500/30 rounded-lg transition-all duration-200"
            onClick={() => onRun(s.q, { collection: s.collection, sourcesFilter: s.sources })}
            title={s.collection}
          >
            <div className="flex-shrink-0 w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center group-hover:bg-purple-500/30 transition-colors">
              <Play className="w-4 h-4 text-purple-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-200 truncate">
                {lang === 'fr' ? s.labelFr : s.labelEn}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {s.sources?.join(', ') || 'all sources'}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export default SampleQueries
