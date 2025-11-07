import sys
from pathlib import Path

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Imports externes
from langgraph.graph import END, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Imports locaux
from agents.state import GraphState
from scripts import config
from scripts.vector_store.retrieve import DocumentRetriever


# Charger les prompts depuis le fichier Markdown
def load_prompts():
    """Charge les prompts depuis le fichier prompts.md avec markers.

    Markers utilisés:
      <!-- PROMPT:GENERATION:SYSTEM:START --> ... END
      <!-- PROMPT:GENERATION:USER:START --> ... END
    Fallback: ancienne logique si markers absents.
    """
    prompts_file = Path(__file__).parent / "prompts.md"
    with open(prompts_file, "r", encoding="utf-8") as f:
        content = f.read()

    def extract_between(text: str, start_marker: str, end_marker: str) -> str | None:
        s = text.find(start_marker)
        if s == -1:
            return None
        e = text.find(end_marker, s + len(start_marker))
        if e == -1:
            return None
        return text[s + len(start_marker):e].strip()

    # Try marker-based extraction
    system_block = extract_between(
        content,
        "<!-- PROMPT:GENERATION:SYSTEM:START -->",
        "<!-- PROMPT:GENERATION:SYSTEM:END -->"
    )
    user_block = extract_between(
        content,
        "<!-- PROMPT:GENERATION:USER:START -->",
        "<!-- PROMPT:GENERATION:USER:END -->"
    )

    if system_block and user_block:
        # Inside those blocks there is a fenced ```text ... ``` we strip again if present
        def strip_fence(b: str) -> str:
            if "```" in b:
                first = b.find("```")
                second = b.find("```", first + 3)
                if second != -1:
                    inner = b[first + 3:second]
                    # remove optional 'text' prefix
                    if inner.startswith("text"):
                        inner = inner[len("text"):]
                    return inner.strip()
            return b.strip()
        system_prompt = strip_fence(system_block)
        user_template = strip_fence(user_block)
        return system_prompt, user_template

    # Fallback legacy parsing
    system_start = content.find("```text", content.find("### **System Prompt**"))
    system_end = content.find("```", system_start + 7)
    system_prompt = content[system_start + 7:system_end].strip()
    user_start = content.find("```text", content.find("### **User Prompt Template**"))
    user_end = content.find("```", user_start + 7)
    user_template = content[user_start + 7:user_end].strip()
    return system_prompt, user_template


# Charger les prompts au démarrage
SYSTEM_PROMPT, USER_TEMPLATE = load_prompts()

# Détection de langue simple (FR / EN) avec heuristiques + support optionnel langdetect
try:
    from langdetect import detect as _ld_detect  # type: ignore
except Exception:  # pragma: no cover
    _ld_detect = None

import re

FRENCH_MARKERS = {
    "carte", "bancaire", "compte", "problème", "bonjour", "merci", "solde", "crédit", "bloquée", "facturation", "non", "autorisé", "opposition"
}

def detect_language(text: str) -> str:
    """Détecte la langue (fr/en) de manière robuste.

    1. Essaie langdetect si disponible.
    2. Heuristique: présence mots FR + caractères accentués.
    3. Fallback: 'en'.
    """
    lower = text.lower()
    if _ld_detect:
        try:
            lang = _ld_detect(text)
            if lang.startswith("fr"):
                return "fr"
            if lang.startswith("en"):
                return "en"
        except Exception:
            pass
    # Accent check
    if re.search(r"[àâçéèêëîïôùûüÿœ]", lower):
        return "fr"
    # Marker hits
    hits = sum(1 for w in FRENCH_MARKERS if w in lower)
    if hits >= 2:
        return "fr"
    return "en"


