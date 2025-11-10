import React from 'react'
import type { Lang } from '../i18n/translations'

interface Props {
  lang: Lang
  onRun: (question: string, opts?: { collection?: string; sourcesFilter?: string[] | null }) => Promise<void>
}

const SAMPLES: Array<{ q: string; collection?: string; sources?: string[] }> = [
  { q: "What was Enron's exact revenue in 2000?", collection: 'knowledge_base_main', sources: ['enron'] },
  { q: 'How to dispute an unauthorized charge on my credit card?', collection: 'knowledge_base_main', sources: ['cfpb'] },
  { q: "Ma carte bancaire est bloquée, que dois-je faire ?", collection: 'knowledge_base_main', sources: ['synth'] },
]

export const SampleQueries: React.FC<Props> = ({ lang, onRun }) => {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
      {SAMPLES.map((s, idx) => (
        <button
          key={idx}
          className="tag"
          onClick={() => onRun(s.q, { collection: s.collection, sourcesFilter: s.sources })}
          title={s.collection}
        >{s.q}</button>
      ))}
    </div>
  )
}

export default SampleQueries
