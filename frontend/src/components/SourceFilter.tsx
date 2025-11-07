import React from 'react'
import type { Lang } from '../i18n/translations'

interface Props {
  lang: Lang
  selected: string[]
  onToggle: (key: string) => void
}

const SOURCES = [
  { key: 'synth', label: { fr: 'Synth', en: 'Synth' } },
  { key: 'cfpb', label: { fr: 'CFPB', en: 'CFPB' } },
  { key: 'enron', label: { fr: 'Enron', en: 'Enron' } }
]

export const SourceFilter: React.FC<Props> = ({ lang, selected, onToggle }) => {
  return (
    <div className="source-filters">
      {SOURCES.map(s => (
        <button
          key={s.key}
          className={selected.includes(s.key) ? 'tag active' : 'tag'}
          onClick={() => onToggle(s.key)}
        >{s.label[lang]}</button>
      ))}
    </div>
  )
}