def retrieve_documents(state):
    """Récupère les documents pertinents depuis Qdrant Cloud."""
    print("---RÉCUPÉRATION DES DOCUMENTS---")
    question = state["question"]
    collection = state.get("collection", "demo_public")
    sources_filter = state.get("sources_filter")  # list[str] optionnelle
    print(f"Question: {question}")
    print(f"Collection demandée: {collection}")
    if sources_filter:
        print(f"Filtre sources: {sources_filter}")

    try:
        retriever = DocumentRetriever(
            collection_name=collection,
            use_cloud=True
        )

        # Construire filtre sources si collection principale
        filters = None
        if collection == "knowledge_base_main" and sources_filter:
            # Validation des valeurs autorisées
            allowed = {"synth", "cfpb", "enron"}
            filtered_values = [s for s in sources_filter if s in allowed]
            if filtered_values:
                filters = {"source": filtered_values}
        results = retriever.retrieve(
            query=question,
            top_k=5,
            score_threshold=0.5,
            filters=filters
        )

        if results:
            documents = []
            sources = []

            for i, result in enumerate(results, 1):
                doc_text = f"[Document {i}] (Score: {result['score']:.3f})\n{result['content']}"
                documents.append(doc_text)

                source_info = {
                    "id": result["id"],
                    "score": result["score"],
                    "source": result["metadata"].get("source", "unknown"),
                    "lang": result["metadata"].get("lang", "unknown"),
                    "type": result["metadata"].get("type", "unknown")
                }
                sources.append(source_info)

            print(f"✅ {len(documents)} document(s) récupéré(s)")
            print(
                f"Score: {results[0]['score']:.3f} - {results[-1]['score']:.3f}")

            return {
                "documents": documents,
                "sources": sources,
                "question": question
            }
        else:
            print("⚠️ Aucun document pertinent trouvé")
            return {"documents": [], "sources": [], "question": question}

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return {"documents": [], "sources": [], "question": question, "error": str(e)}


def grade_documents(state):
    """Évalue la pertinence des documents récupérés."""
    print("---ÉVALUATION DE LA PERTINENCE---")

    documents = state.get("documents", [])
    sources = state.get("sources", [])
    error = state.get("error")

    if error:
        print(f"❌ Erreur: {error}")
        return {"grade": "not_relevant"}

    if not documents:
        print("❌ Aucun document")
        return {"grade": "not_relevant"}

    best_score = sources[0]["score"] if sources else 0

    if best_score >= 0.6:
        print(f"✅ Excellent score: {best_score:.3f}")
        grade = "relevant"
    elif best_score >= 0.5:
        print(f"⚠️ Score acceptable: {best_score:.3f}")
        grade = "relevant"
    else:
        print(f"❌ Score trop faible: {best_score:.3f}")
        grade = "not_relevant"

    return {"grade": grade}


def generate_answer(state):
    """Génère une réponse avec OpenAI GPT en utilisant les prompts depuis prompts.md"""
    print("---GÉNÉRATION DE LA RÉPONSE---")
    question = state["question"]
    documents = state["documents"]
    sources = state.get("sources", [])

    # Détecter la langue de la question pour forcer la réponse
    lang = detect_language(question)
    print(f"🈶 Langue détectée: {lang}")

    # Préparer le contexte
    context = "\n\n".join(documents)
    
    # Construire le system prompt dynamique selon la langue détectée
    if lang == "en":
        dynamic_system = (
            "You are a professional banking assistant working for a reputable financial institution.\n\n"
            "Your role is to help customers resolve banking issues with clear, precise and actionable guidance.\n\n"
            "Guidelines:\n"
            "- Answer directly and naturally, like an experienced banking advisor\n"
            "- NEVER mention using context, documents or a database\n"
            "- Be empathetic and professional\n"
            "- Always propose concrete solutions and next steps\n"
            "- Structure answers clearly (bullet points, numbering)\n"
            "- If information is incomplete, propose alternatives (customer support, emergency numbers)\n"
            "- Remain factual and do not speculate\n\n"
            "IMPORTANT LANGUAGE RULE: Reply STRICTLY in English. Do not mix languages."
        )
        user_template_dynamic = USER_TEMPLATE.replace(
            "Réponds de manière professionnelle et orientée solution, dans la MÊME LANGUE que la question ci-dessus.",
            "Answer professionally and solution-oriented, in the SAME LANGUAGE as the user's question (English here)."
        )
    else:  # French
        dynamic_system = SYSTEM_PROMPT + "\n\nLANGUE DÉTECTÉE: FR — Réponds UNIQUEMENT en français, ne mélange pas les langues."
        user_template_dynamic = USER_TEMPLATE

    # Créer le prompt avec le format OpenAI (system + user) + variables
    prompt = ChatPromptTemplate.from_messages([
        ("system", dynamic_system),
        ("user", user_template_dynamic)
    ])
    
    # Initialiser le LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=config.OPENAI_TEMPERATURE,
        max_tokens=config.OPENAI_MAX_TOKENS,
        api_key=config.OPENAI_API_KEY
    )
    
    # Créer la chaîne
    chain = prompt | llm

    try:
        # Générer la réponse
        response = chain.invoke({
            "context": context,
            "question": question,
            "output_format": "text"  # peut évoluer vers 'json' selon besoin futur
        })
        generation = response.content

        # Validation de langue et éventuelle 2e tentative stricte
        def _validate_lang(txt: str, expected: str) -> bool:
            detected = detect_language(txt)
            return detected == expected

        if not _validate_lang(generation, lang):
            print("⚠️ Langue de la réponse non conforme. Nouvelle tentative stricte...")
            if lang == "en":
                strict_system = dynamic_system + "\n\nHARD REQUIREMENT: Reply ONLY in English. If any non-English word appears, rewrite fully in English."
            else:
                strict_system = dynamic_system + "\n\nEXIGENCE FORTE: Réponds UNIQUEMENT en français. Si des mots non-français apparaissent, réécris intégralement en français."

            strict_prompt = ChatPromptTemplate.from_messages([
                ("system", strict_system),
                ("user", user_template_dynamic)
            ])
            strict_chain = strict_prompt | llm
            response2 = strict_chain.invoke({
                "context": context,
                "question": question,
                "output_format": "text"
            })
            generation2 = response2.content
            if _validate_lang(generation2, lang):
                generation = generation2

        print(f"✅ Réponse générée ({len(generation)} caractères)")
        print(f"Modèle: {config.OPENAI_MODEL}")

        return {"generation": generation, "sources": sources, "response_lang": lang}

    except Exception as e:
        print(f"❌ Erreur LLM: {e}")
        fallback_msg = (
            "Sorry, an error occurred while generating the answer." if lang == "en" else
            "Désolé, une erreur s'est produite lors de la génération de la réponse."
        )
        return {
            "generation": fallback_msg,
            "sources": sources,
            "response_lang": lang
        }
