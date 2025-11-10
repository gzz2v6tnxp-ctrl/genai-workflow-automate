from typing import List, TypedDict, Optional


class GraphState(TypedDict, total=False):
    """
    Représente l'état de notre graphe.

    Les clés sont facultatives (total=False) car le graphe construit progressivement l'état.

    Champs courants:
      - question (str)
      - generation (str)
      - documents (List[str])
      - sources (List[dict])
      - grade (str)
      - collection (str)         # collection demandée par le client
      - sources_filter (List[str])
      - response_lang (str)
      - confidence (float)
    """
    question: str
    generation: str
    documents: List[str]
    sources: List[str]
    grade: str
    collection: str
    sources_filter: List[str]
    response_lang: str
    confidence: float
