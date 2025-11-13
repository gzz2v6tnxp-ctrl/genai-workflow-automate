# 🚀 GenAI Workflow Automate - RAVELOJAONA Irinasoa Sitraka L.

Une **pipeline RAG (Retrieval-Augmented Generation) robuste** avec qualité d'évaluation, escalade humaine et déploiement hybride (Frontend GitHub Pages + Backend Railway).

**Stack technique** :
- 🧠 **LLM** : OpenAI ChatGPT (3.5-turbo)
- 🔍 **Retrieval** : Qdrant Cloud (vecteur DB)
- 📊 **Orchestration** : LangGraph (agentic workflows)
- ⚡ **Backend** : FastAPI (Python)
- 🎨 **Frontend** : React + Vite + TypeScript
- 🐳 **Deployment** : Docker + Railway (backend) + GitHub Pages (frontend)

---

## 📋 Quick Links

1. [Installation locale](#installation-locale)
2. [Configuration](#configuration)
3. [Développement](#développement)
4. [Déploiement hybride](#déploiement-hybride)
5. [API Endpoints](#api-endpoints)
6. [Observabilité](#observabilité)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Prérequis

- **Python 3.11+** + `pip`
- **Node.js 20+** + `npm`
- **Docker & Docker Compose** (optional, pour local dev)
- **Comptes** : OpenAI API, Qdrant Cloud, GitHub, Railway.app

---

## 📥 Installation locale

### 1️⃣ Backend Setup

```bash
# Clone repo
git clone https://github.com/gzz2v6tnxp-ctrl/genai-workflow-automate.git
cd genai-workflow-automate

# Python env
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install deps
pip install -r requirements.txt
```

**Créer `.env`** (à la racine) :
```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.2
OPENAI_TOP_P=0.9
OPENAI_MAX_TOKENS=512

QDRANT_CLOUD_URL=https://xxxx-xxxx.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
COLLECTION_NAME=knowledge_base_main

REDIS_URL=redis://localhost:6379/0
REDIS_TTL=600
```

**Lancer backend** :
```bash
uvicorn main:app --reload
# ✅ http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### 2️⃣ Frontend Setup

```bash
cd frontend
npm install
npm run dev
# ✅ http://localhost:5173
```

### 3️⃣ Tester l'intégration

1. Ouvrir http://localhost:5173
2. Envoyer : "What was Enron's exact revenue in 2000?"
3. Sélectionner collection: `knowledge_base_main`, source: `enron`
4. Vérifier réponse + sources

---

## ⚙️ Configuration

### Variables d'environnement

| Var | Fichier | Exemple | Notes |
|-----|---------|---------|-------|
| `OPENAI_API_KEY` | `.env` | `sk-...` | **Requis** |
| `QDRANT_CLOUD_URL` | `.env` | `https://xxxx.cloud.qdrant.io` | **Requis** |
| `QDRANT_API_KEY` | `.env` | `api-key` | **Requis** |
| `COLLECTION_NAME` | `.env` | `knowledge_base_main` | Défaut: `demo_public` |
| `VITE_API_BASE` | `frontend/.env.production` | `https://backend.railway.app` | Prod only |

### Prompts externalisés

Tous les prompts dans `agents/prompts.md` (Markdown) :

```markdown
# System Prompt
<!-- SYSTEM_PROMPT -->
You are a helpful assistant...
<!-- /SYSTEM_PROMPT -->

# User Template
<!-- USER_PROMPT -->
Question: {question}
<!-- /USER_PROMPT -->
```

Loader auto : `agents.graph.load_prompts()`.

---

## 🛠️ Développement

### Structure

```
genai-workflow-automate/
├── agents/
│   ├── graph.py              # StateGraph principal
│   ├── state.py              # TypedDict + types
│   └── prompts.md            # Prompts Markdown
├── router/
│   ├── chatbot.py            # POST /api/v1/chatbot/query
│   ├── retriever.py
│   └── ingestion.py
├── frontend/
│   ├── src/
│   │   ├── components/       # ChatPanel, SourceFilter, etc.
│   │   ├── hooks/            # useChat (API)
│   │   └── i18n/             # i18n
│   └── vite.config.ts
├── logs/
│   ├── llm_responses.jsonl   # LLM output + citations
│   └── metrics.jsonl         # Quality metrics
├── main.py                   # FastAPI entry
├── Dockerfile                # Backend
├── docker-compose.yml        # Local compose
├── railway.toml              # Railway config
└── README.md
```

### Workflow LangGraph

```
Input: question, collection, sources_filter
  ↓
[retrieve] → Qdrant Cloud (apply filters)
  ↓
[grade_documents] → score top-k results
  ↓
[generate] → LLM generation + [citations]
  ↓
[evaluate_response] → quality gate
  ├─ quality_pass=true → END (return)
  ├─ escalate=true → [human_review] (escalade)
  └─ escalate=false → [fallback] (generic response)
```

### Nodes

- **retrieve** : Semantic search + filter by source
- **grade** : Score documents (relevant/not_relevant)
- **generate** : LLM + citation anchoring
- **evaluate** : Quality gate (confidence, hallucination, cites_ok)
- **human_review** : Escalation message
- **fallback** : Generic fallback response

---

## 🚀 Déploiement hybride

### Architecture

```
┌────────────────────────────────────────┐
│  GitHub Pages (GRATUIT)                │
│  Frontend React (dist/)                │
│  https://gzz2v6tnxp-ctrl.github.io/... │
└──────────────────┬─────────────────────┘
                   │ CORS API calls
                   ▼
┌────────────────────────────────────────┐
│  Railway.app ($5/mois)                 │
│  Backend FastAPI + Docker              │
│  https://backend-xxx.up.railway.app    │
└──────────────────┬─────────────────────┘
                   │ Vector DB API
                   ▼
┌────────────────────────────────────────┐
│  Qdrant Cloud (Gratuit tier 1GB)        │
│  Vecteur DB externe (prod)             │
└────────────────────────────────────────┘
```

### Coûts

| Service | Plan | Coût |
|---------|------|------|
| Frontend (GitHub Pages) | Free | **$0** ✅ |
| Backend (Railway) | Free + $5 credit | **$0-5** 🎉 |
| Qdrant (1GB tier) | Free | **$0** ✅ |
| OpenAI API | Pay-as-you-go | **$1-5** |
| **TOTAL** | | **$1-10/mois** |

### Déploiement étape-par-étape

#### 🔵 Frontend (GitHub Pages)

**1. Push code**
```bash
git add .
git commit -m "feat: hybrid deployment"
git push origin main
```

**2. GitHub Actions déclenche** → `cd-frontend-pages.yml`
- Build : `npm run build -- --base=/genai-workflow-automate/`
- Deploy : artifact → GitHub Pages

**3. Accès**
```
https://gzz2v6tnxp-ctrl.github.io/genai-workflow-automate/
```

#### 🔴 Backend (Railway)

**1. Créer compte Railway** : https://railway.app

**2. Connecter GitHub**
- Dashboard → New Project → Deploy from GitHub
- Sélectionner repo

**3. Railway détecte**
- `Dockerfile` (backend)
- `railway.toml` (config)

**4. Ajouter secrets** (Environment) :
```
OPENAI_API_KEY = sk-...
QDRANT_CLOUD_URL = https://xxxx.cloud.qdrant.io
QDRANT_API_KEY = api-key
```

**5. Déployer**
- Manuelle : Railway UI → Deploy
- Auto : push → GitHub Actions → Railway

**6. Récupérer URL**
```bash
railway env
# SERVICE_URL=https://backend-xxx.up.railway.app
```

**7. Update frontend**

`frontend/.env.production` :
```env
VITE_API_BASE=https://backend-xxx.up.railway.app
```

Push :
```bash
git add frontend/.env.production
git commit -m "chore: update API base URL"
git push origin main
```

**8. Tester**
- Frontend : https://gzz2v6tnxp-ctrl.github.io/genai-workflow-automate/
- DevTools → Network → vérifier POST vers Railway
- Envoyer question → réponse depuis backend

---

## 🌐 API Endpoints

### `POST /api/v1/chatbot/query`

**Request** :
```json
{
  "question": "What is Enron's revenue?",
  "collection": "knowledge_base_main",
  "sources_filter": ["enron"],
  "output_format": "text"
}
```

**Response** :
```json
{
  "question": "What is Enron's revenue?",
  "answer": "Based on available documents...",
  "language": "en",
  "confidence": 0.82,
  "sources": [
    {
      "id": "doc-123",
      "score": 0.91,
      "source": "enron",
      "lang": "en",
      "type": "email"
    }
  ],
  "mode": "generate",
  "quality_pass": true,
  "escalate": false,
  "cites_ok": true
}
```

### Quality Gate Thresholds

- `confidence >= 0.35` → `quality_pass = true`
- `confidence < 0.25` → `escalate = true`
- `hallucination == true` → `escalate = true`
- `cites_ok == false` → warning badge (frontend)

---

## 📊 Observabilité

### Logs

#### `logs/llm_responses.jsonl`
```json
{
  "timestamp": "2025-11-13T10:30:00Z",
  "question": "What is revenue?",
  "generation": "Based on...",
  "detected_ids": ["doc-123", "doc-456"],
  "model": "gpt-3.5-turbo"
}
```

#### `logs/metrics.jsonl`
```json
{
  "avg_score": 0.89,
  "confidence": 0.82,
  "cites_ok": true,
  "overlap_ratio": 0.75,
  "hallucination": false,
  "quality_pass": true,
  "escalate": false
}
```

#### `snapshots/for_review/*.json`
Cas avec `quality_pass=false` (human review requis).

---

## 🆘 Troubleshooting

### ❌ Frontend → Backend CORS error

**Symptôme** : "Access-Control-Allow-Origin" missing

**Solutions** :
1. Vérifier `ALLOWED_ORIGINS` dans `main.py`
2. Vérifier `VITE_API_BASE` correct
3. Redéployer backend

### ❌ Backend won't start (Railway)

```bash
railway logs --service backend --follow
```

**Causes** :
- `PORT` env var → vérifier Dockerfile (`${PORT:-8000}`)
- `OPENAI_API_KEY` vide → ajouter secret
- Qdrant unreachable → vérifier URL/clé

### ❌ Qdrant returns 0 documents

```bash
# Verify collection
curl -X GET "https://your-qdrant-url/collections/knowledge_base_main" \
  -H "api-key: your-key"
```

**Cause** : Collection vide → ingest documents

### ❌ LLM hallucination (quality_pass=false)

1. ↓ Temperature : `0.2 → 0.1`
2. Améliorer prompts dans `agents/prompts.md`
3. Vérifier retrieval pertinent

---

## 🔗 Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Railway Docs](https://docs.railway.app/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Vite Docs](https://vitejs.dev/)

---

## 📝 License

MIT

---

## 👤 Author

**GenAI Workflow Automate** - RAG pipeline for customer support automation

- **Demo** : https://gzz2v6tnxp-ctrl.github.io/genai-workflow-automate/
- **Backend** : https://backend-xxx.up.railway.app/ (après déploiement)

---

## 🤝 Contributions

```bash
# Feature branch
git checkout -b feature/your-feature
git commit -am "feat: your feature"
git push origin feature/your-feature
# Créer PR sur GitHub
```

Merci ! 🎉
