import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ChatPanel } from './components/ChatPanel'
import type { Lang } from './i18n/translations'

function RootApp() {
  const [lang, setLang] = useState<Lang>('fr')
  return <ChatPanel lang={lang} onLangChange={setLang} />
}

const root = createRoot(document.getElementById('root')!)
root.render(<RootApp />)
