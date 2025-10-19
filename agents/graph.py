from langgraph.graph import END, StateGraph
from .state import GraphState

def retrieve_documents(state):
    """
    Récupère les documents depuis la base de données vectorielle.
    (Implémentation à venir dans la Phase C)
    """
    print("---RÉCUPÉRATION DES DOCUMENTS---")
    question = state["question"]
    # Logique de recherche dans Qdrant... (placeholder)
    documents = ["Document A from Qdrant", "Document B from Qdrant"] 
    print(f"Documents récupérés: {documents}")
    return {"documents": documents, "question": question}

def grade_documents(state):
    """
    Évalue la pertinence des documents récupérés.
    (Implémentation à venir)
    """
    print("---ÉVALUATION DE LA PERTINENCE DES DOCUMENTS---")
    # Logique pour évaluer si les documents répondent à la question...
    # Pour l'instant, on considère qu'ils sont toujours pertinents.
    is_relevant = True 
    if is_relevant:
        print("---DÉCISION: DOCUMENTS PERTINENTS---")
        grade = "relevant"
    else:
        print("---DÉCISION: DOCUMENTS NON PERTINENTS---")
        grade = "not_relevant"
    
    return {"grade": grade}

def generate_answer(state):
    """
    Génère une réponse en utilisant le LLM.
    (Implémentation à venir dans la Phase D)
    """
    print("---GÉNÉRATION DE LA RÉPONSE---")
    question = state["question"]
    documents = state["documents"]
    # Logique d'appel au LLM avec un prompt... (placeholder)
    generation = "Réponse générée par le LLM (placeholder)." 
    sources = ["Source A", "Source B"] 
    print(f"Réponse générée: {generation}")
    return {"generation": generation, "sources": sources}

def fallback_response(state):
    """
    Génère une réponse par défaut si aucun document pertinent n'est trouvé.
    """
    print("---AUCUN DOCUMENT PERTINENT TROUVÉ, UTILISATION DU FALLBACK---")
    generation = "Désolé, je n'ai pas pu trouver d'informations pertinentes pour répondre à votre question."
    return {"generation": generation, "sources": []}

# --- Définition de la logique conditionnelle ---

def decide_to_generate(state):
    """
    Détermine le chemin à suivre après l'évaluation des documents.
    """
    if state.get("grade") == "relevant":
        return "generate"
    else:
        return "fallback"

# --- Assemblage du graphe ---

workflow = StateGraph(GraphState)

# Ajout des nœuds
workflow.add_node("retrieve", retrieve_documents)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate_answer)
workflow.add_node("fallback", fallback_response)

# Définition du point d'entrée
workflow.set_entry_point("retrieve")

# Ajout des arêtes
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "generate": "generate",
        "fallback": "fallback",
    },
)
workflow.add_edge("generate", END)
workflow.add_edge("fallback", END)

# Compilation du graphe
app = workflow.compile()

# # Pour tester la structure
# if __name__ == "__main__":
#     inputs = {"question": "Quel est le solde de ma carte ?"}
#     for output in app.stream(inputs):
#         for key, value in output.items():
#             print(f"Sortie du noeud '{key}':")
#             print("---")
#             print(value)
#         print("\n---\n")
