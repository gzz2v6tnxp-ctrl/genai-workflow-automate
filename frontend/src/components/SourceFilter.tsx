import React from 'react'
import type { Lang } from '../i18n/translations'
import { Database } from 'lucide-react'

interface Props {
  lang: Lang
  selected: string[]
  onToggle: (key: string) => void
}

const SOURCES = [
  { key: 'synth', label: { fr: 'Synth', en: 'Synth' }, color: 'purple' },
  { key: 'cfpb', label: { fr: 'CFPB', en: 'CFPB' }, color: 'blue' },
  { key: 'enron', label: { fr: 'Enron', en: 'Enron' }, color: 'green' }
]

export const SourceFilter: React.FC<Props> = ({ lang, selected, onToggle }) => {
  return (
    <div className="flex items-center gap-2">
      <Database className="w-4 h-4 text-gray-500" />
      <div className="flex items-center gap-1.5">
        {SOURCES.map(s => {
          const isActive = selected.includes(s.key)
          return (
            <button
              key={s.key}
              className={`
                px-3 py-1.5 text-xs font-medium rounded-lg border transition-all duration-200
                ${isActive 
                  ? 'bg-purple-500/20 border-purple-500/40 text-purple-300' 
                  : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10 hover:text-gray-300'
                }
              `}
              onClick={() => onToggle(s.key)}
            >
              {s.label[lang]}
            </button>
          )
        })}
      </div>
    </div>
  )
}
