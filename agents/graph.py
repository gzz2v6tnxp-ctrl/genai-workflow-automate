import re
from scripts.vector_store.retrieve import DocumentRetriever
from scripts import config
from agents.state import GraphState
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
import sys
from pathlib import Path
import os
import json
import uuid
from datetime import datetime

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Imports externes

# Imports locaux


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
    system_start = content.find(
        "```text", content.find("### **System Prompt**"))
    system_end = content.find("```", system_start + 7)
    system_prompt = content[system_start + 7:system_end].strip()
    user_start = content.find(
        "```text", content.find("### **User Prompt Template**"))
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
    print('State for retrieval:', state)
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
            score_threshold=0.35,
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


def evaluate_response(state):
    """Quality gate: vérifie citations, calcule confiance et décide human_review/fallback/good.

    - Enregistre une métrique ligne JSON dans `logs/metrics.jsonl`.
    - Sauvegarde un snapshot JSON dans `snapshots/for_review/` quand échec.
    - Définit dans le state: confidence, quality_pass, escalate
    """
    print("---EVALUATION DE LA RÉPONSE---")
    generation = state.get("generation", "") or state.get("generation_text", "")
    sources = state.get("sources", [])
    documents = state.get("documents", [])
    question = state.get("question", "")

    # Calcul des scores : brut (similarité) et ajusté (confiance)
    scores = [float(s.get("score", 0.0)) for s in sources] if sources else [0.0]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    similarity_score = round(avg_score, 3)  # Score de similarité brut
    confidence_score = round(avg_score * 0.8, 3)  # Score de confiance ajusté (×0.8)

    # vérification de citation par id ou chevauchement texte
    cited_ids = [s["id"] for s in sources if str(s.get("id")) in generation]

    def text_overlap(a: str, b: str) -> float:
        aw = {w for w in re.findall(r"\w{3,}", a.lower())}
        bw = {w for w in re.findall(r"\w{3,}", b.lower())}
        if not aw or not bw:
            return 0.0
        inter = aw & bw
        return len(inter) / max(1, min(len(aw), len(bw)))

    overlap_found = False
    for doc in documents:
        ov = text_overlap(doc, generation)
        if ov >= 0.06:  # seuil conservateur
            overlap_found = True
            break

    cites_ok = bool(cited_ids) or overlap_found

    # détection d'hallucination : années / montants présents dans la génération mais absents des docs
    doc_text = " ".join(documents).lower()
    years = re.findall(r"\b(19|20)\d{2}\b", generation)
    amounts = re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s?(?:€|\$|usd|eur)\b", generation, flags=re.IGNORECASE)
    hallucination = False
    for y in years:
        if str(y) not in doc_text:
            hallucination = True
            break
    if not hallucination:
        for a in amounts:
            if a.lower() not in doc_text:
                hallucination = True
                break

    # compute overlap ratio: proportion of docs whose first snippet appears in generation
    overlap_count = 0
    for doc in documents:
        snippet = doc[:200].strip()
        if snippet and snippet in generation:
            overlap_count += 1
    overlap_ratio = overlap_count / max(1, len(documents))

    # decision: accept if NOT hallucination AND confidence_score >= 0.35 AND (cites_ok OR overlap_ratio>=0.35)
    cites_ok = bool(cited_ids) or overlap_found
    quality_pass = (not hallucination) and (confidence_score >= 0.35) and (cites_ok or overlap_ratio >= 0.35)
    escalate = False
    if not quality_pass:
        escalate = (confidence_score < 0.25) or hallucination

    # metrics/log
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "similarity_score": similarity_score,
        "confidence_score": confidence_score,
        "cites_ok": cites_ok,
        "hallucination": hallucination,
        "quality_pass": quality_pass,
        "escalate": escalate,
        "num_sources": len(sources)
    }
    logs_dir = Path(project_root) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    metrics_file = logs_dir / "metrics.jsonl"
    with open(metrics_file, "a", encoding="utf-8") as mf:
        mf.write(json.dumps(metrics, ensure_ascii=False) + "\n")

    # save snapshot if failing for human review / audit
    if not quality_pass:
        snaps_dir = Path(project_root) / "snapshots" / "for_review"
        snaps_dir.mkdir(parents=True, exist_ok=True)
        snap_id = uuid.uuid4().hex
        snapshot = {
            "id": snap_id,
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "documents": documents,
            "sources": sources,
            "generation": generation,
            "metrics": metrics
        }
        snap_path = snaps_dir / f"{snap_id}.json"
        with open(snap_path, "w", encoding="utf-8") as sf:
            json.dump(snapshot, sf, ensure_ascii=False, indent=2)

        print(f"⚠️ Snapshot saved for review: {snap_path}")

    print(f" -> similarity={similarity_score:.3f}, confidence={confidence_score:.3f}, cites_ok={cites_ok}, hallucination={hallucination}, quality_pass={quality_pass}, escalate={escalate}")

    # persist additional metrics
    state["similarity_score"] = similarity_score
    state["confidence_score"] = confidence_score
    state["quality_pass"] = quality_pass
    state["escalate"] = escalate
    state["overlap_ratio"] = overlap_ratio
    state["cites_ok"] = cites_ok

    return {
        "quality_pass": quality_pass,
        "similarity_score": similarity_score,
        "confidence_score": confidence_score,
        "escalate": escalate,
        "cites_ok": cites_ok,
        "overlap_ratio": overlap_ratio,
        "hallucination": hallucination
    }


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

    # Préparer le contexte: construire un bloc contenant l'ID + extrait pour chaque source
    sources_block = []
    for s, doc in zip(sources, documents):
        sid = s.get("id")
        score = round(float(s.get("score", 0.0)), 3)
        # doc already formatted as '[Document i] (Score: x)\n<content>' - take content part
        excerpt = doc
        if len(excerpt) > 400:
            excerpt = excerpt[:400] + "..."
        sources_block.append(f"[{sid}] (score: {score})\n{excerpt}\n")

    context_text = "\n\n".join(sources_block) if sources_block else "\n\n".join(documents)

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
        dynamic_system = SYSTEM_PROMPT + \
            "\n\nLANGUE DÉTECTÉE: FR — Réponds UNIQUEMENT en français, ne mélange pas les langues."
        user_template_dynamic = USER_TEMPLATE

    # Créer le prompt avec le format OpenAI (system + user) + variables
    prompt = ChatPromptTemplate.from_messages([
        ("system", dynamic_system),
        ("user", user_template_dynamic)
    ])

    # Ancrage explicite: demander de citer les IDs des documents utilisés
    anchor_instruction_en = (
        "IMPORTANT: Use ONLY the documents listed below to answer. "
        "Cite the source by its ID (e.g. [<id>]) each time you use information from a document. "
        "If the information is not present, reply: 'I do not have enough information.' "
        "Do not invent dates, amounts or personal data."
    )
    anchor_instruction_fr = (
        "IMPORTANT: Utilisez UNIQUEMENT les documents listés ci-dessous pour répondre. "
        "Citez la source par son ID (ex: [<id>]) chaque fois que vous utilisez une information. "
        "Si l'information n'est pas présente, répondez: 'Je n'ai pas assez d'informations.' "
        "Ne pas inventer de dates, montants ou données personnelles."
    )

    if lang == "en":
        user_template_dynamic = anchor_instruction_en + "\n\n" + user_template_dynamic
    else:
        user_template_dynamic = anchor_instruction_fr + "\n\n" + user_template_dynamic

    # Initialiser le LLM (casts explicites)
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=float(getattr(config, "OPENAI_TEMPERATURE", 0.2)),
        top_p=float(getattr(config, "OPENAI_TOP_P", 0.9)),
        max_tokens=int(getattr(config, "OPENAI_MAX_TOKENS", 1024)),
        api_key=config.OPENAI_API_KEY
    )

    # Créer la chaîne
    chain = prompt | llm

    try:
        # Générer la réponse en passant le contexte construit (IDs + extraits)
        response = chain.invoke({
            "context": context_text,
            "question": question,
            "output_format": "text"
        })
        generation = response.content

        # Validation de langue et éventuelle 2e tentative stricte
        def _validate_lang(txt: str, expected: str) -> bool:
            detected = detect_language(txt)
            return detected == expected

        if not _validate_lang(generation, lang):
            print("⚠️ Langue de la réponse non conforme. Nouvelle tentative stricte...")
            if lang == "en":
                strict_system = dynamic_system + \
                    "\n\nHARD REQUIREMENT: Reply ONLY in English. If any non-English word appears, rewrite fully in English."
            else:
                strict_system = dynamic_system + \
                    "\n\nEXIGENCE FORTE: Réponds UNIQUEMENT en français. Si des mots non-français apparaissent, réécris intégralement en français."

            strict_prompt = ChatPromptTemplate.from_messages([
                ("system", strict_system),
                ("user", user_template_dynamic)
            ])
            strict_chain = strict_prompt | llm
            response2 = strict_chain.invoke({
                "context": context_text,
                "question": question,
                "output_format": "text"
            })
            generation2 = response2.content
            if _validate_lang(generation2, lang):
                generation = generation2

        print(f"✅ Réponse générée ({len(generation)} caractères)")
        print(f"Modèle: {config.OPENAI_MODEL}")

        # Detect cited IDs in the generation (for logging / evaluation)
        detected_ids = []
        for s in sources:
            sid = str(s.get("id", ""))
            if sid and sid in generation:
                detected_ids.append(sid)

        # Log LLM output for audit/debug
        try:
            logs_dir = Path(project_root) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            llm_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "question": question,
                "response_lang": lang,
                "detected_ids": detected_ids,
                "generation_trunc": generation[:1000],
                "num_sources": len(sources)
            }
            with open(logs_dir / "llm_responses.jsonl", "a", encoding="utf-8") as lf:
                lf.write(json.dumps(llm_log, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: could not write llm log: {e}")

        # conserver documents et sources dans l'état pour l'évaluation
        return {"generation": generation, "sources": sources, "response_lang": lang, "documents": documents}

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


def human_review(state):
    """Nœud d'escalade humaine: renvoie un message d'escalade et marque l'état.

    Le snapshot pour revue est enregistré dans evaluate_response, ici on renvoie
    un message lisible pour l'utilisateur et indique escalated=True.
    """
    print("---HUMAN REVIEW ESCALATION---")
    lang = detect_language(state.get("question", "") or "")
    if lang == "en":
        msg = (
            "We could not provide a confident automated answer. "
            "Your request has been escalated to our specialists. "
            "You will be contacted shortly."
        )
    else:
        msg = (
            "Nous ne pouvons pas fournir une réponse automatisée fiable. "
            "Votre demande a été transférée à nos spécialistes. "
            "Vous serez contacté(e) sous peu."
        )

    # Indicate escalation in the returned payload
    return {
        "generation": msg,
        "sources": state.get("sources", []),
        "response_lang": lang,
        "escalated": True,
    }


def decide_to_generate(state):
    """Détermine le chemin à suivre après l'évaluation."""
    return "generate" if state.get("grade") == "relevant" else "fallback"


workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve_documents)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate_answer)
workflow.add_node("evaluate_response", evaluate_response)
workflow.add_node("human_review", human_review)
workflow.add_node("fallback", fallback_response)

workflow.set_entry_point("retrieve")

workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {"generate": "generate", "fallback": "fallback"}
)
workflow.add_edge("generate", "evaluate_response")
# Routing: if quality_pass -> END, elif escalate -> human_review, else -> fallback
workflow.add_conditional_edges(
    "evaluate_response",
    lambda st: "end" if st.get("quality_pass") else ("human_review" if st.get("escalate") else "fallback"),
    {"end": END, "fallback": "fallback", "human_review": "human_review"}
)
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