def fallback_response(state):
    """Réponse par défaut si aucun document pertinent."""
    print("---FALLBACK---")
    q = state.get("question", "")
    lang = detect_language(q) if q else "fr"
    if lang == "en":
        generation = (
            "Sorry, I couldn't find enough information to answer your question right now.\n"
            "Please contact customer support for assistance."
        )
    else:
        generation = (
            "Désolé, je n'ai pas trouvé d'informations pertinentes pour répondre à votre question.\n"
            "Veuillez contacter le support client pour plus d'assistance."
        )
    return {"generation": generation, "sources": [], "response_lang": lang}


def decide_to_generate(state):
    """Détermine le chemin à suivre après l'évaluation."""
    return "generate" if state.get("grade") == "relevant" else "fallback"


workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve_documents)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate_answer)
workflow.add_node("fallback", fallback_response)

workflow.set_entry_point("retrieve")

workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {"generate": "generate", "fallback": "fallback"}
)
workflow.add_edge("generate", END)
workflow.add_edge("fallback", END)

app = workflow.compile()


# if __name__ == "__main__":
#     print("=" * 70)
#     print("🤖 TEST DU WORKFLOW RAG")
#     print("=" * 70)

#     tests = [
#         {"question": "Ma carte bancaire est bloquée, que faire ?", "lang": "FR"},
#         {"question": "unauthorized charge on my credit card", "lang": "EN"}
#     ]

#     for idx, test in enumerate(tests, 1):
#         print(f"\n📝 TEST {idx}: {test['lang']}")
#         print("-" * 70)

#         for output in app.stream({"question": test["question"]}):
#             for key, value in output.items():
#                 print(f"\n🔹 {key.upper()}")

#                 if key == "retrieve":
#                     print(f"Documents: {len(value.get('documents', []))}")
#                     if value.get('sources'):
#                         print(f"Score: {value['sources'][0]['score']:.3f}")

#                 elif key == "grade_documents":
#                     print(f"Grade: {value.get('grade')}")

#                 elif key in ["generate", "fallback"]:
#                     print(f"Réponse: {value.get('generation')[:200]}...")

#         print("-" * 70)

#     print("\n" + "=" * 70)
#     print("✅ Tests terminés")
#     print("=" * 70)
