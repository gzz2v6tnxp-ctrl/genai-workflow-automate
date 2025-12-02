"""
COV-RAG Graph: Workflow LangGraph pour RAG avec Chain-of-Verification

Ce module intègre le système COV-RAG dans un workflow LangGraph
pour une orchestration robuste avec vérification des hallucinations.

Pipeline:
1. retrieve_with_rerank: Récupération hybride + re-ranking
2. generate_initial: Génération avec ancrage strict
3. extract_claims: Extraction des affirmations vérifiables
4. verify_claims: Vérification CoVE contre les sources
5. correct_if_needed: Correction des hallucinations détectées
6. evaluate_final: Évaluation qualité finale

Auteur: GenAI Workflow Automation
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from langgraph.graph import END, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from agents.state import COVRAGGraphState
from agents.cov_rag import COVRAGRetriever, ChainOfVerification
from scripts import config


# ============================================================================
# DÉTECTION DE LANGUE
# ============================================================================

FRENCH_MARKERS = {
    "carte", "bancaire", "compte", "problème", "bonjour", "merci", 
    "solde", "crédit", "bloquée", "facturation", "opposition",
    "comment", "pourquoi", "quand", "combien", "quel", "quelle"
}


def detect_language(text: str) -> str:
    """Détecte la langue (fr/en) de manière robuste."""
    lower = text.lower()
    
    # Vérifier les accents français
    if re.search(r"[àâçéèêëîïôùûüÿœ]", lower):
        return "fr"
    
    # Vérifier les mots français
    hits = sum(1 for w in FRENCH_MARKERS if w in lower)
    if hits >= 2:
        return "fr"
    
    return "en"


# ============================================================================
# NŒUDS DU GRAPHE COV-RAG
# ============================================================================

# Initialisation globale (lazy loading)
_retriever: Optional[COVRAGRetriever] = None
_llm: Optional[ChatOpenAI] = None
_cove: Optional[ChainOfVerification] = None


def _get_retriever(collection_name: str = "demo_public") -> COVRAGRetriever:
    """Récupère ou initialise le retriever."""
    global _retriever
    if _retriever is None or _retriever.collection_name != collection_name:
        _retriever = COVRAGRetriever(
            collection_name=collection_name,
            use_cloud=True,
            top_k=5,
            score_threshold=0.35
        )
    return _retriever


def _get_llm() -> ChatOpenAI:
    """Récupère ou initialise le LLM."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=float(getattr(config, "OPENAI_TEMPERATURE", 0.2)),
            max_tokens=int(getattr(config, "OPENAI_MAX_TOKENS", 1024)),
            api_key=config.OPENAI_API_KEY
        )
    return _llm


def _get_cove(collection_name: str = "demo_public") -> ChainOfVerification:
    """Récupère ou initialise le module CoVE."""
    global _cove
    if _cove is None:
        _cove = ChainOfVerification(
            llm=_get_llm(),
            retriever=_get_retriever(collection_name),
            verification_threshold=0.7,
            max_claims_to_verify=5
        )
    return _cove


# ----------------------------------------------------------------------------
# Nœud 1: Récupération avec Re-ranking
# ----------------------------------------------------------------------------

