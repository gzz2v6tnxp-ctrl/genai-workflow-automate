import React, { useState } from 'react'
import { t, Lang } from '../i18n/translations'
import { useChat } from '../hooks/useChat'
import { LanguageSwitcher } from './LanguageSwitcher'
import { SourceFilter } from './SourceFilter'

interface Props {
  lang: Lang
  onLangChange: (l: Lang) => void
}

export const ChatPanel: React.FC<Props> = ({ lang, onLangChange }) => {
  const { messages, send, loading, error } = useChat(lang)
  const [question, setQuestion] = useState('')
  const [collection, setCollection] = useState<'demo_public' | 'knowledge_base_main'>('demo_public')
  const [sourcesFilter, setSourcesFilter] = useState<string[]>([])

  function toggleSource(key: string) {
    setSourcesFilter(curr => curr.includes(key) ? curr.filter(k => k !== key) : [...curr, key])
  }

  async function handleSend() {
    if (!question.trim()) return
    await send(question.trim(), { collection, sourcesFilter: sourcesFilter.length ? sourcesFilter : null })
    setQuestion('')
  }

  return (
    <div className="card" style={{ display: 'grid', gap: 20 }}>
      <div className="header">
        <div className="brand">
          <div className="logo">G</div>
          <div>
            <h1 className="title">{t(lang, 'appTitle')}</h1>
            <p className="sub">{t(lang, 'subtitle')}</p>
          </div>
        </div>
        <LanguageSwitcher lang={lang} onChange={onLangChange} />
      </div>

      <div className="input-row">
        <input
          className="input"
          placeholder={t(lang,'askPlaceholder')}
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
        />
        <button className="button" onClick={handleSend} disabled={loading}>{loading ? t(lang,'loading') : t(lang,'send')}</button>
      </div>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={collection}
          onChange={e => setCollection(e.target.value as any)}
          className="input"
          style={{ maxWidth: 240 }}
        >
          <option value="demo_public">{t(lang,'demoPublic')}</option>
          <option value="knowledge_base_main">{t(lang,'knowledgeBase')}</option>
        </select>
        {collection === 'knowledge_base_main' && (
          <SourceFilter lang={lang} selected={sourcesFilter} onToggle={toggleSource} />
        )}
      </div>

      {error && <div className="badge" style={{ borderColor: 'red', color: 'red' }}>{t(lang,'error')} : {error}</div>}

      <div className="messages">
        {messages.length === 0 && <div className="meta">{t(lang,'noMessages')}</div>}
        {messages.map(m => (
          <div key={m.id} className="bubble">
            <div className="meta" style={{ marginBottom: 6 }}>{new Date(m.createdAt).toLocaleTimeString()} • {t(lang,'confidence')}: {(m.confidence*100).toFixed(1)}%</div>
            <strong style={{ display: 'block', marginBottom: 6 }}>{m.question}</strong>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.4 }}>{m.answer}</div>
            {m.sources?.length > 0 && (
              <div style={{ marginTop: 10, display: 'grid', gap: 4 }}>
                <div className="meta">{t(lang,'sources')}:</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {m.sources.slice(0,5).map(s => (
                    <span key={s.id} className="badge" title={s.type}>{s.source} • {s.score.toFixed(3)}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="footer">{t(lang,'footer')}</div>
    </div>
  )
}
