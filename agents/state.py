from typing import List, TypedDict

class GraphState(TypedDict):
    """
    Représente l'état de notre graphe.

    Attributs:
        question (str): La question du ticket client.
        generation (str): La réponse générée par le LLM.
        documents (List[str]): La liste des documents récupérés du vector store.
        sources (List[str]): La liste des sources des documents pertinents.
        grade (str): La décision de pertinence des documents ('relevant' ou 'not_relevant').
    """
    question: str
    generation: str
    documents: List[str]
    sources: List[str]
    grade: str
