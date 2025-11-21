import sys
from pathlib import Path
import requests
from qdrant_client import QdrantClient

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config


def create_snapshot(collection_name: str, output_dir: str = "./snapshots") -> str:
    """Crée un snapshot de la collection locale et le télécharge."""
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📸 Création du snapshot pour '{collection_name}'...")

    # Vérifier nombre de points
    try:
        count = client.count(collection_name=collection_name, exact=True).count
        print(f"   📊 Collection contient {count} points")
    except Exception as e:
        print(f"   ⚠️  Impossible de compter les points : {e}")

    # Créer le snapshot
    try:
        snapshot_info = client.create_snapshot(collection_name=collection_name, wait=True)
        snap_name = getattr(snapshot_info, "name", None) or snapshot_info.get("name")
        print(f"✅ Snapshot créé : {snap_name}")
    except Exception as e:
        print(f"❌ Erreur création snapshot : {e}")
        return ""

    # Télécharger via HTTP
    try:
        download_url = f"http://{config.QDRANT_HOST}:{config.QDRANT_PORT}/collections/{collection_name}/snapshots/{snap_name}"
        local_path = out_dir / f"{collection_name}-{snap_name}"

        resp = requests.get(download_url, stream=True)
        resp.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        size_mb = local_path.stat().st_size / 1024 / 1024
        print(f"📦 Snapshot téléchargé : {local_path.name}")
        print(f"   Taille : {size_mb:.2f} MB")
        return str(local_path)
    except Exception as e:
        print(f"❌ Erreur téléchargement : {e}")
        return ""


def delete_cloud_collection_if_exists(collection_name: str):
    """Supprime la collection cloud si elle existe (pour éviter conflit de dimensions)."""
    cloud_client = QdrantClient(url=config.QDRANT_CLOUD_URL, api_key=config.QDRANT_API_KEY)
    
    try:
        if cloud_client.collection_exists(collection_name):
            print(f"🗑️  Suppression de la collection cloud existante '{collection_name}'...")
            cloud_client.delete_collection(collection_name=collection_name)
            print(f"   ✅ Collection '{collection_name}' supprimée du cloud")
        else:
            print(f"   ℹ️  Collection '{collection_name}' n'existe pas encore sur le cloud")
    except Exception as e:
        print(f"   ⚠️  Erreur lors de la vérification/suppression : {e}")


def upload_snapshot_to_cloud(collection_name: str, snapshot_path: str) -> bool:
    """Upload un fichier snapshot vers Qdrant Cloud."""
    if not Path(snapshot_path).exists():
        print(f"❌ Fichier snapshot introuvable : {snapshot_path}")
        return False

    upload_url = (
        f"{config.QDRANT_CLOUD_URL}/collections/{collection_name}/snapshots/upload"
        "?priority=snapshot"
    )

    size_mb = Path(snapshot_path).stat().st_size / 1024 / 1024
    print(f"\n📤 Upload vers le cloud : {collection_name}")
    print(f"   Fichier : {Path(snapshot_path).name} ({size_mb:.2f} MB)")

    try:
        with open(snapshot_path, "rb") as f:
            resp = requests.post(
                upload_url,
                headers={"api-key": config.QDRANT_API_KEY},
                files={"snapshot": f},
                timeout=600,
            )
            resp.raise_for_status()
            print(f"✅ Upload réussi pour '{collection_name}'")
            return True
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP : {e}")
        try:
            print(f"   Détails : {e.response.text}")
        except:
            pass
        return False
    except Exception as e:
        print(f"❌ Erreur upload : {e}")
        return False


def migrate_collection(collection_name: str):
    """Pipeline complet : snapshot local → suppression cloud → upload."""
    print("\n" + "=" * 70)
    print(f"🔄 MIGRATION : {collection_name}")
    print("=" * 70)

    # 1. Créer et télécharger le snapshot local
    snapshot_path = create_snapshot(collection_name)
    if not snapshot_path:
        print(f"❌ Échec création snapshot pour '{collection_name}'")
        return False

    # 2. Supprimer la collection cloud si elle existe (évite conflit de dimensions)
    delete_cloud_collection_if_exists(collection_name)

    # 3. Upload le snapshot vers le cloud
    success = upload_snapshot_to_cloud(collection_name, snapshot_path)
    
    if success:
        print(f"✅ Migration complète pour '{collection_name}'")
    else:
        print(f"❌ Échec upload pour '{collection_name}'")
    
    return success


def main():
    """Migre les deux collections vers Qdrant Cloud."""
    print("\n" + "=" * 70)
    print("� DÉBUT DE LA MIGRATION VERS QDRANT CLOUD")
    print("=" * 70)

    collections = ["demo_public", "knowledge_base_main"]
    results = {}

    for collection in collections:
        results[collection] = migrate_collection(collection)

    # Résumé final
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DE LA MIGRATION")
    print("=" * 70)
    for collection, success in results.items():
        status = "✅ Succès" if success else "❌ Échec"
        print(f"  {collection}: {status}")


if __name__ == "__main__":
    main()