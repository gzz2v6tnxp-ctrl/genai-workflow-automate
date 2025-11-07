from fastapi import APIRouter, BackgroundTasks, HTTPException
import sys
from pathlib import Path

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importer les fonctions logiques de nos scripts
from scripts.vector_store.build_collection import run_build_collections
from scripts.vector_store.populate_collection import run_populate_collections

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion & Vector Store"],
)

@router.post("/build-collections", status_code=202)
async def build_collections_endpoint(background_tasks: BackgroundTasks):
    """
    Lance la création (ou recréation) des collections Qdrant en tâche de fond.
    """
    try:
        print("Lancement de la tâche de création des collections en arrière-plan.")
        background_tasks.add_task(run_build_collections)
        return {"message": "La création des collections a été lancée en arrière-plan."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de la tâche : {e}")


@router.post("/populate-collections", status_code=202)
async def populate_collections_endpoint(background_tasks: BackgroundTasks, limit: int = None):
    """
    Lance le peuplement des collections Qdrant en tâche de fond.
    Un 'limit' peut être spécifié pour les sources (sauf synthétique) pour un test rapide.
    """
    try:
        print(f"Lancement de la tâche de peuplement des collections en arrière-plan avec une limite de {limit}.")
        background_tasks.add_task(run_populate_collections, limit=limit)
        return {"message": "Le peuplement des collections a été lancé en arrière-plan."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de la tâche : {e}")
