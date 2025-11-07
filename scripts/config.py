import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env à la racine du projet
# Le chemin est construit en remontant de deux niveaux depuis le répertoire 'scripts'
load_dotenv()

# --- Configuration Qdrant ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Configuration Qdrant Cloud (pour la migration via snapshots)
QDRANT_CLOUD_URL = os.getenv("QDRANT_CLOUD_URL")  # Ex: https://xxx.aws.cloud.qdrant.io
# COLLECTION_NAME = os.getenv("COLLECTION_NAME", "genai_workflow_docs")
# COLLECTION_NAME = "demo_public"

# --- Configuration du Modèle d'Embedding ---
# La dimension des vecteurs est déterminée par le modèle d'embedding.
# Pour "all-mpnet-base-v2", cette dimension est 768 (vs 384 pour all-MiniLM-L6-v2).
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", 768))
DEFAULT_EMBEDDING_MODEL = str(os.getenv("DEFAULT_EMBEDDING_MODEL", "all-mpnet-base-v2"))

# --- Configuration LLM (OpenAI) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Validation simple ---
if not OPENAI_API_KEY:
    print("Avertissement : La variable d'environnement OPENAI_API_KEY n'est pas définie.")
