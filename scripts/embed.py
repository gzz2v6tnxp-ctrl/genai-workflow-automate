import sys
from pathlib import Path
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document

# Ajouter le répertoire racine du projet au path pour permettre les imports
# depuis d'autres dossiers (ex: scripts/ingest)
sys.path.append(str(Path(__file__).parent.parent))

from scripts.ingest.ingest_synth import load_synth_docs

# --- Constantes ---
# Modèle recommandé dans la roadmap : efficace et polyvalent.
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def generate_embeddings(
    documents: List[Document], model_name: str = DEFAULT_EMBEDDING_MODEL
) -> List[np.ndarray]:
    """
    Génère les embeddings pour une liste de documents en utilisant un modèle Sentence Transformer.

    Args:
        documents: Une liste d'objets Document de LangChain.
        model_name: Le nom du modèle Sentence Transformer à utiliser.

    Returns:
        Une liste de vecteurs d'embedding (numpy arrays).
    """
    print(f"Chargement du modèle d'embedding : '{model_name}'...")
    # Le modèle sera téléchargé depuis Hugging Face Hub la première fois.
    model = SentenceTransformer(model_name)

    # Extraire le contenu textuel de chaque document
    contents = [doc.page_content for doc in documents]

    print(f"Génération des embeddings pour {len(contents)} documents...")
    # L'option show_progress_bar est utile pour suivre l'avancement sur de grands datasets.
    embeddings = model.encode(contents, show_progress_bar=True)

    print("Génération des embeddings terminée.")
    return embeddings


# if __name__ == "__main__":
#     """
#     Bloc d'exécution pour tester la fonctionnalité d'embedding.
#     Charge quelques documents synthétiques et génère leurs embeddings.
#     """
#     print("--- Test du script d'embedding ---")

#     # 1. Charger quelques documents pour le test
#     print("Chargement de documents de test (source synthétique)...")
#     test_docs = load_synth_docs()
#     # Limitons à 5 documents pour un test rapide
#     test_docs = test_docs[:5]

#     # 2. Générer les embeddings
#     embeddings_result = generate_embeddings(test_docs)

#     # 3. Vérifier les résultats
#     print("\n--- Vérification des résultats ---")
#     print(f"Nombre d'embeddings générés : {len(embeddings_result)}")
#     if len(embeddings_result) > 0:
#         first_embedding = embeddings_result[0]
#         print(f"Dimension du premier vecteur d'embedding : {len(first_embedding)}")
#         print(f"Type du premier embedding : {type(first_embedding)}")
#         print(f"Aperçu du premier vecteur (5 premières valeurs) : {first_embedding[:5]}")