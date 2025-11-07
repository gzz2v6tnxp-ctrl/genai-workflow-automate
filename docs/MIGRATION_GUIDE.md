# 📚 Guide de Migration : Qdrant Local → Cloud

Ce guide vous aide à migrer vos collections Qdrant depuis une instance locale vers Qdrant Cloud en utilisant des snapshots.

## 🔧 Prérequis

### 1. Configuration requise

Ajoutez ces variables dans votre fichier `.env` :

```env
# Configuration Qdrant Local
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Configuration Qdrant Cloud (obtenez ces valeurs depuis votre dashboard)
QDRANT_CLOUD_URL=https://your-cluster.aws.cloud.qdrant.io
QDRANT_API_KEY=your-api-key-here

# Configuration des embeddings
VECTOR_DIMENSION=768
DEFAULT_EMBEDDING_MODEL=all-mpnet-base-v2
```

### 2. Dépendances

Installez les packages requis :

```bash
pip install requests qdrant-client>=1.14.2
```

## 🚀 Processus de Migration

### Méthode 1 : Migration Automatique (Recommandée)

Utilisez le script tout-en-un qui gère automatiquement la création et l'upload des snapshots :

```bash
python scripts/vector_store/migrate_to_cloud.py
```

Ce script va :
1. ✅ Vérifier la configuration
2. ✅ Créer des snapshots des collections locales
3. ✅ Télécharger les snapshots dans `./snapshots/`
4. ✅ Uploader vers Qdrant Cloud avec `priority=snapshot`
5. ✅ Vérifier que les données sont bien présentes dans le cloud

### Méthode 2 : Migration Manuelle (Étape par étape)

#### Étape 1 : Créer les snapshots locaux

```bash
python scripts/vector_store/create_snapshot.py
```

Résultat : Les fichiers `.snapshot` seront créés dans `./snapshots/`

#### Étape 2 : Uploader vers le cloud

```bash
python scripts/vector_store/restore_snapshot.py
```

## 📊 Collections Migrées

Deux collections seront migrées :

| Collection | Contenu | Usage |
|-----------|---------|-------|
| `demo_public` | Données synthétiques uniquement | Demo publique |
| `knowledge_base_main` | Toutes les données (synth + CFPB + Enron) | Production |

## 🔍 Vérification Post-Migration

### Via Python

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://your-cluster.aws.cloud.qdrant.io",
    api_key="your-api-key"
)

# Vérifier le nombre de points
print(client.count("demo_public"))
print(client.count("knowledge_base_main"))

# Tester une recherche
results = client.search(
    collection_name="knowledge_base_main",
    query_vector=[0.1] * 768,  # Vecteur de test
    limit=5
)
print(results)
```

### Via l'API REST

```bash
# Compter les points
curl -X POST "https://your-cluster.aws.cloud.qdrant.io/collections/demo_public/points/count" \
  -H "api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"exact": true}'
```

## ⚙️ Configuration Avancée

### Paramètre `priority=snapshot`

Le paramètre `priority=snapshot` est **crucial** lors de la restauration. Il garantit que :
- ✅ Les données du snapshot ont la priorité sur les données existantes
- ✅ La collection est recréée avec les bonnes métadonnées
- ✅ Les index sont correctement reconstruits

Référence : [Documentation Qdrant - Snapshot Priority](https://qdrant.tech/documentation/concepts/snapshots/#snapshot-priority)

### Gestion des gros fichiers

Pour les collections volumineuses (> 100 MB) :

1. **Augmenter le timeout** :
```python
# Dans migrate_to_cloud.py, ligne ~120
timeout=600  # 10 minutes au lieu de 5
```

2. **Upload en arrière-plan** :
```python
# Lors de la création du snapshot
snapshot_info = client.create_snapshot(
    collection_name=collection_name,
    wait=False  # Ne pas attendre la fin
)
```

3. **Surveiller l'état** :
```python
# Liste tous les snapshots
snapshots = client.list_snapshots(collection_name)
print(snapshots)
```

## 🐛 Dépannage

### Erreur : "Payload too large"

**Problème** : Le snapshot est trop volumineux (> 32 MB).

**Solutions** :
1. Augmenter le timeout
2. Utiliser `wait=False` pour l'upload en arrière-plan
3. Diviser la collection en plusieurs snapshots plus petits

### Erreur : "Connection timeout"

**Problème** : La connexion au cloud est lente.

**Solutions** :
1. Vérifier votre connexion Internet
2. Augmenter le paramètre `timeout`
3. Réessayer pendant les heures creuses

### Erreur : "Collection already exists"

**Problème** : Une collection existe déjà sur le cloud.

**Solutions** :
1. Supprimer la collection existante :
```python
client.delete_collection("demo_public")
```

2. Ou modifier le nom de la collection dans le script

### Erreur : "Invalid API key"

**Problème** : La clé API est incorrecte ou expirée.

**Solutions** :
1. Vérifier la clé dans le dashboard Qdrant Cloud
2. Régénérer une nouvelle clé si nécessaire
3. Mettre à jour le fichier `.env`

## 📁 Structure des Snapshots

```
snapshots/
├── demo_public-559032209313046-2024-01-03-13-20-11.snapshot
└── knowledge_base_main-559032209313047-2024-01-03-13-20-12.snapshot
```

Format du nom : `{collection_name}-{timestamp}-{date}.snapshot`

## 🔒 Sécurité

### Protection de la clé API

1. **Jamais commiter la clé** :
```bash
# Vérifier que .env est dans .gitignore
echo ".env" >> .gitignore
```

2. **Utiliser des variables d'environnement** :
```bash
export QDRANT_API_KEY="your-key"
```

3. **Rotation régulière** :
- Régénérer la clé tous les 3-6 mois
- Utiliser des clés différentes pour dev/prod

## 📚 Références

- [Documentation Qdrant - Snapshots](https://qdrant.tech/documentation/concepts/snapshots/)
- [Tutorial Qdrant - Backup & Restore](https://qdrant.tech/documentation/database-tutorials/create-snapshot/)
- [Qdrant Cloud Dashboard](https://cloud.qdrant.io/)
- [Qdrant Migration Tool](https://github.com/qdrant/migration)

## 🆘 Support

En cas de problème :
1. Consulter les logs détaillés
2. Vérifier la documentation Qdrant
3. Contacter le support Qdrant Cloud

## ✅ Checklist de Migration

- [ ] Configuration `.env` complète
- [ ] Collections locales peuplées et vérifiées
- [ ] Dépendances installées (`requests`, `qdrant-client`)
- [ ] Espace disque suffisant pour les snapshots
- [ ] Compte Qdrant Cloud créé et cluster déployé
- [ ] Clé API obtenue et testée
- [ ] Exécution du script de migration
- [ ] Vérification du nombre de points dans le cloud
- [ ] Test d'une recherche sur le cloud
- [ ] Mise à jour des endpoints de production
- [ ] Suppression des snapshots locaux (optionnel)
