import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config
from scripts.embed import generate_embeddings
from langchain_core.documents import Document


class DocumentRetriever:
    """
    Classe pour gérer la récupération de documents pertinents depuis Qdrant.
    """

    def __init__(
        self,
        collection_name: str,
        use_cloud: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        cloud_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialise le récupérateur de documents.

        Args:
            collection_name: Nom de la collection Qdrant à interroger.
            use_cloud: Si True, utilise Qdrant Cloud, sinon utilise l'instance locale.
            host: Hôte Qdrant local (par défaut depuis config).
            port: Port Qdrant local (par défaut depuis config).
            cloud_url: URL du cluster Qdrant Cloud (par défaut depuis config).
            api_key: Clé API Qdrant Cloud (par défaut depuis config).
        """
        self.collection_name = collection_name
        self.use_cloud = use_cloud
        
        if use_cloud:
            # Connexion au cluster Qdrant Cloud
            self.client = QdrantClient(
                url=cloud_url or config.QDRANT_CLOUD_URL,
                api_key=api_key or config.QDRANT_API_KEY,
            )
            print(f"✅ Connecté à Qdrant Cloud : {cloud_url or config.QDRANT_CLOUD_URL}")
        else:
            # Connexion à l'instance locale
            self.client = QdrantClient(
                host=host or config.QDRANT_HOST,
                port=port or config.QDRANT_PORT,
            )
            print(f"✅ Connecté à Qdrant Local : {host or config.QDRANT_HOST}:{port or config.QDRANT_PORT}")
        
        print(f"📚 Collection active : '{self.collection_name}'")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les documents les plus pertinents pour une requête donnée.

        Args:
            query: La requête textuelle de l'utilisateur.
            top_k: Nombre de documents à récupérer.
            score_threshold: Score de similarité minimum (0-1). Les résultats en dessous sont exclus.
            filters: Filtres de métadonnées optionnels (ex: {"source": "synthetic"}).

        Returns:
            Liste de dictionnaires contenant les documents et leurs scores.
        """
        print(f"\n--- Recherche de documents pour la requête : '{query}' ---")

        # 1. Générer l'embedding de la requête
        query_doc = Document(page_content=query)
        query_embedding = generate_embeddings([query_doc])[0]

        # 2. Construire le filtre Qdrant si nécessaire
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                # Enforce OR on multiple values using MatchAny (strict)
                if isinstance(value, (list, tuple, set)):
                    conditions.append(
                        FieldCondition(key=key, match=MatchAny(any=list(value)))
                    )
                else:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
            query_filter = Filter(must=conditions)

        # 3. Rechercher dans Qdrant
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False,
        )

        # 4. Formater les résultats
        results = []
        for hit in search_results.points:
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