def retrieve_with_rerank(state: COVRAGGraphState) -> Dict[str, Any]:
    """
    Récupère les documents avec recherche hybride et re-ranking.
    
    Étapes:
    1. Récupération hybride (dense + MMR)
    2. Re-ranking par pertinence
    3. Formatage pour le contexte
    """
    print("---[1] RÉCUPÉRATION + RE-RANKING---")
    
    question = state["question"]
    collection = state.get("collection", "demo_public")
    sources_filter = state.get("sources_filter")
    
    print(f"Question: {question}")
    print(f"Collection: {collection}")
    
    try:
        retriever = _get_retriever(collection)
        
        # Construire les filtres
        filters = None
        if collection == "knowledge_base_main" and sources_filter:
            allowed = {"synth", "cfpb", "enron"}
            filtered_values = [s for s in sources_filter if s in allowed]
            if filtered_values:
                filters = {"source": filtered_values}
        
        # Récupération hybride
        docs = retriever.hybrid_retrieve(question, filters)
        
        if not docs:
            print("⚠️ Aucun document trouvé")
            return {
                "documents": [],
                "sources": [],
                "reranked_documents": [],
                "reranked_sources": [],
                "grade": "not_relevant"
            }
        
        # Re-ranking
        reranked_docs = retriever.rerank(question, docs)
        
        # Formatage
        documents = []
        sources = []
        reranked_documents = []
        reranked_sources = []
        
        for i, doc in enumerate(reranked_docs, 1):
            score = doc.metadata.get("score", 0.0)
            doc_id = doc.metadata.get("id", f"doc_{i}")
            
            doc_text = f"[{doc_id}] (Score: {score:.3f})\n{doc.page_content}"
            documents.append(doc_text)
            reranked_documents.append(doc_text)
            
            source_info = {
                "id": doc_id,
                "score": score,
                "source": doc.metadata.get("source", "unknown"),
                "lang": doc.metadata.get("lang", "unknown"),
                "content_preview": doc.page_content[:200]
            }
            sources.append(source_info)
            reranked_sources.append(source_info)
        
        print(f"✅ {len(documents)} document(s) récupérés et re-classés")
        print(f"Scores: {reranked_docs[0].metadata.get('score', 0):.3f} - {reranked_docs[-1].metadata.get('score', 0):.3f}")
        
        # Évaluer la pertinence
        best_score = sources[0]["score"] if sources else 0
        grade = "relevant" if best_score >= 0.5 else ("marginal" if best_score >= 0.35 else "not_relevant")
        
        return {
            "documents": documents,
            "sources": sources,
            "reranked_documents": reranked_documents,
            "reranked_sources": reranked_sources,
            "grade": grade,
            "similarity_score": best_score
        }
        
    except Exception as e:
        print(f"❌ Erreur récupération: {e}")
        return {
            "documents": [],
            "sources": [],
            "reranked_documents": [],
            "reranked_sources": [],
            "grade": "not_relevant",
            "error": str(e)
        }


# ----------------------------------------------------------------------------
# Nœud 2: Génération Initiale avec Ancrage
# ----------------------------------------------------------------------------

