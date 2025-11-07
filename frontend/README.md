# Frontend Demo (React + Vite)

Interface de démonstration pour le pipeline RAG / LLM.

## ⚙️ Démarrage

```bash
npm install
npm run dev
```
Ouvrir: http://localhost:5173

## ✨ Fonctionnalités
- Chat RAG: envoie la question à l'endpoint `/api/v1/chatbot/query`
- Sélection collection: `demo_public` ou `knowledge_base_main`
- Filtre de sources (knowledge_base_main): synth / cfpb / enron (multi)
- Multilingue: FR / EN (UI + placeholders)
- Thème: blanc + bleu + touche de jaune
- Cache côté backend (Redis si dispo)

## 🧪 Test Rapide
1. Lancer backend: `uvicorn main:app --reload`
2. Ouvrir frontend et poser: `Ma carte bancaire est bloquée`
3. Basculer en EN et poser: `unauthorized charge on my credit card`
4. Sélectionner collection principale + filtre `cfpb` et tester: `dispute credit card fee`

## 🛠️ Configuration Proxy
Le proxy Vite route `/api` vers `http://localhost:8000`.
Modifier `vite.config.ts` si backend sur autre port.

## 📁 Structure
```
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  index.html
  src/
    theme.css
    main.tsx
    i18n/translations.ts
    hooks/useChat.ts
    components/
      ChatPanel.tsx
      LanguageSwitcher.tsx
      SourceFilter.tsx
```

## 🔄 Évolutions Possibles
- Mode sombre automatique
- Format JSON output_format="json"
- Affichage des documents sources expand/collapse
- Indicateurs de latence et hit cache

## 🧩 Dépendances Principales
- React 18
- Vite 5
- Axios

## ✅ Qualité & Style
Palette:
- Bleu primaire: #0b6efd
- Jaune accent: #f6c90e
- Fond: #ffffff
- Texte: #0b0d12

## Licence
Sous licence MIT comme projet principal.
