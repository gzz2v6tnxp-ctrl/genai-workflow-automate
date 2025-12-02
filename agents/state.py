from typing import List, TypedDict, Optional, Dict, Any
from dataclasses import dataclass, field


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
    similarity_score: float
    confidence_score: float
    quality_pass: bool
    escalate: bool
    overlap_ratio: float
    cites_ok: bool
    # Nouveaux champs pour COV-RAG
    initial_generation: str  # Réponse avant vérification CoVE
    hallucination_detected: bool
    verification_results: List[Dict[str, Any]]
    corrections_made: int
    cove_enabled: bool


# ============================================================================
# STRUCTURES DE DONNÉES POUR COV-RAG
# ============================================================================

@dataclass
class VerificationState:
    """État de vérification CoVE pour le suivi des hallucinations."""
    claims_extracted: List[str] = field(default_factory=list)
    questions_generated: List[str] = field(default_factory=list)
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 1.0
    corrections_made: int = 0
    hallucination_detected: bool = False
    
    def add_verification(self, claim: str, is_verified: bool, confidence: float, 
                         evidence: str = "", correction: str = None):
        """Ajoute un résultat de vérification."""
        self.verification_results.append({
            "claim": claim,
            "is_verified": is_verified,
            "confidence": confidence,
            "evidence": evidence,
            "correction": correction
        })
        if not is_verified:
            self.hallucination_detected = True
            if correction:
                self.corrections_made += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'état de vérification."""
        total = len(self.verification_results)
        verified = sum(1 for v in self.verification_results if v["is_verified"])
        return {
            "total_claims": total,
            "verified_claims": verified,
            "verification_rate": verified / total if total > 0 else 1.0,
            "hallucination_detected": self.hallucination_detected,
            "corrections_made": self.corrections_made,
            "avg_confidence": (
                sum(v["confidence"] for v in self.verification_results) / total
                if total > 0 else 1.0
            )
        }


@dataclass 
class RAGState:
    """État complet du système RAG avec métriques."""
    query: str = ""
    retrieved_docs: List[Dict[str, Any]] = field(default_factory=list)
    reranked_docs: List[Dict[str, Any]] = field(default_factory=list)
    initial_response: Optional[str] = None
    final_response: Optional[str] = None
    verification: VerificationState = field(default_factory=VerificationState)
    sources_cited: List[str] = field(default_factory=list)
    language: str = "fr"
    processing_time_ms: float = 0.0
    
    # Scores et métriques
    retrieval_score: float = 0.0
    confidence_score: float = 0.0
    quality_pass: bool = False
    escalate: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'état en dictionnaire pour sérialisation."""
        return {
            "query": self.query,
            "num_docs_retrieved": len(self.retrieved_docs),
            "num_docs_reranked": len(self.reranked_docs),
            "has_initial_response": self.initial_response is not None,
            "has_final_response": self.final_response is not None,
            "verification_summary": self.verification.get_summary(),
            "sources_cited": self.sources_cited,
            "language": self.language,
            "processing_time_ms": self.processing_time_ms,
            "retrieval_score": self.retrieval_score,
            "confidence_score": self.confidence_score,
            "quality_pass": self.quality_pass,
            "escalate": self.escalate
        }


class COVRAGGraphState(TypedDict, total=False):
    """
    État étendu pour le graphe COV-RAG avec vérification des hallucinations.
    
    Inclut tous les champs de GraphState plus les champs spécifiques CoVE.
    """
    # Champs de base (hérités de GraphState)
    question: str
    generation: str
    documents: List[str]
    sources: List[Dict[str, Any]]
    grade: str
    collection: str
    sources_filter: List[str]
    response_lang: str
    
    # Champs de scoring
    similarity_score: float
    confidence_score: float
    quality_pass: bool
    escalate: bool
    overlap_ratio: float
    cites_ok: bool
    
    # Champs COV-RAG spécifiques
    initial_generation: str
    reranked_documents: List[str]
    reranked_sources: List[Dict[str, Any]]
    
    # Champs CoVE (Chain-of-Verification)
    cove_enabled: bool
    claims_extracted: List[Dict[str, Any]]
    verification_questions: List[Dict[str, Any]]
    verification_results: List[Dict[str, Any]]
    hallucination_detected: bool
    corrections_made: int
    cove_confidence: float
    
    # Métriques finales
    final_confidence: float
    processing_time_ms: float
    error: str
