import React, { useState } from 'react'
import { t, type Lang } from '../i18n/translations'
import { useChat } from '../hooks/useChat'
import { LanguageSwitcher } from './LanguageSwitcher'
import { SourceFilter } from './SourceFilter'
import { SampleQueries } from './SampleQueries'
import { MetricsDashboard } from './MetricsDashboard'
import { SystemStatus } from './SystemStatus'
import { ScoreDisplay } from './ScoreDisplay'
import { Layout } from './Layout'
import { ArrowLeft, Send, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

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
  const navigate = useNavigate()

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
    <Layout>
      <div className="flex flex-col h-screen max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <header className="flex items-center justify-between mb-6 bg-white/5 backdrop-blur-md p-4 rounded-2xl border border-white/10">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center font-bold text-white shadow-lg shadow-purple-500/20">
                G
              </div>
              <div>
                <h1 className="font-bold text-lg leading-tight">{t(lang, 'appTitle')}</h1>
                <p className="text-xs text-gray-400">{t(lang, 'subtitle')}</p>
              </div>
            </div>
          </div>
          <LanguageSwitcher lang={lang} onChange={onLangChange} />
        </header>

        <main className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
          {/* Chat Column */}
          <section className="lg:col-span-2 flex flex-col gap-4 min-h-0">
            <div className="flex-1 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 flex flex-col overflow-hidden relative">

              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto space-y-6 pr-2 mb-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {messages.length === 0 && (
                  <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 p-8">
                    <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-4">
                      <Sparkles className="w-8 h-8 text-purple-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">{t(lang, 'heroTitle')}</h2>
                    <p className="max-w-md">{t(lang, 'heroSubtitle')}</p>
                  </div>
                )}

                {messages.map(m => (
                  <div key={m.id} className="group">
                    <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
                      <span>{new Date(m.createdAt).toLocaleTimeString()}</span>
                      {typeof m.latencyMs === 'number' && <span>• {m.latencyMs.toFixed(0)} ms</span>}
                    </div>

                    <div className="bg-white/5 rounded-2xl rounded-tl-none p-5 border border-white/10 mb-2">
                      <strong className="block text-purple-300 mb-2 text-sm uppercase tracking-wide">User</strong>
                      <div className="text-white/90 leading-7">{m.question}</div>
                    </div>

                    <div className="pl-8">
                      <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-2xl rounded-tr-none p-5 border border-white/10">
                        <strong className="block text-blue-300 mb-2 text-sm uppercase tracking-wide">Assistant</strong>
                        <div className="text-gray-200 whitespace-pre-wrap leading-8">{m.answer}</div>

                        {/* Scores */}
                        {(m.similarity_score !== undefined || m.confidence_score !== undefined) && (
                          <div className="mt-6 pt-4 border-t border-white/5">
                            <ScoreDisplay
                              similarityScore={m.similarity_score}
                              confidenceScore={m.confidence_score}
                            />
                          </div>
                        )}

                        {/* Warnings */}
                        {m.quality_pass === false && (
                          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-200 leading-relaxed">
                            This answer could not be fully verified automatically. Please review the cited sources.
                          </div>
                        )}

                        {/* Sources */}
                        {m.sources?.length > 0 && (
                          <div className="mt-6">
                            <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">{t(lang, 'sources')}</div>
                            <div className="flex flex-wrap gap-2">
                              {m.sources.slice(0, 5).map(s => (
                                <span key={s.id} className="px-3 py-1.5 text-xs rounded-md bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 transition-colors cursor-help flex items-center gap-2" title={s.type}>
                                  {s.source} <span className="w-1 h-1 rounded-full bg-gray-600"></span> <span className="text-green-400 font-mono">{s.score.toFixed(3)}</span>
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Input Area */}
              <div className="mt-auto space-y-4">
                {/* Controls */}
                <div className="flex flex-wrap gap-4 items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                  <div className="flex items-center gap-3">
                    <select
                      value={collection}
                      onChange={e => setCollection(e.target.value as any)}
                      className="bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-purple-500 transition-colors"
                    >
                      <option value="demo_public">{t(lang, 'demoPublic')}</option>
                      <option value="knowledge_base_main">{t(lang, 'knowledgeBase')}</option>
                    </select>
                    {collection === 'knowledge_base_main' && (
                      <SourceFilter lang={lang} selected={sourcesFilter} onToggle={toggleSource} />
                    )}
                  </div>
                  <button
                    className="text-xs text-purple-400 hover:text-purple-300 transition-colors font-medium px-2 py-1 hover:bg-white/5 rounded"
                    type="button"
                    onClick={() => setShowSamples(s => !s)}
                  >
                    {showSamples ? t(lang, 'hideSamples') : t(lang, 'showSamples')}
                  </button>
                </div>

                {showSamples && (
                  <div className="p-4 bg-white/5 rounded-xl border border-white/10 animate-fade-in">
                    <SampleQueries lang={lang} onRun={handleSampleRun} />
                  </div>
                )}

                <div className="relative">
                  <input
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-5 pr-14 py-4 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all shadow-lg shadow-black/20"
                    placeholder={t(lang, 'askPlaceholder')}
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') handleSend()
                    }}
                  />
                  <button
                    className={`absolute right-2 top-1/2 -translate-y-1/2 p-2.5 rounded-lg bg-purple-600 text-white hover:bg-purple-500 transition-all shadow-lg shadow-purple-600/20 disabled:opacity-50 disabled:cursor-not-allowed ${loading ? 'animate-pulse' : ''}`}
                    onClick={handleSend}
                    disabled={loading}
                    type="button"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>

                {error && (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-200">
                    {t(lang, 'error')} : {error}
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* Sidebar */}
          <aside className="space-y-6 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-white/10">
            <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6">
              <MetricsDashboard lang={lang} messages={messages} metrics={metrics} />
            </div>
            <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6">
              <SystemStatus lang={lang} messages={messages} metrics={metrics} />
            </div>
            <div className="text-center text-xs text-gray-600 mt-8">
              {t(lang, 'footer')}
            </div>
          </aside>
        </main>
      </div>
    </Layout>
  )
}