def generate_initial(state: COVRAGGraphState) -> Dict[str, Any]:
    """
    Génère la réponse initiale avec ancrage strict sur les sources.
    """
    print("---[2] GÉNÉRATION INITIALE---")
    
    question = state["question"]
    documents = state.get("reranked_documents", state.get("documents", []))
    sources = state.get("reranked_sources", state.get("sources", []))
    
    if not documents:
        return {"generation": "", "initial_generation": ""}
    
    # Détecter la langue
    lang = detect_language(question)
    print(f"Langue détectée: {lang}")
    
    # Construire le contexte avec IDs
    context_parts = []
    for doc, src in zip(documents, sources):
        doc_id = src.get("id", "unknown")
        score = src.get("score", 0.0)
        # Extraire le contenu sans le header
        content = doc.split("\n", 1)[-1] if "\n" in doc else doc
        context_parts.append(f"[{doc_id}] (score: {score:.3f})\n{content[:600]}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Prompt avec ancrage strict
    if lang == "fr":
        system_prompt = """Tu es un assistant bancaire professionnel.

RÈGLES D'ANCRAGE STRICTES:
1. Utilise UNIQUEMENT les informations des documents fournis
2. Cite TOUJOURS la source [ID] quand tu utilises une information  
3. Si l'information n'est pas dans les sources, dis-le clairement
4. NE PAS inventer de dates, montants, numéros ou données
5. Reste factuel et précis

Réponds de manière professionnelle et empathique."""
        
        user_template = """Documents sources:
{context}

Question: {question}

Réponds en français en citant les sources [ID] utilisées."""
    else:
        system_prompt = """You are a professional banking assistant.

STRICT GROUNDING RULES:
1. Use ONLY information from the provided documents
2. ALWAYS cite the source [ID] when using information
3. If information is not in sources, say so clearly
4. DO NOT invent dates, amounts, numbers or data
5. Stay factual and precise

Respond professionally and empathetically."""
        
        user_template = """Source documents:
{context}

Question: {question}

Reply in English, citing sources [ID] used."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_template)
    ])
    
    llm = _get_llm()
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "context": context,
            "question": question
        })
        generation = response.content
        
        print(f"✅ Réponse générée ({len(generation)} caractères)")
        
        return {
            "generation": generation,
            "initial_generation": generation,
            "response_lang": lang
        }
        
    except Exception as e:
        print(f"❌ Erreur génération: {e}")
        fallback = (
            "Désolé, une erreur s'est produite." if lang == "fr"
            else "Sorry, an error occurred."
        )
        return {
            "generation": fallback,
            "initial_generation": fallback,
            "response_lang": lang,
            "error": str(e)
        }


# ----------------------------------------------------------------------------
# Nœud 3: Extraction des Affirmations (CoVE Step 1)
# ----------------------------------------------------------------------------

def extract_claims(state: COVRAGGraphState) -> Dict[str, Any]:
    """
    Extrait les affirmations vérifiables de la réponse générée.
    """
    print("---[3] EXTRACTION DES AFFIRMATIONS---")
    
    generation = state.get("generation", "")
    cove_enabled = state.get("cove_enabled", True)
    
    if not cove_enabled or not generation:
        return {"claims_extracted": [], "cove_enabled": cove_enabled}
    
    llm = _get_llm()
    
    extract_prompt = ChatPromptTemplate.from_messages([
        ("system", """Extrais les affirmations factuelles vérifiables de cette réponse.

Pour chaque affirmation:
- Le fait précis énoncé
- La catégorie: "numerical", "temporal", "entity", "factual"

Retourne UNIQUEMENT un tableau JSON:
[{"fact": "...", "category": "..."}, ...]

Ignore les conseils généraux et formulations vagues."""),
        ("human", "Réponse:\n{response}")
    ])
    
    chain = extract_prompt | llm
    
    try:
        result = chain.invoke({"response": generation})
        content = result.content.strip()
        
        # Nettoyer le JSON
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Trouver le tableau JSON
        start = content.find('[')
        end = content.rfind(']')
        if start != -1 and end != -1:
            content = content[start:end + 1]
        
        claims = json.loads(content)
        
        print(f"✅ {len(claims)} affirmation(s) extraite(s)")
        
        return {"claims_extracted": claims[:5]}  # Limiter à 5
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Erreur extraction (fallback): {e}")
        
        # Fallback: extraction basée sur des règles
        claims = []
        sentences = re.split(r'[.!?]\s+', generation)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Ignorer les phrases génériques
            if re.search(r'^(je|vous|nous|voici|n\'hésitez)', sentence, re.I):
                continue
            
            category = "factual"
            if re.search(r'\b\d+[,.]?\d*\s*[€$%]', sentence):
                category = "numerical"
            elif re.search(r'\b(19|20)\d{2}\b', sentence):
                category = "temporal"
            
            claims.append({"fact": sentence, "category": category})
        
        return {"claims_extracted": claims[:5]}


# ----------------------------------------------------------------------------
# Nœud 4: Vérification des Affirmations (CoVE Step 2-3)
# ----------------------------------------------------------------------------

def verify_claims(state: COVRAGGraphState) -> Dict[str, Any]:
    """
    Vérifie chaque affirmation contre les sources.
    """
    print("---[4] VÉRIFICATION CoVE---")
    
    claims = state.get("claims_extracted", [])
    documents = state.get("reranked_documents", state.get("documents", []))
    sources = state.get("reranked_sources", state.get("sources", []))
    cove_enabled = state.get("cove_enabled", True)
    
    if not cove_enabled or not claims:
        return {
            "verification_results": [],
            "hallucination_detected": False,
            "cove_confidence": 1.0
        }
    
    llm = _get_llm()
    
    # Préparer le texte des sources
    sources_text = "\n\n---\n\n".join([
        f"[{src.get('id', i)}]\n{doc}"
        for i, (doc, src) in enumerate(zip(documents, sources))
    ])
    
    verify_prompt = ChatPromptTemplate.from_messages([
        ("system", """Vérifie si l'affirmation est correcte selon les sources.

RÈGLES:
1. "is_verified": true SEULEMENT si explicitement supporté par les sources
2. Si l'info n'est pas dans les sources: is_verified = false
3. Pour chiffres/dates: doivent correspondre exactement
4. Cite l'evidence exacte

Retourne UNIQUEMENT un objet JSON:
{{"is_verified": true/false, "confidence": 0.0-1.0, "evidence": "...", "correction": "..." ou null}}"""),
        ("human", """Affirmation: {claim}

Sources:
{sources}""")
    ])
    
    chain = verify_prompt | llm
    
    verification_results = []
    hallucination_detected = False
    
    for claim_data in claims:
        claim = claim_data.get("fact", str(claim_data))
        
        try:
            result = chain.invoke({
                "claim": claim,
                "sources": sources_text
            })
            
            content = result.content.strip()
            # Nettoyer
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                content = content[start:end + 1]
            
            verification = json.loads(content)
            
            verification_results.append({
                "claim": claim,
                "is_verified": verification.get("is_verified", False),
                "confidence": verification.get("confidence", 0.5),
                "evidence": verification.get("evidence", ""),
                "correction": verification.get("correction")
            })
            
            if not verification.get("is_verified", False):
                hallucination_detected = True
                
        except Exception as e:
            print(f"⚠️ Erreur vérification claim: {e}")
            verification_results.append({
                "claim": claim,
                "is_verified": False,
                "confidence": 0.3,
                "evidence": "Vérification impossible",
                "correction": None
            })
            hallucination_detected = True
    
    # Calculer la confiance CoVE
    if verification_results:
        verified_count = sum(1 for v in verification_results if v["is_verified"])
        cove_confidence = verified_count / len(verification_results)
    else:
        cove_confidence = 1.0
    
    print(f"✅ Vérification: {sum(1 for v in verification_results if v['is_verified'])}/{len(verification_results)}")
    print(f"Hallucination détectée: {hallucination_detected}")
    
    return {
        "verification_results": verification_results,
        "hallucination_detected": hallucination_detected,
        "cove_confidence": cove_confidence
    }


# ----------------------------------------------------------------------------
# Nœud 5: Correction si Nécessaire (CoVE Step 4)
# ----------------------------------------------------------------------------

def correct_if_needed(state: COVRAGGraphState) -> Dict[str, Any]:
    """
    Corrige la réponse si des hallucinations ont été détectées.
    """
    print("---[5] CORRECTION (si nécessaire)---")
    
    hallucination_detected = state.get("hallucination_detected", False)
    verification_results = state.get("verification_results", [])
    initial_generation = state.get("initial_generation", "")
    generation = state.get("generation", "")
    documents = state.get("reranked_documents", state.get("documents", []))
    question = state["question"]
    lang = state.get("response_lang", "fr")
    
    # Compter les corrections nécessaires
    needs_correction = any(not v["is_verified"] for v in verification_results)
    
    if not needs_correction:
        print("✅ Aucune correction nécessaire")
        return {
            "generation": generation,
            "corrections_made": 0
        }
    
    print("⚠️ Correction en cours...")
    
    llm = _get_llm()
    
    # Formater les résultats de vérification
    results_text = "\n".join([
        f"- \"{v['claim'][:100]}...\"\n"
        f"  Vérifié: {'✅' if v['is_verified'] else '❌'} (confiance: {v['confidence']:.0%})\n"
        f"  Correction: {v['correction'] or 'N/A'}"
        for v in verification_results
    ])
    
    sources_text = "\n\n".join(documents[:3])
    
    if lang == "fr":
        system_prompt = """Corrige la réponse en tenant compte des vérifications.

RÈGLES:
1. Conserve les parties vérifiées correctes
2. Corrige ou supprime les affirmations incorrectes
3. Ne rajoute PAS de nouvelles informations
4. Maintiens un ton professionnel
5. Cite les sources quand approprié"""
    else:
        system_prompt = """Correct the response based on verifications.

RULES:
1. Keep verified correct parts
2. Fix or remove incorrect claims
3. Do NOT add new information
4. Maintain professional tone
5. Cite sources when appropriate"""
    
    correct_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Question: {question}

Réponse initiale:
{initial_response}

Résultats de vérification:
{verification_results}

Sources:
{sources}

Génère la réponse corrigée:""")
    ])
    
    chain = correct_prompt | llm
    
    try:
        result = chain.invoke({
            "question": question,
            "initial_response": initial_generation,
            "verification_results": results_text,
            "sources": sources_text
        })
        
        corrected = result.content
        corrections_made = sum(1 for v in verification_results if not v["is_verified"])
        
        print(f"✅ {corrections_made} correction(s) appliquée(s)")
        
        return {
            "generation": corrected,
            "corrections_made": corrections_made
        }
        
    except Exception as e:
        print(f"❌ Erreur correction: {e}")
        return {
            "generation": generation,
            "corrections_made": 0,
            "error": str(e)
        }


