# 📚 Guide de Référence - Sources de Données Qdrant

Ce document décrit les sources de données disponibles dans le cluster Qdrant Cloud, leurs caractéristiques, et comment les interroger efficacement avec le système RAG.

---

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Sources Disponibles](#sources-disponibles)
  - [1. Données Synthétiques (synth)](#1-données-synthétiques-synth)
  - [2. Plaintes CFPB (cfpb)](#2-plaintes-cfpb-cfpb)
  - [3. Emails Enron (enron)](#3-emails-enron-enron)
- [Métadonnées Communes](#métadonnées-communes)
- [Stratégies de Filtrage](#stratégies-de-filtrage)
- [Exemples de Requêtes](#exemples-de-requêtes)
- [Statistiques et Performance](#statistiques-et-performance)
- [Best Practices](#best-practices)

---

## 🎯 Vue d'ensemble

### Collections Disponibles

| Collection | Usage | Nombre de Documents | Sources Incluses |
|-----------|-------|---------------------|------------------|
| `demo_public` | Démonstration publique | ~100-150 | Synthétique uniquement |
| `knowledge_base_main` | Production | ~3000-5000 | Synth + CFPB + Enron |

### Architecture de Stockage

```
Qdrant Cloud
├── Collection: demo_public
│   └── Source: synth (100-150 chunks)
│
└── Collection: knowledge_base_main
    ├── Source: synth (100-150 chunks, 3-5%)
    ├── Source: cfpb (2000-3000 chunks, 60-70%)
    └── Source: enron (500-1500 chunks, 20-30%)
```

### Modèle d'Embedding

- **Modèle** : `sentence-transformers/all-mpnet-base-v2`
- **Dimension** : 768
- **Max tokens** : 384 (~600 caractères)
- **Langues** : Multilingue (50+ langues incluant FR et EN)
- **Distance** : COSINE similarity

---

## 📊 Sources Disponibles

### 1. Données Synthétiques (`synth`)

#### **Caractéristiques**

- **Volume** : ~100-150 chunks
- **Langues** : Français (60%) + Anglais (40%)
- **Type** : Tickets de support client bancaire simulés
- **Format** : JSONL
- **Domaine** : Services financiers (banque, assurance)
- **Cas d'usage** : Plaintes, demandes d'information, réclamations

#### **Métadonnées Disponibles**

| Champ | Type | Valeurs Possibles | Description |
|-------|------|-------------------|-------------|
| `source` | string | `"synth"` | Identifiant de la source |
| `type` | string | `"ticket_support"` | Type de document |
| `lang` | string | `"fr"`, `"en"` | Langue du document |
| `priority` | string | `"high"`, `"medium"`, `"low"` | Niveau de priorité |
| `date` | string | ISO 8601 | Date du ticket |
| `customer_id` | string | UUID | ID client anonymisé |
| `id` | string | UUID | ID unique du document |

#### **Exemples de Contenu**

**Français :**
```
Objet : Problème de prélèvement automatique

Bonjour,

J'ai constaté un prélèvement non autorisé de 150€ sur mon compte 
le 15/10/2025. Le libellé indique "PRELEVEMENT SEPA XYZ SARL". 
Je n'ai jamais autorisé ce prélèvement. Merci de régulariser 
cette situation au plus vite.
```

**Anglais :**
```
Subject: Unauthorized charge on account [ACCOUNT]

Hello,

I have noticed a double charge affecting my account [ACCOUNT]. 
The transaction reference is [NUMBER] and occurred on 2025-10-03. 
Please advise the next steps to resolve this issue.
```

#### **Cas d'Usage Typiques**

- ✅ Problèmes de carte bancaire (blocage, perte, vol)
- ✅ Prélèvements non autorisés
- ✅ Frais bancaires contestés
- ✅ Virements retardés ou échoués
- ✅ Accès au compte en ligne
- ✅ Demandes de modification de contrat

#### **Exemples de Requêtes**

```python
# Recherche en français
results = retriever.retrieve(
    query="Ma carte bancaire est bloquée depuis hier",
    filters={"source": "synth", "lang": "fr"},
    top_k=5
)

# Recherche en anglais
results = retriever.retrieve(
    query="unauthorized charge on my account",
    filters={"source": "synth", "lang": "en"},
    top_k=5
)

# Recherche par priorité
results = retriever.retrieve(
    query="urgent problem need help",
    filters={"source": "synth", "priority": "high"},
    top_k=3
)
```

#### **Scores de Similarité Attendus**

| Type de Query | Score Minimum | Score Typique |
|--------------|---------------|---------------|
| Match exact (mots-clés présents) | 0.70 | 0.75-0.85 |
| Match sémantique (synonymes) | 0.60 | 0.65-0.75 |
| Match contextuel | 0.50 | 0.55-0.65 |

---

### 2. Plaintes CFPB (`cfpb`)

#### **Caractéristiques**

- **Volume** : ~2000-3000 chunks (après chunking)
- **Langue** : Anglais (US)
- **Type** : Plaintes de consommateurs américains
- **Source Originale** : [Consumer Financial Protection Bureau](https://www.consumerfinance.gov/data-research/consumer-complaints/)
- **Période** : 2011-2023
- **Domaine** : Produits et services financiers

#### **Métadonnées Disponibles**

| Champ | Type | Description | Exemples de Valeurs |
|-------|------|-------------|---------------------|
| `source` | string | Identifiant de la source | `"cfpb"` |
| `product` | string | Produit financier concerné | "Credit card", "Mortgage", "Debt collection", "Checking or savings account" |
| `issue` | string | Type de problème | "Unauthorized transactions", "Closing an account", "Managing an account" |
| `company` | string | Institution financière | "Bank of America", "Chase", "Wells Fargo" |
| `company_response` | string | Réponse de l'entreprise | "Closed with explanation", "Closed with monetary relief" |
| `date_received` | string | Date de réception | ISO 8601 |
| `state` | string | État US | "CA", "NY", "TX", etc. |
| `zipcode` | string | Code postal (anonymisé) | "XXXXX" |

#### **Produits Financiers Couverts**

| Produit | Pourcentage | Volume Estimé |
|---------|-------------|---------------|
| Credit card or prepaid card | 25% | ~500-750 chunks |
| Checking or savings account | 20% | ~400-600 chunks |
| Mortgage | 15% | ~300-450 chunks |
| Debt collection | 15% | ~300-450 chunks |
| Credit reporting | 10% | ~200-300 chunks |
| Student loan | 8% | ~160-240 chunks |
| Autres | 7% | ~140-210 chunks |

#### **Issues Principales**

- Unauthorized transactions / Fraud
- Incorrect information on credit report
- Problem when making payment
- Struggling to pay mortgage
- Communication tactics (debt collection)
- Closing an account
- Managing overdrafts and fees

#### **Exemples de Contenu**

```
Upon reviewing the transaction history, I discovered XXXX XXXX XXXXXXXX 
unauthorized charges XXXX XXXX, all processed at the same time, from 
the same merchant, and for amounts that together match the balance 
that should have been available. The transactions were made to a 
merchant labeled : XXXX XXXX XXXX. I immediately contacted my bank 
to report these fraudulent charges, but they refused to refund the 
amounts, claiming that the transactions were authorized.
```

**Note :** Les données sensibles (montants, dates précises, noms) sont anonymisées avec `XXXX`.

#### **Exemples de Requêtes**

```python
# Recherche par type de produit
results = retriever.retrieve(
    query="credit card dispute unauthorized charge",
    filters={"source": "cfpb", "product": "Credit card"},
    top_k=5
)

# Recherche par type d'issue
results = retriever.retrieve(
    query="fraud transaction not authorized",
    filters={
        "source": "cfpb", 
        "issue": "Unauthorized transactions"
    },
    top_k=10
)

# Recherche globale CFPB
results = retriever.retrieve(
    query="bank closed my account without notice",
    filters={"source": "cfpb"},
    top_k=5,
    score_threshold=0.65
)

# Recherche multi-critères
results = retriever.retrieve(
    query="mortgage foreclosure payment problem",
    filters={
        "source": "cfpb",
        "product": "Mortgage"
    },
    top_k=8
)
```

#### **Scores de Similarité Attendus**

| Type de Query | Score Minimum | Score Typique |
|--------------|---------------|---------------|
| Termes juridiques/techniques | 0.65 | 0.70-0.80 |
| Descriptions de problèmes | 0.60 | 0.65-0.75 |
| Queries génériques | 0.50 | 0.55-0.65 |

---

### 3. Emails Enron (`enron`)

#### **Caractéristiques**

- **Volume** : ~500-1500 chunks (après chunking)
- **Langue** : Anglais (Corporate US)
- **Type** : Emails internes d'entreprise
- **Source Originale** : [CMU Enron Email Dataset](https://www.cs.cmu.edu/~enron/)
- **Période** : 1999-2002
- **Domaine** : Énergie, trading, communication d'entreprise
- **Format** : Emails bruts (.eml) parsés

#### **Métadonnées Disponibles**

| Champ | Type | Description | Exemples |
|-------|------|-------------|----------|
| `source` | string | Identifiant de la source | `"enron"` |
| `from` | string | Expéditeur (anonymisé) | "phillip.allen@enron.com" |
| `to` | string | Destinataire(s) | "john.smith@enron.com" |
| `subject` | string | Sujet de l'email | "Re: Meeting Schedule", "Gas Trading Position" |
| `date` | string | Date d'envoi | ISO 8601 |
| `folder` | string | Dossier d'origine | "sent_mail", "inbox", "deleted_items" |

#### **Catégories d'Emails**

| Catégorie | Pourcentage | Description |
|-----------|-------------|-------------|
| Business meetings | 30% | Coordination, planification, agendas |
| Energy trading | 25% | Positions, marchés, transactions |
| Internal communication | 20% | Annonces, updates, politiques |
| Contracts & Legal | 15% | Contrats, approbations, conformité |
| HR & Administration | 10% | RH, voyages, dépenses |

#### **Thématiques Principales**

- ✅ Coordination de réunions et calendriers
- ✅ Trading d'énergie (gaz naturel, électricité)
- ✅ Négociation de contrats
- ✅ Crise énergétique californienne (2000-2001)
- ✅ Gestion de projets
- ✅ Communication interdépartementale

#### **Exemples de Contenu**

```
Subject: Re: Gas Trading Vision Meeting - Reschedule

Status update:
Fletcher J Sturm -> No Response
Scott Neal -> No Response
Hunter S Shively -> No Response
Phillip K Allen -> No Response
Allan Severude -> Accepted
Scott Mills -> Accepted
Russ Severson -> No Response

---------------------- Forwarded by Phillip K Allen/HOU/ECT 
on 09/26/2000 02:00 PM ---------------------------

Reschedule
Chairperson: Richard Burchfield
Sent by: Cindy Cicchetti

Start: 09/27/2000 02:00 PM
End: 09/27/2000 03:00 PM

Description: Gas Trading Vision Meeting - Room EB2601
```

#### **Exemples de Requêtes**

```python
# Recherche de meetings
results = retriever.retrieve(
    query="schedule meeting next week conference room",
    filters={"source": "enron"},
    top_k=5
)

# Recherche sur le trading
results = retriever.retrieve(
    query="natural gas trading positions market analysis",
    filters={"source": "enron"},
    top_k=10
)

# Recherche de contrats
results = retriever.retrieve(
    query="contract approval legal review signature",
    filters={"source": "enron"},
    top_k=5
)

# Recherche par expéditeur (si metadata disponible)
results = retriever.retrieve(
    query="project update status report",
    filters={"source": "enron", "from": "phillip.allen@enron.com"},
    top_k=8
)
```

#### **Scores de Similarité Attendus**

| Type de Query | Score Minimum | Score Typique |
|--------------|---------------|---------------|
| Termes business spécifiques | 0.65 | 0.70-0.80 |
| Coordination/meetings | 0.60 | 0.65-0.75 |
| Queries génériques | 0.50 | 0.55-0.65 |

---

## 🔑 Métadonnées Communes

Tous les documents partagent ces métadonnées de base :

| Champ | Type | Description |
|-------|------|-------------|
| `source` | string | Origine du document (`"synth"`, `"cfpb"`, `"enron"`) |
| `page_content` | string | Contenu textuel du chunk |
| `id` | string | UUID unique du document |

---

## 🎯 Stratégies de Filtrage

### Filtrage par Source

```python
# Données synthétiques uniquement
filters = {"source": "synth"}

# Plaintes CFPB uniquement
filters = {"source": "cfpb"}

# Emails Enron uniquement
filters = {"source": "enron"}
```

### Filtrage par Langue (Synth)

```python
# Français uniquement
filters = {"source": "synth", "lang": "fr"}

# Anglais uniquement
filters = {"source": "synth", "lang": "en"}
```

### Filtrage par Produit (CFPB)

```python
# Cartes de crédit
filters = {"source": "cfpb", "product": "Credit card"}

# Hypothèques
filters = {"source": "cfpb", "product": "Mortgage"}

# Comptes bancaires
filters = {"source": "cfpb", "product": "Checking or savings account"}
```

### Filtrage par Priorité (Synth)

```python
# Urgences uniquement
filters = {"source": "synth", "priority": "high"}

# Priorité normale
filters = {"source": "synth", "priority": "medium"}
```

### Filtrage Multi-Critères

```python
# Tickets français urgents
filters = {
    "source": "synth",
    "lang": "fr",
    "priority": "high"
}

# Fraudes sur cartes de crédit
filters = {
    "source": "cfpb",
    "product": "Credit card",
    "issue": "Unauthorized transactions"
}
```

---

## 💡 Exemples de Requêtes Avancées

### 1. Recherche Multilingue

```python
# Query en français cherchant dans toutes les sources
results = retriever.retrieve(
    query="problème de carte bancaire bloquée",
    top_k=10
)
# Retournera prioritairement des docs synth FR, 
# mais peut aussi retourner CFPB si sémantiquement proche
```

### 2. Recherche avec Seuil de Pertinence

```python
# Seulement les résultats très pertinents
results = retriever.retrieve(
    query="mortgage foreclosure prevention options",
    filters={"source": "cfpb"},
    score_threshold=0.75,  # Seuil élevé
    top_k=5
)
```

### 3. Recherche Comparative entre Sources

```python
query = "unauthorized payment transaction"

# Comparer les résultats par source
synth_results = retriever.retrieve(query, filters={"source": "synth"}, top_k=3)
cfpb_results = retriever.retrieve(query, filters={"source": "cfpb"}, top_k=3)

# Analyser les différences de scores et contenus
```

### 4. Recherche par Contexte Temporel

```python
# Récent uniquement (si date disponible)
from datetime import datetime, timedelta

recent_date = (datetime.now() - timedelta(days=90)).isoformat()

results = retriever.retrieve(
    query="account closure issue",
    filters={"source": "cfpb", "date_received": {"$gte": recent_date}},
    top_k=10
)
```

### 5. Recherche Exhaustive sans Filtre

```python
# Chercher dans toutes les sources
results = retriever.retrieve(
    query="payment dispute resolution process",
    top_k=20,  # Plus de résultats
    score_threshold=0.5  # Seuil plus permissif
)

# Analyser la distribution des sources
sources_count = {}
for r in results:
    src = r['metadata']['source']
    sources_count[src] = sources_count.get(src, 0) + 1

print("Distribution:", sources_count)
# Exemple: {'cfpb': 12, 'synth': 5, 'enron': 3}
```

---

## 📈 Statistiques et Performance

### Volume de Données

| Métrique | Collection `demo_public` | Collection `knowledge_base_main` |
|----------|-------------------------|----------------------------------|
| **Total chunks** | ~100-150 | ~3000-5000 |
| **Sources** | 1 (synth) | 3 (synth + cfpb + enron) |
| **Taille moyenne chunk** | 400-600 chars | 400-600 chars |
| **Overlap** | 100 chars | 100 chars |

### Performance des Requêtes

| Opération | Temps Moyen | Temps Maximum |
|-----------|-------------|---------------|
| Recherche simple (top-5) | 0.3-0.8s | 1.5s |
| Recherche avec filtres | 0.4-1.0s | 2.0s |
| Recherche large (top-20) | 0.5-1.2s | 2.5s |
| Count documents | 0.1-0.3s | 0.5s |

### Scores de Similarité Observés

| Plage de Score | Interprétation | Recommandation |
|---------------|----------------|----------------|
| 0.80 - 1.00 | Excellent match | Utiliser directement |
| 0.70 - 0.79 | Très pertinent | Confiance élevée |
| 0.60 - 0.69 | Pertinent | Valider avec LLM |
| 0.50 - 0.59 | Moyennement pertinent | Reformuler query |
| < 0.50 | Peu pertinent | Élargir recherche |

---

## ✅ Best Practices

### 1. Choix du Top-K

```python
# Pour réponses précises
top_k = 3-5

# Pour analyse large
top_k = 10-20

# Pour benchmarking
top_k = 50-100
```

### 2. Utilisation du Score Threshold

```python
# Production (haute précision)
score_threshold = 0.70

# Développement (exploration)
score_threshold = 0.50

# Recherche exhaustive
score_threshold = None  # Pas de seuil
```

### 3. Filtrage Intelligent

```python
# Étape 1: Déterminer la langue de la query
if is_french(query):
    filters = {"source": "synth", "lang": "fr"}
else:
    filters = None  # Chercher partout

# Étape 2: Si query contient des termes juridiques/financiers
if contains_financial_terms(query):
    filters = {"source": "cfpb"}

# Étape 3: Si query mentionne "meeting", "schedule", "email"
if is_business_communication(query):
    filters = {"source": "enron"}
```

### 4. Gestion des Résultats Vides

```python
results = retriever.retrieve(query, filters={"source": "cfpb"}, top_k=5)

if not results:
    # Stratégie 1: Élargir la recherche
    results = retriever.retrieve(query, top_k=5)  # Sans filtre
    
if not results or max([r['score'] for r in results]) < 0.5:
    # Stratégie 2: Reformuler la query
    query_reformulated = reformulate_with_llm(query)
    results = retriever.retrieve(query_reformulated, top_k=5)
```

### 5. Logging et Monitoring

```python
import logging

logger = logging.getLogger(__name__)

results = retriever.retrieve(query, filters, top_k)

# Log des métriques
logger.info(f"Query: {query}")
logger.info(f"Results count: {len(results)}")
logger.info(f"Top score: {results[0]['score'] if results else 0}")
logger.info(f"Sources: {set(r['metadata']['source'] for r in results)}")
```

### 6. Caching pour Performance

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_retrieve(query: str, source: str, top_k: int) -> tuple:
    results = retriever.retrieve(
        query=query,
        filters={"source": source} if source else None,
        top_k=top_k
    )
    return tuple(results)  # Tuple pour hashability
```

---

## 🔧 Maintenance et Mises à Jour

### Ajout de Nouvelles Sources

Pour ajouter une nouvelle source de données :

1. Créer un script d'ingestion dans `scripts/ingest/ingest_<source>.py`
2. Définir la valeur de `source` dans les métadonnées
3. Chunker les documents (600 chars, 100 overlap)
4. Générer les embeddings avec `all-mpnet-base-v2`
5. Insérer dans Qdrant par lots de 100 points
6. Créer un snapshot
7. Uploader vers le cloud
8. Mettre à jour cette documentation

### Vérification de l'Intégrité

```python
# Script de vérification
def check_data_integrity():
    total = retriever.count_documents()
    print(f"Total documents: {total}")
    
    for source in ["synth", "cfpb", "enron"]:
        count = len(retriever.retrieve(
            query="test", 
            filters={"source": source}, 
            top_k=10000
        ))
        print(f"Source {source}: {count} documents")
```

---

## 📞 Support et Contact

Pour toute question ou problème concernant les sources de données :

- **Documentation complète** : [`README.md`](../README.md)
- **Guide de migration** : [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md)
- **Repository** : [GitHub - genai-workflow-automate](https://github.com/gzz2v6tnxp-ctrl/genai-workflow-automate)

---

**Dernière mise à jour** : 7 novembre 2025  
**Version** : 1.0.0  
**Auteur** : Équipe GenAI Workflow Automation