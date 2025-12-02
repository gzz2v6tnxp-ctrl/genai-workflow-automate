# 🚀 GenAI Workflow Automate

Une **pipeline RAG (Retrieval-Augmented Generation) robuste** avec **COV-RAG** (Chain-of-Verification) pour minimiser les hallucinations, qualité d'évaluation, escalade humaine et déploiement hybride.

**Stack technique** :
- 🧠 **LLM** : OpenAI ChatGPT (gpt-3.5-turbo / gpt-4)
- 🔍 **Retrieval** : Qdrant Cloud (vecteur DB) + Récupération hybride
- 🛡️ **Anti-Hallucination** : Chain-of-Verification (CoVE)
- 📊 **Orchestration** : LangGraph (agentic workflows)
- ⚡ **Backend** : FastAPI (Python)
- 🎨 **Frontend** : React + Vite + TypeScript
- 🐳 **Deployment** : Docker + Railway (backend) + GitHub Pages (frontend)

---

## 🆕 Nouveautés: COV-RAG avec Chain-of-Verification

### Qu'est-ce que COV-RAG?

COV-RAG est une architecture RAG avancée qui intègre **Chain-of-Verification (CoVE)** pour détecter et corriger automatiquement les hallucinations du LLM. https://arxiv.org/pdf/2410.05801 

**Pipeline COV-RAG:**
```
Question → Récupération Hybride → Re-ranking → Génération Initiale
                                                       ↓
                                            Extraction des Affirmations
                                                       ↓
                                            Vérification vs Sources
                                                       ↓
                                            Correction si Hallucination
                                                       ↓
                                            Réponse Finale + Score Confiance
```

### Techniques Anti-Hallucination

| Technique | Description | Impact |
|-----------|-------------|--------|
| **Récupération Hybride** | Dense (embedding) + MMR (diversité) | Meilleure couverture |
| **Re-ranking** | 70% sémantique + 30% lexical | Documents plus pertinents |
| **Ancrage Strict** | Citation obligatoire des sources `[ID]` | Traçabilité |
| **CoVE** | Vérification des affirmations vs sources | Détection hallucinations |
| **Correction Auto** | Réécriture des parties incorrectes | Réponses fiables |
| **Score de Confiance** | Combinaison similarité + vérification | Transparence |

---

## 📋 Quick Links