# ----------------------------------------------------------------------------
# Nœud 6: Évaluation Finale
# ----------------------------------------------------------------------------

def evaluate_final(state: COVRAGGraphState) -> Dict[str, Any]:
    """
    Évalue la qualité finale de la réponse.
    """
    print("---[6] ÉVALUATION FINALE---")
    
    generation = state.get("generation", "")
    documents = state.get("documents", [])
    sources = state.get("sources", [])
    verification_results = state.get("verification_results", [])
    cove_confidence = state.get("cove_confidence", 1.0)
    similarity_score = state.get("similarity_score", 0.0)
    question = state.get("question", "")
    
    # Score de similarité des sources
    scores = [float(s.get("score", 0.0)) for s in sources] if sources else [0.0]
    avg_similarity = sum(scores) / len(scores) if scores else 0.0
    
    # Vérification des citations
    doc_text = " ".join(documents).lower()
    cited_ids = []
    for s in sources:
        sid = str(s.get("id", ""))
        if sid and sid in generation:
            cited_ids.append(sid)
    cites_ok = len(cited_ids) > 0
    
    # Détection d'hallucination basique (dates/montants)
    years = re.findall(r"\b(19|20)\d{2}\b", generation)
    amounts = re.findall(r"\b\d+[,.]?\d*\s*[€$]\b", generation, re.I)
    
    basic_hallucination = False
    for y in years:
        if y not in doc_text:
            basic_hallucination = True
            break
    
    # Score de confiance final
    # Combinaison: 40% similarité, 40% CoVE, 20% citations
    confidence_score = (
        0.4 * avg_similarity +
        0.4 * cove_confidence +
        0.2 * (1.0 if cites_ok else 0.5)
    )
    
    # Décision qualité
    hallucination_detected = state.get("hallucination_detected", False) or basic_hallucination
    quality_pass = (
        not hallucination_detected and
        confidence_score >= 0.4 and
        (cites_ok or cove_confidence >= 0.7)
    )
    
    escalate = confidence_score < 0.3 or (hallucination_detected and cove_confidence < 0.5)
    
    # Log des métriques
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "similarity_score": round(avg_similarity, 3),
        "cove_confidence": round(cove_confidence, 3),
        "final_confidence": round(confidence_score, 3),
        "cites_ok": cites_ok,
        "hallucination_detected": hallucination_detected,
        "quality_pass": quality_pass,
        "escalate": escalate,
        "corrections_made": state.get("corrections_made", 0),
        "num_sources": len(sources),
        "num_verifications": len(verification_results)
    }
    
    # Sauvegarder les métriques
    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    with open(logs_dir / "cov_rag_metrics.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")
    
    # Sauvegarder snapshot si échec
    if not quality_pass:
        snaps_dir = project_root / "snapshots" / "for_review"
        snaps_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot = {
            "id": uuid.uuid4().hex,
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "generation": generation,
            "initial_generation": state.get("initial_generation", ""),
            "verification_results": verification_results,
            "metrics": metrics
        }
        
        snap_path = snaps_dir / f"{snapshot['id']}.json"
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
        print(f"⚠️ Snapshot saved: {snap_path.name}")
    
    print(f"📊 Confiance finale: {confidence_score:.0%}")
    print(f"   Quality pass: {quality_pass}, Escalate: {escalate}")
    
    return {
        "similarity_score": avg_similarity,
        "confidence_score": confidence_score,
        "final_confidence": confidence_score,
        "quality_pass": quality_pass,
        "escalate": escalate,
        "cites_ok": cites_ok,
        "hallucination_detected": hallucination_detected
    }


