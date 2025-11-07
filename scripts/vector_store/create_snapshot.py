import sys
from pathlib import Path
from qdrant_client import QdrantClient

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config

def create_and_download_snapshot(collection_name: str, output_dir: str = "./snapshots"):
    """
    Crée un snapshot d'une collection Qdrant locale et le télécharge.
    À EXÉCUTER APRÈS avoir peuplé vos collections.
    """
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    
    # Créer le dossier de sortie s'il n'existe pas
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"\n📸 Création du snapshot pour '{collection_name}'...")
    
    # 1. Vérifier que la collection existe et contient des données
    try:
        count_result = client.count(collection_name=collection_name, exact=True)
        print(f"   Collection contient {count_result.count} points")
        
        if count_result.count == 0:
            print(f"⚠️  ATTENTION : La collection '{collection_name}' est VIDE !")
            response = input("   Voulez-vous continuer quand même ? (y/N): ")
            if response.lower() != 'y':
                print("   Snapshot annulé.")
                return None
    except Exception as e:
        print(f"❌ Erreur : La collection '{collection_name}' n'existe pas ou est inaccessible")
        print(f"   Détails : {e}")
        return None
    
    # 2. Créer le snapshot
    try:
        snapshot_info = client.create_snapshot(collection_name=collection_name)
        snapshot_name = snapshot_info.name
        print(f"✅ Snapshot créé : {snapshot_name}")
    except Exception as e:
        print(f"❌ Erreur lors de la création du snapshot : {e}")
        return None
    
    # 3. Télécharger le snapshot
    try:
        snapshot_path = client.download_snapshot(
            collection_name=collection_name,
            snapshot_name=snapshot_name,
            output_path=f"{output_dir}/{collection_name}-{snapshot_name}"
        )
        print(f"📦 Snapshot téléchargé : {snapshot_path}")
        print(f"   Taille : {Path(snapshot_path).stat().st_size / 1024 / 1024:.2f} MB")
        return snapshot_path
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement : {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 CRÉATION DE SNAPSHOTS QDRANT")
    print("=" * 60)
    print("\n⚠️  IMPORTANT : Ce script doit être exécuté APRÈS avoir peuplé vos collections !")
    print("   Utilisez d'abord : python scripts/vector_store/populate_collection.py\n")
    
    response = input("Avez-vous déjà peuplé vos collections ? (y/N): ")
    if response.lower() != 'y':
        print("\n❌ Veuillez d'abord peupler vos collections.")
        print("   1. python scripts/vector_store/build_collection.py")
        print("   2. python scripts/vector_store/populate_collection.py")
        print("   3. Puis relancez ce script")
        sys.exit(0)
    
    print("\n📸 Création des snapshots...")
    
    # Créer les snapshots pour les deux collections
    snapshot1 = create_and_download_snapshot("demo_public")
    snapshot2 = create_and_download_snapshot("knowledge_base_main")
    
    if snapshot1 and snapshot2:
        print("\n" + "=" * 60)
        print("✅ SNAPSHOTS CRÉÉS AVEC SUCCÈS")
        print("=" * 60)
        print(f"\n📁 Fichiers créés dans le dossier './snapshots/'")
        print(f"\n🚀 Prochaine étape : Restaurer sur Qdrant Cloud")
        print(f"   python scripts/vector_store/restore_snapshot.py")
    else:
        print("\n❌ Échec de la création des snapshots")
