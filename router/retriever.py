from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.vector_store.retrieve import DocumentRetriever

router = APIRouter(
    prefix="/retriever",
    tags=["Document Retrieval"],
)


class SearchRequest(BaseModel):
    """Modèle de requête pour la recherche de documents."""
    query: str = Field(..., description="La requête textuelle de l'utilisateur", min_length=1)
    top_k: int = Field(default=5, description="Nombre de documents à récupérer", ge=1, le=50)
    score_threshold: Optional[float] = Field(
        default=None,
        description="Score de similarité minimum (0-1)",
        ge=0.0,
        le=1.0
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filtres de métadonnées optionnels (ex: {'source': '*synth'})"
    )
    collection_name: str = Field(
        default="demo_public",
        description="Nom de la collection Qdrant à interroger"
    )


class SearchResult(BaseModel):
    """Modèle de résultat pour un document trouvé."""
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Modèle de réponse pour la recherche de documents."""
    query: str
    total_results: int
    results: List[SearchResult]


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Effectue une recherche sémantique dans la collection Qdrant spécifiée.
    
    - **query**: La question ou le texte à rechercher
    - **top_k**: Nombre maximum de résultats à retourner (1-50)
    - **score_threshold**: Seuil de score minimum pour filtrer les résultats (optionnel)
    - **filters**: Filtres sur les métadonnées, par exemple {"source": "synthetic"}
    - **collection_name**: Nom de la collection Qdrant (par défaut: "demo_public")
    
    Retourne les documents les plus pertinents avec leurs scores de similarité.
    """
    try:
        # Initialiser le retriever avec la collection spécifiée
        retriever = DocumentRetriever(collection_name=request.collection_name)
        
        # Effectuer la recherche
        results = retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            filters=request.filters,
        )
        
        # Formater la réponse
        search_results = [
            SearchResult(
                id=result["id"],
                score=result["score"],
                content=result["content"],
                metadata=result["metadata"]
            )
            for result in results
        ]
        
        return SearchResponse(
            query=request.query,
            total_results=len(search_results),
            results=search_results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche de documents : {str(e)}"
        )


@router.get("/collections/{collection_name}/count")
async def count_documents_in_collection(collection_name: str):
    """
    Retourne le nombre total de documents dans une collection spécifiée.
    
    - **collection_name**: Nom de la collection Qdrant à interroger
    """
    try:
        retriever = DocumentRetriever(collection_name=collection_name)
        count = retriever.count_documents()
        
        return {
            "collection_name": collection_name,
            "document_count": count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du comptage des documents : {str(e)}"
        )


@router.get("/documents/{document_id}")
async def get_document_by_id(
    document_id: str,
    collection_name: str = Query(default="demo_public", description="Nom de la collection Qdrant")
):
    """
    Récupère un document spécifique par son ID.
    
    - **document_id**: L'identifiant unique du document
    - **collection_name**: Nom de la collection Qdrant (par défaut: "demo_public")
    """
    try:
        retriever = DocumentRetriever(collection_name=collection_name)
        document = retriever.retrieve_by_id(document_id)
        
        if document is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document avec l'ID '{document_id}' non trouvé dans la collection '{collection_name}'"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du document : {str(e)}"
        )