# ----------------------------------------------------------------------------
# Nœud: Fallback
# ----------------------------------------------------------------------------

def fallback_response(state: COVRAGGraphState) -> Dict[str, Any]:
    """Réponse de secours si pas de documents pertinents."""
    print("---FALLBACK---")
    
    question = state.get("question", "")
    lang = detect_language(question)
    
    if lang == "fr":
        generation = (
            "Je n'ai pas trouvé d'informations suffisamment pertinentes pour répondre "
            "à votre question de manière fiable. Je vous recommande de contacter "
            "notre service client pour une assistance personnalisée."
        )
    else:
        generation = (
            "I couldn't find sufficiently relevant information to answer your question "
            "reliably. I recommend contacting our customer service for personalized assistance."
        )
    
    return {
        "generation": generation,
        "sources": [],
        "response_lang": lang,
        "quality_pass": False,
        "confidence_score": 0.0
    }


# ----------------------------------------------------------------------------
# Nœud: Human Review Escalation
# ----------------------------------------------------------------------------

def human_review(state: COVRAGGraphState) -> Dict[str, Any]:
    """Escalade vers revue humaine."""
    print("---HUMAN REVIEW ESCALATION---")
    
    question = state.get("question", "")
    lang = detect_language(question)
    
    if lang == "fr":
        msg = (
            "Nous ne pouvons pas fournir une réponse automatisée suffisamment fiable. "
            "Votre demande a été transférée à nos spécialistes qui vous contacteront sous peu."
        )
    else:
        msg = (
            "We cannot provide a sufficiently reliable automated response. "
            "Your request has been escalated to our specialists who will contact you shortly."
        )
    
    return {
        "generation": msg,
        "escalated": True,
        "response_lang": lang
    }


