```
# 🤖 GenAI Workflow Automation

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Technologies](#technologies)
- [Installation](#installation)
- [Configuration](#configuration)
- [Pipeline de Données](#pipeline-de-données)
- [API Endpoints](#api-endpoints)
- [Migration Cloud](#migration-cloud)
- [Développement](#développement)
- [Data & Licences](#data--licences)
- [Références](#références)

---

## 🎯 Vue d'ensemble

**GenAI Workflow Automation** est une solution MVP de traitement automatisé de tickets clients du secteur financier utilisant une architecture **RAG (Retrieval-Augmented Generation)** avec LLM. Le système permet de :

- ✅ Ingérer et vectoriser des documents provenant de multiples sources
- ✅ Effectuer une recherche sémantique performante sur une base de connaissances distribuée
- ✅ Générer des réponses contextualisées via LLM (OpenAI GPT)
- ✅ Orchestrer des workflows complexes avec LangGraph
- ✅ Déployer en production avec Qdrant Cloud

### 🎪 Cas d'usage

**Secteur** : Services Financiers (Banque, Assurance, FinTech)

**Problématique** : Automatiser le traitement de tickets clients (plaintes, demandes d'information) avec un système intelligent capable de comprendre le contexte et fournir des réponses pertinentes basées sur l'historique et la documentation interne.

**Solution** : Pipeline RAG multi-sources combinant recherche vectorielle et génération LLM.

---

## 🏗️ Architecture

### Architecture Globale

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────┤
│  • Synthetic Docs (100 docs, FR/EN)                             │
│  • CFPB Complaints (10K records, EN)                            │
│  • Enron Emails (Corporate communication, EN)                   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Document Loading (LangChain Document abstraction)           │
│  2. Text Chunking (RecursiveCharacterTextSplitter)              │
│     • Chunk size: 600 chars (~384 tokens)                       │
│     • Overlap: 100 chars                                        │
│  3. Embedding Generation (sentence-transformers)                │
│     • Model: all-mpnet-base-v2                                  │
│     • Dimension: 768                                            │
│  4. Batch Insertion (100 points/batch)                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR DATABASE                                │
├─────────────────────────────────────────────────────────────────┤
│  Qdrant (Docker local + Cloud)                                  │
│  • Collection: demo_public (synthetic only)                     │
│  • Collection: knowledge_base_main (all sources)                │
│  • Distance metric: COSINE                                      │
│  • Snapshots: Automated backup/restore                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL SYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│  • Semantic search with filters                                 │
│  • Top-k results with score threshold                           │
│  • Metadata filtering (source, date, etc.)                      │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                             │
├─────────────────────────────────────────────────────────────────┤
│  retrieve → grade_documents → generate / fallback               │
│  • State management                                             │
│  • Conditional routing                                          │
│  • Error handling                                               │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM GENERATION                                 │
├─────────────────────────────────────────────────────────────────┤
│  OpenAI GPT (via LangChain)                                     │
│  • Contextualized response generation                           │
│  • Source citation                                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                            │
├─────────────────────────────────────────────────────────────────┤
│  • /search : Semantic search                                    │
│  • /build-collections : Collection management                   │
│  • /populate-collections : Data ingestion                       │
└─────────────────────────────────────────────────────────────────┘
```

### LangGraph Workflow

```
┌──────────┐
│  START   │
└────┬─────┘
     │
     ▼
┌──────────────┐
│   retrieve   │  ← Recherche sémantique dans Qdrant
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ grade_documents  │  ← Évaluation de la pertinence
└──────┬───────────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌──────────┐   ┌──────────┐
│ generate │   │ fallback │
└────┬─────┘   └────┬─────┘
     │              │
     └──────┬───────┘
            │
            ▼
       ┌────────┐
       │  END   │
       └────────┘
```

---

## 🛠️ Technologies

### Stack Technique

| Composant | Technologie | Version | Usage |
|-----------|-------------|---------|-------|
| **Orchestration** | LangGraph | Latest | Workflow management |
| **LLM Framework** | LangChain | >=0.0.278 | RAG pipeline |
| **LLM Provider** | OpenAI | Latest | Text generation |
| **Vector DB** | Qdrant | >=1.14.2 | Semantic search |
| **Embeddings** | Sentence-Transformers | >=2.2.2 | Text vectorization |
| **API Framework** | FastAPI | Latest | REST API |
| **Server** | Uvicorn | Latest | ASGI server |
| **Data Processing** | Pandas, NumPy | Latest | Data manipulation |
| **Environment** | Python-dotenv | Latest | Config management |
| **Testing** | Pytest | Latest | Unit tests |
| **UI Demo** | Gradio | >=3.14.0 | Interactive demo |

