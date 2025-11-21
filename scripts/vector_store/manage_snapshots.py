import sys
from pathlib import Path
from qdrant_client import QdrantClient

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config


def delete_cloud_collection(collection_name: str) -> None:
    """
    Supprime complètement une collection sur Qdrant Cloud.
    À utiliser avant de recréer la collection avec un nouveau modèle d'embedding.

    Effets :
      - La collection est effacée (points + index).
      - Les snapshots associés à cette collection sont également supprimés côté Cloud.
    """
    if not config.QDRANT_CLOUD_URL or not config.QDRANT_API_KEY:
        raise RuntimeError(
            "QDRANT_CLOUD_URL ou QDRANT_API_KEY manquant(e) dans la configuration."
        )

    client = QdrantClient(
        url=config.QDRANT_CLOUD_URL,
        api_key=config.QDRANT_API_KEY,
    )

    print(f"🔗 Connecté à Qdrant Cloud : {config.QDRANT_CLOUD_URL}")
    print(f"🗑️  Suppression de la collection cloud '{collection_name}'...")

    try:
        client.delete_collection(collection_name)
        print(f"✅ Collection '{collection_name}' supprimée sur Qdrant Cloud.")
    except Exception as e:
        print(f"❌ Erreur lors de la suppression de la collection '{collection_name}' : {e}")
        raise


if __name__ == "__main__":
    # Exemple : nettoyer la collection principale avant de la recréer avec OpenAI embeddings
    target_collection = "knowledge_base_main"

    print(f"⚠️ Cette opération va SUPPRIMER définitivement la collection '{target_collection}' sur Qdrant Cloud.")
    confirm = input("Continuer ? (y/N): ")
    if confirm.lower() == "y":
        delete_cloud_collection(target_collection)
    else:
        print("❌ Opération annulée.")