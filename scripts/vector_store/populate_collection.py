import sys
from pathlib import Path
import uuid
from typing import List

from qdrant_client import QdrantClient, models
from langchain_core.documents import Document

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config
from scripts.embed import generate_embeddings
from scripts.ingest.ingest_synth import load_synth_docs
from scripts.ingest.ingest_cfpb import load_cfpb_docs
from scripts.ingest.ingest_enron_mail import load_enron_docs
from scripts.chunking import chunk_documents

# --- Noms des Collections ---
PUBLIC_COLLECTION_NAME = "demo_public"
MAIN_KB_COLLECTION_NAME = "knowledge_base_main"


def load_all_documents(limit_per_source: int = None) -> List[Document]:
    """Charge et découpe intelligemment les documents."""
    all_docs = []
    print("--- Chargement des documents depuis toutes les sources ---")

    # Synth : généralement courts, mais on applique quand même le chunking au cas où
    print("Source: synth...")
    synth_docs = load_synth_docs()
    synth_chunked = chunk_documents(synth_docs, chunk_size=600)
    all_docs.extend(synth_chunked)

    # CFPB : plaintes souvent longues, chunking nécessaire
    print("Source: cfpb...")
    cfpb_docs = load_cfpb_docs(limit=limit_per_source)
    cfpb_chunked = chunk_documents(cfpb_docs, chunk_size=600)
    all_docs.extend(cfpb_chunked)

    # Enron : emails de longueurs variables, chunking pour les longs threads
    print("Source: enron...")
    enron_docs = load_enron_docs(limit=limit_per_source)
    enron_chunked = chunk_documents(enron_docs, chunk_size=600)
    all_docs.extend(enron_chunked)

    print(f"\n✅ Total de {len(all_docs)} chunks prêts pour embedding.")
    return all_docs


def upsert_data_to_collection(client: QdrantClient, collection_name: str, documents: List[Document]):
    """
    Génère les embeddings et insère les documents dans une collection Qdrant spécifiée.
    """
    if not documents:
        print(f"Aucun document à insérer dans '{collection_name}'.")
        return

    print(f"\n--- Traitement pour la collection '{collection_name}' ---")

    # 1. Générer les embeddings
    embeddings = generate_embeddings(documents)

    # 2. Préparer les points pour Qdrant
    points = []
    for i, doc in enumerate(documents):
        # Tenter de convertir l'ID existant en UUID. S'il échoue ou n'existe pas, en générer un nouveau.
        try:
            doc_id = str(uuid.UUID(str(doc.metadata.get("id"))))
        except (ValueError, TypeError):
            # Génère un UUID basé sur le contenu si aucun ID valide n'est trouvé
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc.page_content))

        payload = doc.metadata.copy()
        payload["page_content"] = doc.page_content
        
        points.append(
            models.PointStruct(
                id=doc_id, # Utiliser directement doc_id qui est maintenant un UUID valide
                vector=embeddings[i].tolist(),
                payload=payload,
            )
        )

    # 3. Insérer les points dans Qdrant par lots
    batch_size = 100  # Taille du lot (ajustable selon la taille de vos documents)
    total_batches = (len(points) + batch_size - 1) // batch_size
    
    print(f"Insertion de {len(points)} points dans '{collection_name}' par lots de {batch_size}...")
    
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        try:
            client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True,
            )
            print(f"  ✓ Lot {batch_num}/{total_batches} inséré ({len(batch)} points)")
        except Exception as e:
            print(f"  ✗ Erreur lors de l'insertion du lot {batch_num} : {e}")
            raise
    
    print(f"✅ Insertion dans '{collection_name}' terminée.")


def run_populate_collections(limit: int = 0):
    """
    Point d'entrée principal pour peupler les bases de données vectorielles.
    """
    all_documents = load_all_documents(limit_per_source=limit)
    if not all_documents:
        print("Aucun document à traiter. Arrêt du script.")
        return

    # synth_documents = [doc for doc in all_documents if doc.metadata.get("source") == "synth"]

    try:
        client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT, timeout=30000)
        print(f"\n🔗 Connecté à Qdrant sur {config.QDRANT_HOST}:{config.QDRANT_PORT}")

        # upsert_data_to_collection(client, PUBLIC_COLLECTION_NAME, synth_documents)
        upsert_data_to_collection(client, MAIN_KB_COLLECTION_NAME, all_documents)

        print("\n--- Vérification finale du nombre de points ---")
        public_count = client.count(collection_name=PUBLIC_COLLECTION_NAME, exact=True)
        main_kb_count = client.count(collection_name=MAIN_KB_COLLECTION_NAME, exact=True)
        print(f"📊 Collection '{PUBLIC_COLLECTION_NAME}' : {public_count.count} points")
        print(f"📊 Collection '{MAIN_KB_COLLECTION_NAME}' : {main_kb_count.count} points")

    except Exception as e:
        print(f"\n❌ Erreur lors de l'opération avec Qdrant : {e}")

if __name__ == "__main__":
    TEST_LIMIT = 200
    run_populate_collections(limit=TEST_LIMIT)


# def main(limit: int = None):
#     """
#     Point d'entrée principal pour peupler les bases de données vectorielles.
#     """
#     # 1. Charger tous les documents
#     all_documents = load_all_documents(limit_per_source=limit)
#     if not all_documents:
#         print("Aucun document à traiter. Arrêt du script.")
#         return

#     # 2. Séparer les documents par destination
#     synth_documents = [doc for doc in all_documents if doc.metadata.get("source") == "synth"]

#     # 3. Initialiser le client Qdrant
#     try:
#         client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
#         print(f"\nConnecté à Qdrant sur {config.QDRANT_HOST}:{config.QDRANT_PORT}")

#         # 4. Peupler la collection publique
#         upsert_data_to_collection(client, PUBLIC_COLLECTION_NAME, synth_documents)

#         # 5. Peupler la collection principale
#         upsert_data_to_collection(client, MAIN_KB_COLLECTION_NAME, all_documents)

#         # 6. Vérification finale
#         print("\n--- Vérification finale du nombre de points ---")
#         public_count = client.count(collection_name=PUBLIC_COLLECTION_NAME, exact=True)
#         main_kb_count = client.count(collection_name=MAIN_KB_COLLECTION_NAME, exact=True)
#         print(f"Collection '{PUBLIC_COLLECTION_NAME}' contient : {public_count.count} points.")
#         print(f"Collection '{MAIN_KB_COLLECTION_NAME}' contient : {main_kb_count.count} points.")

#     except Exception as e:
#         print(f"\nUne erreur est survenue lors de l'opération avec Qdrant : {e}")


# if __name__ == "__main__":
#     # Pour un test rapide, on peut limiter le nombre de documents par source (sauf synth)
#     # Mettre à None pour tout traiter (attention, peut être long)
#     TEST_LIMIT = 500
#     main(limit=TEST_LIMIT)