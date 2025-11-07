import sys
from pathlib import Path
from qdrant_client import QdrantClient
import requests

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config

def restore_snapshot_to_cloud(collection_name: str, snapshot_path: str):
    """
    Restaure un snapshot local vers Qdrant Cloud.
    """
    # Vérifier que le fichier existe
    if not Path(snapshot_path).exists():
        print(f"❌ Erreur : Le fichier '{snapshot_path}' n'existe pas")
        return False
    
    print(f"\n📤 Restauration de '{collection_name}' sur le cloud...")
    print(f"   Fichier : {snapshot_path}")
    print(f"   Taille : {Path(snapshot_path).stat().st_size / 1024 / 1024:.2f} MB")
    
    # Vérifier la configuration cloud
    cloud_url = getattr(config, 'QDRANT_CLOUD_URL', None)
    api_key = getattr(config, 'QDRANT_API_KEY', None)
    
    if not cloud_url or not api_key:
        print(f"❌ Configuration cloud manquante dans config.py")
        print("\n💡 Ajoutez ces variables dans votre fichier .env :")
        print("   QDRANT_CLOUD_URL=https://your-cluster-id.aws.cloud.qdrant.io")
        print("   QDRANT_API_KEY=your-api-key-here")
        return False
    
    # Connexion au cluster cloud
    try:
        cloud_client = QdrantClient(
            url=cloud_url,
            api_key=api_key,
        )
        print(f"✅ Connecté à {cloud_url}")
    except Exception as e:
        print(f"❌ Erreur de connexion au cloud : {e}")
        return False
    
    # Upload et restauration via HTTP API (recommandé par la documentation)
    try:
        snapshot_name = Path(snapshot_path).name
        
        # Méthode HTTP avec priority=snapshot (recommandation officielle)
        upload_url = f"{cloud_url}/collections/{collection_name}/snapshots/upload?priority=snapshot"
        
        print(f"   📤 Upload en cours...")
        
        with open(snapshot_path, 'rb') as f:
            response = requests.post(
                upload_url,
                headers={
                    "api-key": api_key,
                },
                files={"snapshot": (snapshot_name, f)},
                timeout=300  # 5 minutes timeout pour les gros fichiers
            )
        
        response.raise_for_status()
        print(f"✅ Collection '{collection_name}' restaurée sur le cloud")
        
        # Vérifier le nombre de points
        count_result = cloud_client.count(collection_name=collection_name, exact=True)
        print(f"   📊 Nombre de points dans le cloud : {count_result.count}")
        return True
        
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout : Le fichier est trop volumineux ou la connexion trop lente")
        print(f"   💡 Astuce : Le snapshot peut continuer à s'uploader en arrière-plan")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la restauration : {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("☁️  RESTAURATION DES SNAPSHOTS SUR QDRANT CLOUD")
    print("=" * 60)
    
    # Vérifier la configuration
    cloud_url = getattr(config, 'QDRANT_CLOUD_URL', None)
    api_key = getattr(config, 'QDRANT_API_KEY', None)
    
    if not cloud_url or not api_key:
        print("\n❌ Configuration cloud manquante !")
        print("\n📝 Ajoutez ces variables dans votre fichier .env :")
        print("   QDRANT_CLOUD_URL=https://your-cluster-id.aws.cloud.qdrant.io")
        print("   QDRANT_API_KEY=your-api-key-here")
        sys.exit(1)
    
    print(f"\n🌐 Cluster cible : {cloud_url}")
    print("\n📦 Recherche des snapshots...")
    
    # Liste les fichiers disponibles
    snapshot_dir = Path("./snapshots")
    if snapshot_dir.exists():
        available_snapshots = list(snapshot_dir.glob("*.snapshot"))
        if available_snapshots:
            print("\n📁 Fichiers snapshot trouvés :")
            for i, snap in enumerate(available_snapshots, 1):
                print(f"   {i}. {snap.name} ({snap.stat().st_size / 1024 / 1024:.2f} MB)")
        else:
            print("\n⚠️  Aucun snapshot trouvé dans './snapshots/'")
            print("   Exécutez d'abord : python scripts/vector_store/create_snapshot.py")
            sys.exit(1)
    else:
        print("\n❌ Le dossier './snapshots/' n'existe pas")
        print("   Exécutez d'abord : python scripts/vector_store/create_snapshot.py")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    response = input("\n🚀 Lancer la restauration ? (y/N): ")
    
    if response.lower() == 'y':
        print("\n📤 Restauration en cours...\n")
        
        success_count = 0
        # Restaurer chaque collection
        for snapshot_path in available_snapshots:
            # Extraire le nom de la collection du nom du fichier
            collection_name = snapshot_path.name.split('-')[0]
            if restore_snapshot_to_cloud(collection_name, str(snapshot_path)):
                success_count += 1
        
        print("\n" + "=" * 60)
        if success_count == len(available_snapshots):
            print("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
        else:
            print(f"⚠️  MIGRATION PARTIELLE : {success_count}/{len(available_snapshots)} collections restaurées")
        print("=" * 60)
    else:
        print("\n❌ Restauration annulée")