# ============================================================================
# CONSTRUCTION DU GRAPHE
# ============================================================================

def decide_after_retrieval(state: COVRAGGraphState) -> str:
    """Décide le chemin après la récupération."""
    grade = state.get("grade", "not_relevant")
    if grade == "relevant":
        return "generate"
    elif grade == "marginal":
        return "generate"  # Tenter quand même
    else:
        return "fallback"


def decide_after_evaluation(state: COVRAGGraphState) -> str:
    """Décide le chemin après l'évaluation finale."""
    quality_pass = state.get("quality_pass", False)
    escalate = state.get("escalate", False)
    
    if quality_pass:
        return "end"
    elif escalate:
        return "human_review"
    else:
        return "end"  # Retourner quand même la réponse (avec warning)


def build_cov_rag_graph(enable_cove: bool = True) -> StateGraph:
    """
    Construit le graphe COV-RAG.
    
    Args:
        enable_cove: Active/désactive la vérification CoVE
        
    Returns:
        StateGraph compilé
    """
    workflow = StateGraph(COVRAGGraphState)
    
    # Ajouter les nœuds
    workflow.add_node("retrieve", retrieve_with_rerank)
    workflow.add_node("generate", generate_initial)
    workflow.add_node("fallback", fallback_response)
    workflow.add_node("human_review", human_review)
    workflow.add_node("evaluate", evaluate_final)
    
    if enable_cove:
        workflow.add_node("extract_claims", extract_claims)
        workflow.add_node("verify_claims", verify_claims)
        workflow.add_node("correct", correct_if_needed)
    
    # Point d'entrée
    workflow.set_entry_point("retrieve")
    
    # Arêtes conditionnelles après récupération
    workflow.add_conditional_edges(
        "retrieve",
        decide_after_retrieval,
        {
            "generate": "generate",
            "fallback": "fallback"
        }
    )
    
    # Pipeline CoVE ou direct vers évaluation
    if enable_cove:
        workflow.add_edge("generate", "extract_claims")
        workflow.add_edge("extract_claims", "verify_claims")
        workflow.add_edge("verify_claims", "correct")
        workflow.add_edge("correct", "evaluate")
    else:
        workflow.add_edge("generate", "evaluate")
    
    # Décision après évaluation
    workflow.add_conditional_edges(
        "evaluate",
        decide_after_evaluation,
        {
            "end": END,
            "human_review": "human_review"
        }
    )
    
    # Terminaisons
    workflow.add_edge("fallback", END)
    workflow.add_edge("human_review", END)
    
    return workflow.compile()


