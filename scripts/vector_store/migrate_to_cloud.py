"""
Script de migration complète : Local → Qdrant Cloud
Basé sur les recommandations officielles Qdrant :
https://qdrant.tech/documentation/database-tutorials/create-snapshot/
"""

import sys
from pathlib import Path
from qdrant_client import QdrantClient
import requests

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config


def create_snapshot(collection_name: str, output_dir: str = "./snapshots") -> str:
    """
    Crée un snapshot de la collection locale et le télécharge.
    
    Returns:
        str: Chemin du fichier snapshot téléchargé
    """
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"\n📸 Création du snapshot pour '{collection_name}'...")
    
    # Vérifier la collection
    try:
        count_result = client.count(collection_name=collection_name, exact=True)
        print(f"   📊 Collection contient {count_result.count} points")
        
        if count_result.count == 0:
            print(f"⚠️  ATTENTION : Collection vide !")
            return None
    except Exception as e:
        print(f"❌ Collection inaccessible : {e}")
        return None
    
    # Créer le snapshot
    try:
        snapshot_info = client.create_snapshot(
            collection_name=collection_name,
            wait=True  # Attendre la fin de la création
        )
        print(f"✅ Snapshot créé : {snapshot_info.name}")
    except Exception as e:
        print(f"❌ Erreur création snapshot : {e}")
        return None
    
    # Télécharger le snapshot via HTTP API
    try:
        snapshot_url = f"http://{config.QDRANT_HOST}:{config.QDRANT_PORT}/collections/{collection_name}/snapshots/{snapshot_info.name}"
        local_path = Path(output_dir) / f"{collection_name}-{snapshot_info.name}"
        
        response = requests.get(snapshot_url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        size_mb = local_path.stat().st_size / 1024 / 1024
        print(f"📦 Snapshot téléchargé : {local_path.name}")
        print(f"   Taille : {size_mb:.2f} MB")
        return str(local_path)
        
    except Exception as e:
        print(f"❌ Erreur téléchargement : {e}")
        return None


def upload_snapshot_to_cloud(collection_name: str, snapshot_path: str) -> bool:
    """
    Upload un snapshot vers Qdrant Cloud avec priority=snapshot.
    Méthode recommandée par la documentation officielle.
    
    Args:
        collection_name: Nom de la collection à créer/restaurer
        snapshot_path: Chemin local du fichier snapshot
        
    Returns:
        bool: True si succès
    """
    if not Path(snapshot_path).exists():
        print(f"❌ Fichier inexistant : {snapshot_path}")
        return False
    
    # Vérifier la configuration cloud
    if not config.QDRANT_CLOUD_URL or not config.QDRANT_API_KEY:
        print("❌ Configuration cloud manquante (QDRANT_CLOUD_URL / QDRANT_API_KEY)")
        return False
    
    print(f"\n📤 Upload vers le cloud : {collection_name}")
    size_mb = Path(snapshot_path).stat().st_size / 1024 / 1024
    print(f"   Fichier : {Path(snapshot_path).name} ({size_mb:.2f} MB)")
    
    try:
        # URL de l'API Cloud avec priority=snapshot (recommandation officielle)
        upload_url = f"{config.QDRANT_CLOUD_URL}/collections/{collection_name}/snapshots/upload?priority=snapshot"
        
        # Upload du fichier
        with open(snapshot_path, 'rb') as f:
            response = requests.post(
                upload_url,
                headers={"api-key": config.QDRANT_API_KEY},
                files={"snapshot": (Path(snapshot_path).name, f)},
                timeout=600  # 10 minutes pour les gros fichiers
            )
        
        response.raise_for_status()
        print(f"✅ Upload réussi")
        
        # Vérification
        cloud_client = QdrantClient(
            url=config.QDRANT_CLOUD_URL,
            api_key=config.QDRANT_API_KEY,
        )
        count_result = cloud_client.count(collection_name=collection_name, exact=True)
        print(f"   📊 Points dans le cloud : {count_result.count}")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout : Le fichier est volumineux")
        print(f"   💡 L'upload peut continuer en arrière-plan")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP : {e}")
        if hasattr(e.response, 'text'):
            print(f"   Détails : {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False


def migrate_collection(collection_name: str) -> bool:
    """
    Migration complète d'une collection : Local → Cloud
    
    Args:
        collection_name: Nom de la collection à migrer
        
    Returns:
        bool: True si succès
    """
    print("\n" + "=" * 70)
    print(f"🔄 MIGRATION : {collection_name}")
    print("=" * 70)
    
    # Étape 1 : Créer snapshot local
    snapshot_path = create_snapshot(collection_name)
    if not snapshot_path:
        print(f"❌ Échec création snapshot")
        return False
    
    # Étape 2 : Upload vers le cloud
    if upload_snapshot_to_cloud(collection_name, snapshot_path):
        print(f"✅ Migration réussie pour '{collection_name}'")
        return True
    else:
        print(f"❌ Échec upload pour '{collection_name}'")
        return False


def main():
    """
    Script principal de migration
    """
    print("=" * 70)
    print("☁️  MIGRATION QDRANT : LOCAL → CLOUD")
    print("=" * 70)
    
    # Vérifier la configuration
    print(f"\n🔧 Configuration :")
    print(f"   Local  : {config.QDRANT_HOST}:{config.QDRANT_PORT}")
    print(f"   Cloud  : {config.QDRANT_CLOUD_URL or '❌ Non configuré'}")
    
    if not config.QDRANT_CLOUD_URL or not config.QDRANT_API_KEY:
        print("\n❌ Configuration cloud manquante !")
        print("\n📝 Ajoutez dans votre fichier .env :")
        print("   QDRANT_CLOUD_URL=https://your-cluster.aws.cloud.qdrant.io")
        print("   QDRANT_API_KEY=your-api-key")
        sys.exit(1)
    
    # Collections à migrer
    collections = ["demo_public", "knowledge_base_main"]
    
    print(f"\n📦 Collections à migrer : {', '.join(collections)}")
    print("\n⚠️  Cette opération va :")
    print("   1. Créer des snapshots des collections locales")
    print("   2. Les télécharger dans ./snapshots/")
    print("   3. Les uploader vers Qdrant Cloud")
    print("   4. Recréer les collections sur le cloud")
    
    response = input("\n🚀 Continuer ? (y/N): ")
    if response.lower() != 'y':
        print("\n❌ Migration annulée")
        sys.exit(0)
    
    # Migration
    print("\n🔄 Démarrage de la migration...")
    success_count = 0
    
    for collection in collections:
        if migrate_collection(collection):
            success_count += 1
    
    # Résumé
    print("\n" + "=" * 70)
    if success_count == len(collections):
        print("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
        print(f"   {success_count}/{len(collections)} collections migrées")
    else:
        print(f"⚠️  MIGRATION PARTIELLE")
        print(f"   {success_count}/{len(collections)} collections migrées")
    print("=" * 70)
    
    # Cleanup
    print("\n🧹 Nettoyage :")
    print("   Les snapshots sont conservés dans ./snapshots/")
    print("   Vous pouvez les supprimer manuellement si nécessaire")


if __name__ == "__main__":
    main()
