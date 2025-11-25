import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ChatPanel } from './components/ChatPanel'
import { Dashboard } from './pages/Dashboard'
import type { Lang } from './i18n/translations'
import './globals.css'
import './theme.css'

function ChatRoute() {
  const [lang, setLang] = useState<Lang>('fr')
  return <ChatPanel lang={lang} onLangChange={setLang} />
}

function RootApp() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/project/genai-workflow" element={<ChatRoute />} />
        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

const root = createRoot(document.getElementById('root')!)
root.render(<RootApp />)
