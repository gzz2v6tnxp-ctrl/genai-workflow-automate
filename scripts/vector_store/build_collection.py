from qdrant_client import QdrantClient, models
import sys
from pathlib import Path

# Ajouter le répertoire racine du projet au path pour permettre les imports
# depuis d'autres dossiers (ex: scripts/config.py)
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config


def create_qdrant_collection(
    client: QdrantClient, collection_name: str, vector_dim: int
):
    """
    Crée ou recrée une collection dans Qdrant avec la configuration spécifiée.

    Args:
        client: Le client Qdrant connecté.
        collection_name: Le nom de la collection à créer.
        vector_dim: La dimension des vecteurs qui seront stockés.
    """
    try:
        print(f"Tentative de création de la collection '{collection_name}'...")
        # recreate_collection est pratique en développement pour s'assurer
        # de repartir d'un état propre à chaque exécution.
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_dim, distance=models.Distance.COSINE
            ),
        )
        print(f"La collection '{collection_name}' a été créée/recréée avec succès.")
        print(f" -> Dimension des vecteurs : {vector_dim}")
        print(f" -> Métrique de distance : {models.Distance.COSINE}")

    except Exception as e:
        print(f"Une erreur est survenue lors de la création de la collection : {e}")
        raise

def run_build_collections():
    """
    Point d'entrée pour créer les collections Qdrant.
    """
    print("--- Démarrage du script de création de collection Qdrant ---")
    
    PUBLIC_COLLECTION_NAME = "demo_public"
    MAIN_KB_COLLECTION_NAME = "knowledge_base_main"

    try:
        qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        print(f"Connecté au client Qdrant à l'adresse {config.QDRANT_HOST}:{config.QDRANT_PORT}")

        create_qdrant_collection(
            client=qdrant_client,
            collection_name=PUBLIC_COLLECTION_NAME,
            vector_dim=config.VECTOR_DIMENSION,
        )

        create_qdrant_collection(
            client=qdrant_client,
            collection_name=MAIN_KB_COLLECTION_NAME,
            vector_dim=config.VECTOR_DIMENSION,
        )

        print("\nOpération terminée avec succès. Les deux collections ont été créées.")

    except Exception as e:
        print(f"\nLe script a échoué. Erreur détaillée : {e}")

if __name__ == "__main__":
    run_build_collections()

# if __name__ == "__main__":
#     """
#     Point d'entrée pour créer la collection Qdrant depuis la ligne de commande.
#     """
#     print("--- Démarrage du script de création de collection Qdrant ---")
#     try:
#         # Initialisation du client Qdrant en utilisant la configuration centralisée
#         qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
#         print(f"Connecté au client Qdrant à l'adresse {config.QDRANT_HOST}:{config.QDRANT_PORT}")

#         # Appel de la fonction pour créer la collection
#         create_qdrant_collection(
#             client=qdrant_client,
#             collection_name="knowledge_base_main",
#             vector_dim=config.VECTOR_DIMENSION,
#         )

#         print("\nOpération terminée avec succès.")

#     except Exception as e:
#         print(f"\nLe script a échoué. Assurez-vous que l'instance Qdrant est bien en cours d'exécution sur Docker.")
#         print(f"Erreur détaillée : {e}")