### Modèles ML

- **Embedding Model** : `all-mpnet-base-v2`
  - Dimension : 768
  - Max tokens : 384
  - Languages : Multilingual (50+ languages)
  - Performance : SOTA sur SBERT benchmarks

- **LLM** : OpenAI GPT-3.5/4
  - Task : Response generation
  - Context window : 16K+ tokens

---

## 📦 Installation

### Prérequis

```bash
Python >= 3.9
Docker >= 20.10 (pour Qdrant local)
Git
```

### Installation des dépendances

```bash
# Cloner le repository
git clone https://github.com/gzz2v6tnxp-ctrl/genai-workflow-automate.git
cd genai-workflow-automate

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### Lancer Qdrant (Docker)

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant:latest
```

---

## ⚙️ Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Qdrant Local
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Qdrant Cloud (pour production)
QDRANT_CLOUD_URL=https://your-cluster.aws.cloud.qdrant.io
QDRANT_API_KEY=your-api-key-here

# Embedding Configuration
VECTOR_DIMENSION=768
DEFAULT_EMBEDDING_MODEL=all-mpnet-base-v2

# OpenAI API
OPENAI_API_KEY=sk-...

# Collection Names
COLLECTION_NAME=genai_workflow_docs_test
```

### Structure de Configuration

```python
# scripts/config.py
- QDRANT_HOST / PORT : Qdrant local instance
- QDRANT_CLOUD_URL / API_KEY : Production cluster
- VECTOR_DIMENSION : Embedding dimension (768)
- DEFAULT_EMBEDDING_MODEL : Model name
- OPENAI_API_KEY : LLM API key
```

---

## 📊 Pipeline de Données

### 1. Ingestion des Sources

```bash
# Charger les données synthétiques
python scripts/ingest/ingest_synth.py

# Charger les plaintes CFPB
python scripts/ingest/ingest_cfpb.py

# Charger les emails Enron
python scripts/ingest/ingest_enron_mail.py
```

### 2. Création des Collections

```bash
# Créer les collections Qdrant
python scripts/vector_store/build_collection.py
```

**Collections créées** :
- `demo_public` : 100 docs synthétiques (demo publique)
- `knowledge_base_main` : ~5000 chunks (production)

### 3. Génération des Embeddings et Population

```bash
# Générer les embeddings et peupler Qdrant
python scripts/vector_store/populate_collection.py
```

**Process** :
1. Chargement des documents depuis toutes les sources
2. Chunking avec RecursiveCharacterTextSplitter (600 chars, overlap 100)
3. Génération des embeddings (batch processing)
4. Insertion par lots dans Qdrant (100 points/batch)

### 4. Vérification

```bash
# Statistiques des collections
python scripts/vector_store/retrieve.py --count
```

---

## 🚀 API Endpoints

### Lancer l'API

```bash
# Mode développement
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Mode production
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Endpoints Disponibles

#### 1. Recherche Sémantique

```http
POST /api/retriever/search
Content-Type: application/json

{
  "query": "problème de carte de crédit refusée",
  "collection_name": "knowledge_base_main",
  "top_k": 5,
  "score_threshold": 0.7,
  "filters": {
    "source": "cfpb_complaints"
  }
}
```

**Response** :
```json
{
  "results": [
    {
      "id": "uuid",
      "score": 0.89,
      "content": "Document content...",
      "metadata": {
        "source": "cfpb_complaints",
        "product": "Credit card",
        "issue": "Transaction declined"
      }
    }
  ],
  "total": 5
}
```

#### 2. Compter les Documents

```http
GET /api/retriever/count?collection_name=knowledge_base_main
```

#### 3. Récupérer un Document par ID

```http
GET /api/retriever/documents/{document_id}?collection_name=knowledge_base_main
```

#### 4. Gestion des Collections

```http
POST /api/ingestion/build-collections
POST /api/ingestion/populate-collections
```

### Documentation Interactive

Accédez à la documentation Swagger :
```
http://localhost:8000/docs
```

---

## ☁️ Migration Cloud

### Processus de Migration

Consultez le guide détaillé : [`docs/MIGRATION_GUIDE.md`](docs/MIGRATION_GUIDE.md)