1. [Installation locale](#installation-locale)
2. [Configuration](#configuration)
3. [COV-RAG: Anti-Hallucination](#cov-rag-anti-hallucination)
4. [Développement](#développement)
5. [Déploiement hybride](#déploiement-hybride)
6. [API Endpoints](#api-endpoints)
7. [Observabilité](#observabilité)
8. [Troubleshooting](#troubleshooting)

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

## 🛡️ COV-RAG: Anti-Hallucination

### Architecture des Modules

```
agents/
├── cov_rag.py           # Classes principales COV-RAG
│   ├── COVRAGRetriever  # Récupération hybride + re-ranking
│   ├── ChainOfVerification  # Pipeline CoVE
│   └── COVRAGAgent      # Agent intégré
├── cov_rag_graph.py     # Workflow LangGraph COV-RAG
│   ├── retrieve_with_rerank
│   ├── generate_initial
│   ├── extract_claims
│   ├── verify_claims
│   ├── correct_if_needed
│   └── evaluate_final
└── state.py             # États du graphe
```

### Utilisation via l'API

**Avec CoVE (défaut - recommandé):**
```bash
curl -X POST "http://localhost:8000/api/v1/chatbot/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Ma carte bancaire est bloquée, que faire?",
    "collection": "demo_public",
    "enable_cove": true
  }'
```

**Sans CoVE (plus rapide):**
```bash
curl -X POST "http://localhost:8000/api/v1/chatbot/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Ma carte bancaire est bloquée, que faire?",
    "enable_cove": false
  }'
```

### Utilisation Programmatique

```python
# Méthode 1: API Simple (sync)
from agents import run_cov_rag

result = run_cov_rag(
    question="Ma carte bancaire est bloquée",
    collection="demo_public",
    enable_cove=True
)

print(f"Réponse: {result['answer']}")
print(f"Confiance: {result['confidence']:.0%}")
print(f"Hallucination détectée: {result['hallucination_detected']}")
print(f"Corrections appliquées: {result['corrections_made']}")

# Méthode 2: Agent Async
import asyncio
from agents import create_cov_rag_agent

async def main():
    agent = create_cov_rag_agent(enable_cove=True)
    result = await agent.answer("Ma carte est bloquée")
    
    print(f"Réponse: {result.answer}")
    print(f"Score: {result.confidence_score:.0%}")
    
    # Vérifications détaillées
    for v in result.verifications:
        status = "✅" if v.is_verified else "❌"
        print(f"{status} {v.original_claim[:50]}...")

asyncio.run(main())
```

### Pipeline CoVE Détaillé

#### Étape 1: Extraction des Affirmations
```python
# Le LLM extrait les faits vérifiables
affirmations = [
    {"fact": "La carte peut être débloquée en 24h", "category": "temporal"},
    {"fact": "Le numéro d'urgence est le 0800 123 456", "category": "numerical"},
]
```

#### Étape 2: Génération des Questions de Vérification
```python
questions = [
    {"question": "Quel est le délai de déblocage d'une carte?", "fact": "..."},
    {"question": "Quel est le numéro d'urgence?", "fact": "..."},
]
```

#### Étape 3: Vérification contre les Sources
```python
# Chaque affirmation est vérifiée
verification = {
    "is_verified": False,  # Non trouvé dans les sources
    "confidence": 0.3,
    "evidence": "Aucune mention du délai de 24h dans les documents",
    "correction": "Le délai dépend du type de blocage"
}
```

#### Étape 4: Correction Automatique
```python
# La réponse est corrigée automatiquement
original = "Votre carte sera débloquée en 24h..."
corrected = "Le délai de déblocage dépend du type de blocage..."
```

### Métriques COV-RAG

Les métriques sont enregistrées dans `logs/cov_rag_metrics.jsonl`:

```json
{
  "timestamp": "2025-12-02T10:30:00Z",
  "question": "Ma carte est bloquée",
  "similarity_score": 0.85,
  "cove_confidence": 0.9,
  "final_confidence": 0.87,
  "hallucination_detected": false,
  "corrections_made": 0,
  "num_verifications": 3,
  "quality_pass": true
}
```

### Seuils de Qualité

| Métrique | Seuil | Action |
|----------|-------|--------|
| `final_confidence >= 0.4` | ✅ Pass | Réponse retournée |
| `final_confidence < 0.4` | ⚠️ Warning | Badge UI + log |
| `final_confidence < 0.3` | 🚨 Escalate | Revue humaine |
| `hallucination_detected` | 🔄 Correct | Correction auto |

---

## 🛠️ Développement

### Structure

```
genai-workflow-automate/
├── agents/
│   ├── graph.py              # StateGraph RAG standard
│   ├── cov_rag.py            # 🆕 COV-RAG: Retriever + CoVE + Agent
│   ├── cov_rag_graph.py      # 🆕 Workflow LangGraph COV-RAG
│   ├── state.py              # TypedDict + COVRAGGraphState
│   └── prompts.md            # Prompts Markdown
├── router/
│   ├── chatbot.py            # POST /api/v1/chatbot/query (COV-RAG + Standard)
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
│   ├── metrics.jsonl         # Quality metrics (standard)
│   └── cov_rag_metrics.jsonl # 🆕 COV-RAG metrics
├── main.py                   # FastAPI entry
├── Dockerfile                # Backend
├── docker-compose.yml        # Local compose
├── railway.toml              # Railway config
└── README.md
```

### Workflow LangGraph - COV-RAG

```
Input: question, collection, sources_filter, enable_cove
  ↓
[retrieve_with_rerank] → Qdrant (hybrid + rerank)
  ↓
[generate_initial] → LLM generation + ancrage strict
  ↓ (si enable_cove=true)
[extract_claims] → Extraction affirmations vérifiables
  ↓
[verify_claims] → Vérification vs sources (CoVE)
  ↓
[correct_if_needed] → Correction hallucinations
  ↓
[evaluate_final] → Quality gate final
  ├─ quality_pass=true → END (return)
  ├─ escalate=true → [human_review]
  └─ else → END (avec warning)
```

### Workflow LangGraph - Standard (sans CoVE)

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

- **retrieve** / **retrieve_with_rerank** : Semantic search + filter + rerank
- **grade** : Score documents (relevant/marginal/not_relevant)
- **generate** / **generate_initial** : LLM + citation anchoring
- **extract_claims** : 🆕 Extraction affirmations (CoVE)
- **verify_claims** : 🆕 Vérification vs sources (CoVE)
- **correct_if_needed** : 🆕 Correction automatique (CoVE)
- **evaluate** / **evaluate_final** : Quality gate (confidence, hallucination)
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
  "output_format": "text",
  "enable_cove": true
}
```

**Paramètres:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `question` | string | **requis** | Question utilisateur |
| `collection` | string | `demo_public` | Collection Qdrant |
| `sources_filter` | string[] | `null` | Filtrer: `synth`, `cfpb`, `enron` |
| `output_format` | string | `text` | Format: `text` ou `json` |
| `enable_cove` | bool | `true` | 🆕 Activer Chain-of-Verification |

**Response (avec CoVE)** :
```json
{
  "question": "What is Enron's revenue?",
  "answer": "Based on available documents [doc-123]...",
  "language": "en",
  "similarity_score": 0.91,
  "confidence_score": 0.85,
  "sources": [
    {
      "id": "doc-123",
      "score": 0.91,
      "source": "enron",
      "lang": "en",
      "type": "email"
    }
  ],
  "mode": "cov_rag",
  "quality_pass": true,
  "escalate": false,
  "cites_ok": true,
  "cove_enabled": true,
  "hallucination_detected": false,
  "corrections_made": 0,
  "verifications": [
    {
      "claim": "Revenue was $100 billion",
      "is_verified": true,
      "confidence": 0.95,
      "evidence": "Document states: 'Revenue reached $100.8 billion'",
      "correction": null
    }
  ],
  "initial_answer": null
}
```

**Response (avec corrections)** :
```json
{
  "answer": "Le délai dépend du type de blocage...",
  "hallucination_detected": true,
  "corrections_made": 1,
  "verifications": [
    {
      "claim": "La carte sera débloquée en 24h",
      "is_verified": false,
      "confidence": 0.3,
      "evidence": "Aucune mention du délai dans les sources",
      "correction": "Le délai dépend du type de blocage"
    }
  ],
  "initial_answer": "Votre carte sera débloquée en 24h..."
}
```
```

### Quality Gate Thresholds

| Métrique | Seuil | Résultat |
|----------|-------|----------|
| `confidence >= 0.40` | ✅ | `quality_pass = true` |
| `confidence < 0.40` | ⚠️ | `quality_pass = false` |
| `confidence < 0.30` | 🚨 | `escalate = true` |
| `hallucination_detected` | 🔄 | Correction automatique (CoVE) |
| `cites_ok == false` | ⚠️ | Warning badge (frontend) |

### Modes de Réponse

| Mode | Description | CoVE |
|------|-------------|------|
| `cov_rag` | COV-RAG avec vérification réussie | ✅ |
| `cov_rag_fallback` | COV-RAG avec confiance faible | ✅ |
| `generate` | RAG standard | ❌ |
| `fallback` | Réponse générique | ❌ |
| `human_review` | Escalade humaine | ✅/❌ |

---

## 📊 Observabilité

### Logs

#### `logs/llm_responses.jsonl`
```json
{
  "timestamp": "2025-12-02T10:30:00Z",
  "question": "What is revenue?",
  "generation": "Based on...",
  "detected_ids": ["doc-123", "doc-456"],
  "model": "gpt-3.5-turbo"
}
```

#### `logs/metrics.jsonl` (RAG Standard)
```json
{
  "timestamp": "2025-12-02T10:30:00Z",
  "avg_score": 0.89,
  "confidence": 0.82,
  "cites_ok": true,
  "overlap_ratio": 0.75,
  "hallucination": false,
  "quality_pass": true,
  "escalate": false
}
```

#### `logs/cov_rag_metrics.jsonl` (COV-RAG) 🆕
```json
{
  "timestamp": "2025-12-02T10:30:00Z",
  "question": "Ma carte est bloquée",
  "similarity_score": 0.85,
  "cove_confidence": 0.9,
  "final_confidence": 0.87,
  "cites_ok": true,
  "hallucination_detected": false,
  "quality_pass": true,
  "escalate": false,
  "corrections_made": 0,
  "num_sources": 5,
  "num_verifications": 3
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

**Avec COV-RAG (recommandé):**
1. Activer CoVE: `enable_cove: true` dans la requête
2. Les hallucinations sont automatiquement détectées et corrigées
3. Vérifier `verifications` dans la réponse pour les détails

**Sans COV-RAG:**
1. ↓ Temperature : `0.2 → 0.1`
2. Améliorer prompts dans `agents/prompts.md`
3. Vérifier retrieval pertinent

### ❌ COV-RAG lent

**Cause**: Pipeline CoVE ajoute ~2-3 appels LLM supplémentaires

**Solutions**:
1. Utiliser `enable_cove: false` pour les requêtes simples
2. Réduire `max_claims_to_verify` dans la config (défaut: 5)
3. Utiliser un modèle plus rapide (gpt-3.5-turbo vs gpt-4)

### ❌ Trop de corrections CoVE

**Cause**: Le LLM génère des affirmations non présentes dans les sources

**Solutions**:
1. Améliorer le prompt d'ancrage dans `agents/cov_rag.py`
2. Augmenter `top_k` pour récupérer plus de documents
3. Baisser `score_threshold` pour inclure plus de sources

---

## 🔗 Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Railway Docs](https://docs.railway.app/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Vite Docs](https://vitejs.dev/)
- [Chain-of-Verification Paper](https://arxiv.org/abs/2309.11495) - Référence CoVE

---

## 📝 License

MIT

---

## 👤 Author

**GenAI Workflow Automate** - RAG pipeline with COV-RAG for low-hallucination customer support automation

- **Demo** : https://gzz2v6tnxp-ctrl.github.io/genai-workflow-automate/
- **Backend** : https://backend-xxx.up.railway.app/ (après déploiement)

### Fonctionnalités Principales

✅ **Retrieval-Augmented Generation (RAG)**
✅ **Chain-of-Verification (CoVE)** - Anti-hallucination
✅ **Récupération Hybride** - Dense + MMR
✅ **Re-ranking** - Pertinence optimisée
✅ **Multi-langue** - FR/EN auto-détecté
✅ **Escalade Humaine** - Confiance faible
✅ **Observabilité** - Métriques + Logs

---

## 🎨 Frontend Moderne v2.0

### Interface Utilisateur Améliorée

Le frontend a été entièrement repensé avec un **design moderne et intuitif** pour afficher toutes les métriques COV-RAG en temps réel :

#### ✨ Nouveaux Composants

1. **COVEMetrics** - Affichage des vérifications claim-by-claim
   - Badge CoVE actif avec gradient violet/bleu
   - Détection d'hallucinations avec compteur de corrections
   - Liste détaillée des vérifications (claim, confiance, evidence)
   - Comparaison avant/après correction (section pliable)

2. **AdvancedMetricsPanel** - Métriques avancées avec visualisations
   - Grille 2x2 : Confiance, Latence, Qualité, Hallucinations
   - Tendances avec indicateurs (↑↓)
   - Métriques secondaires : citations, sources/requête, scores

#### 🎯 Composants Refactorisés

- **SystemStatus** : Design moderne avec Tailwind CSS, espacements optimisés
- **MetricsDashboard** : Cartes avec gradients colorés, séparateurs visuels nets
- **ChatPanel** : Intégration complète des métriques COV-RAG

#### 📊 Corrections d'Espacement

**Avant** :
```
Erreurs1          ❌ Texte collé
Qualité0 0%       ❌ Illisible
```

**Après** :
```
Erreurs        1       ✅ Espacé
Qualité        0 (0%)  ✅ Lisible
```

**Guide complet** : Voir [`frontend/VISUAL_GUIDE.md`](frontend/VISUAL_GUIDE.md) et [`frontend/FRONTEND_UPDATES.md`](frontend/FRONTEND_UPDATES.md)

#### 🚀 Démarrage Rapide

```bash
# Windows
start-frontend.bat

# Linux/Mac
cd frontend && npm install && npm run dev
```

Interface disponible sur : **http://localhost:5173**

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
