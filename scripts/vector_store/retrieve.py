import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings  # ✅ Remplacement de SentenceTransformer

class DocumentRetriever:
    def __init__(self, collection_name: str = "knowledge_base_main", 
                 use_cloud: bool = True,
                 host: str = None, port: int = None, 
                 cloud_url: str = None, api_key: str = None):
        self.collection_name = collection_name
        self.use_cloud = use_cloud
        
        # Client Qdrant
        if use_cloud:
            self.client = QdrantClient(
                url=cloud_url or config.QDRANT_CLOUD_URL,
                api_key=api_key or config.QDRANT_API_KEY,
            )
            print(f"✅ Connecté à Qdrant Cloud : {cloud_url or config.QDRANT_CLOUD_URL}")
        else:
            self.client = QdrantClient(
                host=host or config.QDRANT_HOST,
                port=port or config.QDRANT_PORT
            )
            print(f"✅ Connecté à Qdrant Local : {host or config.QDRANT_HOST}:{port or config.QDRANT_PORT}")

        # ✅ Initialisation du modèle OpenAI pour la requête (1536 dims)
        self.embedding_model = OpenAIEmbeddings(
            model=config.DEFAULT_EMBEDDING_MODEL, # "text-embedding-3-small"
            api_key=config.OPENAI_API_KEY
        )
        
        print(f"📚 Collection active : '{self.collection_name}'")

    def retrieve(self, query: str, top_k: int = 5, score_threshold: float = None, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        Vectorise la question avec OpenAI et cherche dans Qdrant.
        """
        print(f"\n--- Recherche de documents pour la requête : '{query}' ---")

        # 1. Vectoriser la question
        try:
            query_vector = self.embedding_model.embed_query(query)
        except Exception as e:
            print(f"❌ Erreur embedding OpenAI: {e}")
            return []

        # 2. Construire les filtres Qdrant (si présents)
        query_filter = None
        if filters:
            from qdrant_client import models
            must_conditions = []
            for key, value in filters.items():
                # Gestion des listes (OR)
                if isinstance(value, (list, tuple, set)):
                    must_conditions.append(
                        models.FieldCondition(
                            key=key, # key est déjà metadata.source ou source selon ingestion
                            match=models.MatchAny(any=list(value))
                        )
                    )
                else:
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
            if must_conditions:
                query_filter = models.Filter(must=must_conditions)

        # 3. Recherche
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold
        )

        # 4. Formatage
        results = []
        for hit in search_result:
            results.append({
                "id": hit.id,
                "score": hit.score,
                "content": hit.payload.get("page_content", ""),
                "metadata": {k: v for k, v in hit.payload.items() if k != "page_content"},
            })
        
        print(f"Trouvé {len(results)} document(s) pertinent(s).")
        return results

    def retrieve_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un document spécifique par son ID.

        Args:
            document_id: L'ID du document à récupérer.

        Returns:
            Dictionnaire contenant le document, ou None si non trouvé.
        """
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[document_id],
                with_payload=True,
                with_vectors=False,
            )

            if points:
                point = points[0]
                return {
                    "id": point.id,
                    "content": point.payload.get("page_content", ""),
                    "metadata": {k: v for k, v in point.payload.items() if k != "page_content"},
                }
            else:
                print(f"Aucun document trouvé avec l'ID : {document_id}")
                return None

        except Exception as e:
            print(f"Erreur lors de la récupération du document {document_id} : {e}")
            return None

    def count_documents(self) -> int:
        """
        Retourne le nombre total de documents dans la collection.

        Returns:
            Nombre de documents.
        """
        count_result = self.client.count(
            collection_name=self.collection_name,
            exact=True,
        )
        return count_result.count


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    print("=" * 70)
    print("🔍 TEST DU RETRIEVER QDRANT")
    print("=" * 70)
    
    # Par défaut, utilise Qdrant Cloud
    # Pour utiliser l'instance locale, passez use_cloud=False
    print("\n📡 Mode : Qdrant Cloud (production)")
    retriever = DocumentRetriever(
        collection_name="knowledge_base_main",
        use_cloud=True  # True = Cloud, False = Local
    )
    
    # Exemple 1 : Recherche simple
    # print("\n" + "=" * 70)
    # print("TEST 1 : Recherche simple")
    # print("=" * 70)
    
    # query = "unauthorized charge"
    # results = retriever.retrieve(query=query, top_k=3)
    
    # print("\n=== Résultats de la recherche ===")
    # for i, result in enumerate(results, 1):
    #     print(f"\n[{i}] Score: {result['score']:.4f}")
    #     print(f"ID: {result['id']}")
    #     print(f"Contenu: {result['content'][:200]}...")
    #     print(f"Source: {result['metadata'].get('source', 'N/A')}")
    #     print(f"Métadonnées: {result['metadata']}")

    # # Exemple 2 : Recherche avec filtres
    # print("\n" + "=" * 70)
    # print("TEST 2 : Recherche avec filtre (source=synthetic)")
    # print("=" * 70)
    
    # filtered_results = retriever.retrieve(
    #     query=query,
    #     top_k=3,
    #     filters={"source": "synth"},
    #     score_threshold=0.5,
    # )
    
    # print(f"\n📊 Résultats filtrés : {len(filtered_results)}")
    # for i, result in enumerate(filtered_results, 1):
    #     print(f"  [{i}] Score: {result['score']:.4f} | Source: {result['metadata'].get('source')}")

    # Exemple 3 : Récupération par ID
    # print("\n" + "=" * 70)
    # print("TEST 3 : Récupération par CFPB")
    # print("=" * 70)

    # # Recherche qui devrait matcher CFPB
    # cfpb_results = retriever.retrieve(
    #     query="credit card dispute unauthorized transaction",
    #     top_k=5,
    #     filters={"source": "cfpb"}  # Vérifier le nom exact dans vos données
    # )

    # if cfpb_results:
    #     cfpb_doc_id = cfpb_results[0]["id"]
    #     print(f"\nRécupération du document CFPB avec ID : {cfpb_doc_id}")
    #     cfpb_doc = retriever.retrieve_by_id(document_id=cfpb_doc_id)
    #     if cfpb_doc:
    #         print(f"Contenu CFPB : {cfpb_doc['content'][:300]}...")

    # Test 4 : Vérifier Enron
    # print("\n" + "=" * 70)
    # print("TEST 4 : Récupération Enron Emails")
    # print("=" * 70)

    # enron_results = retriever.retrieve(
    #     query="meeting schedule energy trading",
    #     top_k=5,
    #     filters={"source": "enron"}
    # )

    # if enron_results:
    #     print(f"✅ Trouvé {len(enron_results)} emails Enron")
    #     print(f"Exemple : {enron_results[0]['content'][:800]}...")
    # else:
    #     print("⚠️ Aucun résultat Enron - Essayer 'enron_emails'")