#### Méthode Automatique

```bash
# Migration complète (local → cloud)
python scripts/vector_store/migrate_to_cloud.py
```

#### Méthode Manuelle

```bash
# 1. Créer les snapshots
python scripts/vector_store/create_snapshot.py

# 2. Uploader vers le cloud
python scripts/vector_store/restore_snapshot.py
```

### Snapshots

Les snapshots sont stockés dans `./snapshots/` :

```
snapshots/
├── demo_public-{timestamp}.snapshot
└── knowledge_base_main-{timestamp}.snapshot
```

**Fonctionnalités** :
- ✅ Backup automatique
- ✅ Compression des données
- ✅ Migration entre clusters
- ✅ Restauration point-in-time

---

## 👨‍💻 Développement

### Structure du Projet

```
genai-workflow-automate/
├── agents/                    # LangGraph workflows
│   ├── graph.py              # Graph definition
│   └── state.py              # State management
├── backend/                   # Backend logic (future)
├── data/                      # Raw datasets
│   ├── complaints.csv/
│   ├── enron_mail_20150507/
│   └── synth/
├── docs/                      # Documentation
│   └── MIGRATION_GUIDE.md
├── frontend/                  # UI (future)
├── infra/                     # Infrastructure
│   └── Dockerfile
├── notebooks/                 # Jupyter notebooks
│   └── analyse_data.ipynb
├── router/                    # FastAPI routers
│   ├── ingestion.py
│   └── retriever.py
├── scripts/                   # Data processing scripts
│   ├── chunking.py
│   ├── config.py
│   ├── embed.py
│   ├── ingest/
│   │   ├── ingest_cfpb.py
│   │   ├── ingest_enron_mail.py
│   │   └── ingest_synth.py
│   └── vector_store/
│       ├── build_collection.py
│       ├── create_snapshot.py
│       ├── migrate_to_cloud.py
│       ├── populate_collection.py
│       ├── restore_snapshot.py
│       └── retrieve.py
├── snapshots/                 # Qdrant snapshots
├── main.py                    # FastAPI app entry point
├── requirements.txt
└── README.md
```

### Workflow de Développement

```bash
# 1. Créer une branche feature
git checkout -b feature/nouvelle-fonctionnalite

# 2. Développer et tester
pytest tests/

# 3. Formater le code (optionnel)
black .
pre-commit run --all-files

# 4. Commit et push
git add .
git commit -m "feat: description de la fonctionnalité"
git push origin feature/nouvelle-fonctionnalite

# 5. Créer une Pull Request
```

### Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=scripts --cov-report=html

# Tests spécifiques
pytest tests/test_retrieval.py
```

### Linting et Formatage

```bash
# Formater le code
black scripts/ router/ agents/