# Graphes pré-compilés
cov_rag_app = build_cov_rag_graph(enable_cove=True)
rag_app = build_cov_rag_graph(enable_cove=False)


# ============================================================================
# API SIMPLIFIÉE
# ============================================================================

def run_cov_rag(
    question: str,
    collection: str = "demo_public",
    sources_filter: List[str] = None,
    enable_cove: bool = True
) -> Dict[str, Any]:
    """
    Exécute le pipeline COV-RAG de manière synchrone.
    
    Args:
        question: Question de l'utilisateur
        collection: Collection Qdrant à interroger
        sources_filter: Filtres optionnels sur les sources
        enable_cove: Active la vérification CoVE
        
    Returns:
        Dict avec la réponse et les métriques
    """
    initial_state = {
        "question": question,
        "collection": collection,
        "sources_filter": sources_filter or [],
        "cove_enabled": enable_cove
    }
    
    app = cov_rag_app if enable_cove else rag_app
    
    final_state = {}
    for output in app.stream(initial_state):
        for key, value in output.items():
            final_state.update(value)
    
    return {
        "answer": final_state.get("generation", ""),
        "sources": final_state.get("sources", []),
        "confidence": final_state.get("final_confidence", final_state.get("confidence_score", 0.0)),
        "quality_pass": final_state.get("quality_pass", False),
        "hallucination_detected": final_state.get("hallucination_detected", False),
        "corrections_made": final_state.get("corrections_made", 0),
        "language": final_state.get("response_lang", "fr"),
        "escalated": final_state.get("escalated", False)
    }


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 TEST COV-RAG GRAPH")
    print("=" * 70)
    
    tests = [
        {"question": "Ma carte bancaire est bloquée, que dois-je faire ?", "lang": "FR"},
        {"question": "How can I dispute an unauthorized transaction?", "lang": "EN"}
    ]
    
    for idx, test in enumerate(tests, 1):
        print(f"\n{'='*70}")
        print(f"📝 TEST {idx}: {test['lang']} - {test['question']}")
        print("=" * 70)
        
        result = run_cov_rag(
            question=test["question"],
            collection="demo_public",
            enable_cove=True
        )
        
        print("\n📊 RÉSULTATS:")
        print(f"  Confiance: {result['confidence']:.0%}")
        print(f"  Quality pass: {result['quality_pass']}")
        print(f"  Hallucination: {result['hallucination_detected']}")
        print(f"  Corrections: {result['corrections_made']}")
        print(f"  Sources: {len(result['sources'])}")
        
        print("\n💬 RÉPONSE:")
        answer = result['answer']
        print(answer[:500] + "..." if len(answer) > 500 else answer)
    
    print("\n" + "=" * 70)
    print("✅ Tests terminés")
    print("=" * 70)
