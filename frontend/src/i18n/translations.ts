export type Lang = 'en' | 'fr'

const fr = {
  appTitle: 'Assistant Bancaire RAG',
  subtitle: 'Démonstration MVP • Recherche augmentée + Génération',
  askPlaceholder: 'Posez votre question (ex: Ma carte est bloquée...)',
  send: 'Envoyer',
  sources: 'Sources',
  selectSources: 'Filtrer les sources',
  collection: 'Collection',
  demoPublic: 'Démo Publique',
  knowledgeBase: 'Base Principale',
  response: 'Réponse',
  confidence: 'Confiance',
  noMessages: 'Aucun message pour le moment.',
  language: 'Langue',
  filtersApplied: 'Filtre appliqué',
  loading: 'Chargement...',
  error: 'Erreur lors de la requête',
  footer: '© 2025 GenAI Workflow Automation'
}

const en = {
  appTitle: 'Banking RAG Assistant',
  subtitle: 'MVP Demo • Retrieval Augmented Generation',
  askPlaceholder: 'Ask your question (e.g. unauthorized charge...)',
  send: 'Send',
  sources: 'Sources',
  selectSources: 'Filter sources',
  collection: 'Collection',
  demoPublic: 'Public Demo',
  knowledgeBase: 'Main Knowledge Base',
  response: 'Response',
  confidence: 'Confidence',
  noMessages: 'No messages yet.',
  language: 'Language',
  filtersApplied: 'Filter applied',
  loading: 'Loading...',
  error: 'Error during request',
  footer: '© 2025 GenAI Workflow Automation'
}

export const t = (lang: Lang, key: keyof typeof en) => (lang === 'fr' ? (fr as any)[key] : (en as any)[key])
