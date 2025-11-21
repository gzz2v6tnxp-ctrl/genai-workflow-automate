import React, { useState } from 'react'
import { t, type Lang } from '../i18n/translations'
import { useChat } from '../hooks/useChat'
import { LanguageSwitcher } from './LanguageSwitcher'
import { SourceFilter } from './SourceFilter'
import { SampleQueries } from './SampleQueries'
import { MetricsDashboard } from './MetricsDashboard'
import { SystemStatus } from './SystemStatus'

interface Props {
  lang: Lang
  onLangChange: (l: Lang) => void
}

export const ChatPanel: React.FC<Props> = ({ lang, onLangChange }) => {
  const { messages, send, loading, error, metrics } = useChat(lang)
  const [question, setQuestion] = useState('')
  const [collection, setCollection] =
    useState<'demo_public' | 'knowledge_base_main'>('demo_public')
  const [sourcesFilter, setSourcesFilter] = useState<string[]>([])
  const [showSamples, setShowSamples] = useState(false)

  function toggleSource(key: string) {
    setSourcesFilter(curr =>
      curr.includes(key) ? curr.filter(k => k !== key) : [...curr, key]
    )
  }

  async function handleSend() {
    if (!question.trim()) return
    await send(question.trim(), {
      collection,
      sourcesFilter: sourcesFilter.length ? sourcesFilter : null
    })
    setQuestion('')
  }

  async function handleSampleRun(
    q: string,
    opts?: { collection?: string; sourcesFilter?: string[] | null }
  ) {
    if (opts?.collection) {
      setCollection(opts.collection as any)
    }
    if (opts?.sourcesFilter) {
      setSourcesFilter(opts.sourcesFilter || [])
    }
    await send(q, {
      collection: (opts?.collection as any) || collection,
      sourcesFilter: opts?.sourcesFilter || (sourcesFilter.length ? sourcesFilter : null)
    })
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <div className="logo">G</div>
          <div>
            <h1 className="title">{t(lang, 'appTitle')}</h1>
            <p className="sub">{t(lang, 'subtitle')}</p>
          </div>
        </div>
        <LanguageSwitcher lang={lang} onChange={onLangChange} />
      </header>

      <main className="app-grid">
        <section className="chat-column">
          <div className="card">
            <div className="hero-text">
              <h2 className="hero-title">{t(lang, 'heroTitle')}</h2>
              <p className="hero-subtitle">{t(lang, 'heroSubtitle')}</p>
            </div>

            <div className="input-row">
              <input
                className="input"
                placeholder={t(lang, 'askPlaceholder')}
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') handleSend()
                }}
              />
              <button
                className={`button ${loading ? 'button-loading' : ''}`}
                onClick={handleSend}
                disabled={loading}
                type="button"
              >
                {loading ? t(lang, 'loading') : t(lang, 'send')}
              </button>
            </div>

            <div className="controls-row">
              <select
                value={collection}
                onChange={e => setCollection(e.target.value as any)}
                className="input"
              >
                <option value="demo_public">{t(lang, 'demoPublic')}</option>
                <option value="knowledge_base_main">{t(lang, 'knowledgeBase')}</option>
              </select>
              {collection === 'knowledge_base_main' && (
                <SourceFilter lang={lang} selected={sourcesFilter} onToggle={toggleSource} />
              )}
            </div>

            <div className="samples-row">
              <button
                className="button secondary"
                type="button"
                onClick={() => setShowSamples(s => !s)}
              >
                {showSamples ? t(lang, 'hideSamples') : t(lang, 'showSamples')}
              </button>
            </div>

            {showSamples && (
              <div className="samples-panel">
                <SampleQueries lang={lang} onRun={handleSampleRun} />
              </div>
            )}

            {error && (
              <div className="badge badge-error">
                {t(lang, 'error')} : {error}
              </div>
            )}

            <div className="messages">
              {messages.length === 0 && (
                <div className="meta">{t(lang, 'noMessages')}</div>
              )}
              {messages.map(m => (
                <div key={m.id} className="bubble">
                  <div className="meta" style={{ marginBottom: 6 }}>
                    {new Date(m.createdAt).toLocaleTimeString()} • {t(lang, 'confidence')}: 
                    {(m.confidence * 100).toFixed(1)}%
                    {typeof m.latencyMs === 'number' ? ` • ${m.latencyMs.toFixed(0)} ms` : ''}
                  </div>
                  <strong>{m.question}</strong>
                  <div className="answer">{m.answer}</div>
                  {m.quality_pass === false && (
                    <div className="quality-warning">
                      This answer could not be fully verified automatically. Please review the
                      cited sources or contact support.
                    </div>
                  )}
                  {m.escalate === true && (
                    <div className="escalate-note">
                      This question has been flagged for human review. Our team will follow up.
                    </div>
                  )}
                  {m.sources?.length > 0 && (
                    <div style={{ marginTop: 10, display: 'grid', gap: 4 }}>
                      <div className="meta">{t(lang, 'sources')}:</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {m.sources.slice(0, 5).map(s => (
                          <span key={s.id} className="badge" title={s.type}>
                            {s.source} • {s.score.toFixed(3)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="footer">{t(lang, 'footer')}</div>
          </div>
        </section>

        <aside className="insights-column">
          <div className="card">
            <MetricsDashboard lang={lang} messages={messages} metrics={metrics} />
          </div>
          <div className="card">
            <SystemStatus lang={lang} messages={messages} metrics={metrics} />
          </div>
        </aside>
      </main>
    </div>
  )
}