# Vérifier la qualité
flake8 scripts/ router/ agents/
```

---

## 📊 Data & Licences

### Sources de Données

#### 1. CFPB Consumer Complaint Database

- **Source** : [Consumer Financial Protection Bureau](https://www.consumerfinance.gov/data-research/consumer-complaints/)
- **Licence** : Domaine public (US federal data)
- **Description** : Base de données de plaintes clients dans le secteur financier américain
- **Volume** : 10,000 enregistrements (subset)
- **Champs utilisés** :
  - `Consumer complaint narrative` : Description textuelle de la plainte
  - `Product` : Catégorie de produit financier
  - `Issue` : Type de problème
  - `Company response to consumer` : Réponse de l'entreprise
- **Modifications** : Échantillonnage aléatoire, nettoyage des données sensibles, anonymisation
- **Citation** : 
  ```
  Consumer Financial Protection Bureau. Consumer Complaint Database. 
  Retrieved from https://www.consumerfinance.gov/data-research/consumer-complaints/
  ```

#### 2. Enron Email Dataset

- **Source** : [CMU Enron Email Dataset](https://www.cs.cmu.edu/~enron/)
- **Licence** : Publié pour la recherche (public domain equivalent)
- **Description** : Corpus d'emails professionnels de la société Enron
- **Volume** : Subset de plusieurs milliers d'emails
- **Champs utilisés** :
  - `Subject` : Objet de l'email
  - `Body` : Corps du message
  - `From/To` : Expéditeur/Destinataire (anonymisés)
  - `Date` : Date d'envoi
- **Modifications** : Extraction de sous-ensembles pertinents, nettoyage, anonymisation des identités
- **Citation** :
  ```
  Klimt, B., & Yang, Y. (2004). The Enron Corpus: A New Dataset for Email Classification Research. 
  European Conference on Machine Learning (ECML).
  ```

#### 3. Synthetic Financial Documents

- **Source** : Générés spécifiquement pour ce projet
- **Licence** : MIT (open source)
- **Description** : Documents synthétiques simulant des tickets clients et documentation financière
- **Volume** : 100 documents
- **Langues** : Français, Anglais
- **Champs** :
  - `content` : Contenu textuel du document
  - `metadata` : Métadonnées structurées (type, langue, catégorie)
- **Génération** : Template-based avec variations aléatoires
- **Format** : JSONL

### Considérations Éthiques et Légales

#### Confidentialité

- ✅ Toutes les données personnelles identifiables (PII) ont été anonymisées
- ✅ Aucune information bancaire réelle n'est incluse
- ✅ Les emails Enron utilisent des données déjà publiques et anonymisées

#### Usage Autorisé

Ce projet est destiné à :
- 📚 Recherche et développement en NLP/ML
- 🎓 Éducation et formation
- 🔬 Démonstration de concepts techniques
- 💼 Portfolio professionnel

#### Restrictions

❌ **Ne pas utiliser** pour :
- Production commerciale sans vérification des licences
- Traitement de données clients réelles sans consentement
- Prise de décisions financières automatisées sans supervision humaine

### Conformité RGPD

Pour une utilisation en production avec données réelles :

1. **Consentement** : Obtenir le consentement explicite des utilisateurs
2. **Minimisation** : Collecter uniquement les données nécessaires
3. **Anonymisation** : Appliquer des techniques d'anonymisation robustes
4. **Droit à l'oubli** : Implémenter des mécanismes de suppression de données
5. **Sécurité** : Chiffrement des données sensibles (at rest + in transit)

### Datasets Complémentaires (Recommandations)

Pour étendre le système :

- **Financial QA** : [FiQA Dataset](https://sites.google.com/view/fiqa/) (CC BY-SA)
- **Banking77** : [Banking Intent Dataset](https://arxiv.org/abs/2003.04807) (CC BY 4.0)
- **FinBERT** : [Financial Domain Corpus](https://huggingface.co/ProsusAI/finbert) (Apache 2.0)

---

## 📚 Références

### Documentation Technique

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Articles de Recherche

1. **RAG Architecture**
   - Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS.

2. **Sentence Embeddings**
   - Reimers, N., & Gurevych, I. (2019). "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks." EMNLP.

3. **Vector Databases**
   - Johnson, J., Douze, M., & Jégou, H. (2019). "Billion-scale similarity search with GPUs." IEEE Transactions on Big Data.

### Tutoriels et Guides

- [RAG Tutorial by LangChain](https://python.langchain.com/docs/use_cases/question_answering/)
- [Qdrant Snapshot Migration](https://qdrant.tech/documentation/database-tutorials/create-snapshot/)
- [Building Production-Ready RAG Systems](https://www.pinecone.io/learn/retrieval-augmented-generation/)

---

## 📄 Licence

Ce projet est sous licence **MIT**.

```
MIT License

Copyright (c) 2025 [Votre Nom]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[Texte complet de la licence MIT]
```

---

## 🤝 Contribution

Les contributions sont bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Guidelines

- Suivre les conventions PEP 8
- Ajouter des tests pour les nouvelles fonctionnalités
- Documenter les fonctions avec docstrings
- Mettre à jour le README si nécessaire

---

## 📧 Contact

**Auteur** : [Votre Nom]  
**Email** : votre.email@example.com  
**LinkedIn** : [Votre profil LinkedIn]  
**GitHub** : [@gzz2v6tnxp-ctrl](https://github.com/gzz2v6tnxp-ctrl)

---

## 🙏 Remerciements

- [LangChain](https://github.com/langchain-ai/langchain) pour le framework RAG
- [Qdrant](https://github.com/qdrant/qdrant) pour la base vectorielle performante
- [Sentence-Transformers](https://github.com/UKPLab/sentence-transformers) pour les modèles d'embedding
- [OpenAI](https://openai.com/) pour les capacités LLM
- [CFPB](https://www.consumerfinance.gov/) et [CMU](https://www.cs.cmu.edu/) pour les datasets publics

---

**⭐ Si ce projet vous a été utile, n'hésitez pas à lui donner une étoile sur GitHub !**