from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
import os
import time
import json
import hashlib
import sys
from pathlib import Path

# Assurer l'accès aux modules internes
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# LAZY LOADING: Les workflows RAG sont chargés uniquement à la première requête
# Cela économise ~200-300 Mo de RAM au démarrage
_rag_app = None
_cov_rag_app = None


def get_rag_app():
    """Charge le workflow RAG standard de manière lazy (à la demande)."""
    global _rag_app
    if _rag_app is None:
        print("[LazyLoader] Chargement du workflow RAG standard...")
        from agents.graph import app
        _rag_app = app
        print("[LazyLoader] Workflow RAG standard chargé.")
    return _rag_app


def get_cov_rag_app():
    """Charge le workflow COV-RAG (avec CoVE) de manière lazy."""
    global _cov_rag_app
    if _cov_rag_app is None:
        print("[LazyLoader] Chargement du workflow COV-RAG...")
        from agents.cov_rag_graph import cov_rag_app
        _cov_rag_app = cov_rag_app
        print("[LazyLoader] Workflow COV-RAG chargé.")
    return _cov_rag_app

# Cache Redis (optionnel) avec fallback local en mémoire
try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class LocalTTLCache:
    def __init__(self, ttl: int = 600, maxsize: int = 1000):
        self.ttl = ttl
        self.maxsize = maxsize
        self._store: Dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        ts, val = item
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, val: str):
        if len(self._store) >= self.maxsize:
            # Eviction naïve: supprimer le plus ancien
            oldest = sorted(self._store.items(), key=lambda x: x[1][0])[0][0]
            self._store.pop(oldest, None)
        self._store[key] = (time.time(), val)


def _get_redis_client():
    if not redis:
        return None
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis.Redis.from_url(url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


_redis = _get_redis_client()
_local_cache = LocalTTLCache(ttl=int(os.getenv("REDIS_TTL", "600")))

router = APIRouter(prefix="/api/v1/chatbot", tags=["Chatbot"])

class ChatQuery(BaseModel):
    question: str = Field(..., min_length=3, description="Question utilisateur")
    collection: Optional[str] = Field("demo_public", description="Nom de la collection Qdrant")
    output_format: Optional[str] = Field("text", pattern="^(text|json)$", description="Format de sortie souhaité")
    sources_filter: Optional[List[str]] = Field(None, description="Filtre de sources: subset de ['synth','cfpb','enron']")
    enable_cove: Optional[bool] = Field(True, description="Activer Chain-of-Verification (CoVE) pour réduire les hallucinations")


class SourceInfo(BaseModel):
    id: Any
    score: float
    source: str
    lang: str
    type: str


class VerificationInfo(BaseModel):
    """Informations sur la vérification CoVE d'une affirmation."""
    claim: str
    is_verified: bool
    confidence: float
    evidence: Optional[str] = None
    correction: Optional[str] = None


class ChatResponse(BaseModel):
    question: str
    answer: str
    language: str
    similarity_score: float  # Score de similarité brut (0-1)
    confidence_score: float  # Score de confiance ajusté
    sources: List[SourceInfo]
    mode: str
    # Quality evaluation fields
    quality_pass: Optional[bool] = None
    escalate: Optional[bool] = None
    cites_ok: Optional[bool] = None
    overlap_ratio: Optional[float] = None
    hallucination: Optional[bool] = None
    # COV-RAG specific fields
    cove_enabled: Optional[bool] = None
    hallucination_detected: Optional[bool] = None
    corrections_made: Optional[int] = None
    verifications: Optional[List[VerificationInfo]] = None
    initial_answer: Optional[str] = None  # Réponse avant correction CoVE

@router.post("/query", response_model=ChatResponse)
async def query_chatbot(payload: ChatQuery):
    """
    Interroge le workflow RAG pour une question utilisateur.
    
    Deux modes disponibles:
    - enable_cove=True (défaut): Utilise COV-RAG avec Chain-of-Verification pour réduire les hallucinations
    - enable_cove=False: Utilise le workflow RAG standard (plus rapide mais moins robuste)
    """
    try:
        # Log reçu (debug)
        try:
            print(f"[chatbot] received payload: collection={payload.collection} sources_filter={payload.sources_filter} enable_cove={payload.enable_cove}")
        except Exception:
            pass

        # Clé de cache (inclure enable_cove)
        sf = ",".join(sorted(payload.sources_filter)) if payload.sources_filter else ""
        cove_flag = "cove" if payload.enable_cove else "std"
        key_base = f"{payload.collection}:{sf}:{payload.output_format}:{cove_flag}:{payload.question.strip().lower()}"
        cache_key = "chat:" + hashlib.sha256(key_base.encode("utf-8")).hexdigest()

        # Tentative de cache
        ttl = int(os.getenv("REDIS_TTL", "600"))
        cached_json = None
        if _redis:
            try:
                cached_json = _redis.get(cache_key)
            except Exception:
                cached_json = None
        if cached_json is None:
            cached_json = _local_cache.get(cache_key)

        if cached_json:
            try:
                data = json.loads(cached_json)
                return ChatResponse(**data)
            except Exception:
                pass

        # Choisir le workflow selon enable_cove
        if payload.enable_cove:
            return await _run_cov_rag_pipeline(payload, cache_key, ttl)
        else:
            return await _run_standard_rag_pipeline(payload, cache_key, ttl)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_cov_rag_pipeline(payload: ChatQuery, cache_key: str, ttl: int) -> ChatResponse:
    """
    Exécute le pipeline COV-RAG avec Chain-of-Verification.
    
    Ce pipeline vérifie les affirmations générées contre les sources
    pour détecter et corriger les hallucinations.
    """
    print("[chatbot] Using COV-RAG pipeline with Chain-of-Verification")
    
    cov_rag_app = get_cov_rag_app()
    
    # État initial pour COV-RAG
    initial_state = {
        "question": payload.question,
        "collection": payload.collection,
        "sources_filter": payload.sources_filter or [],
        "cove_enabled": True
    }
    
    # Collecter les sorties du workflow
    final_state = {}
    for output in cov_rag_app.stream(initial_state):
        for key, value in output.items():
            if isinstance(value, dict):
                final_state.update(value)
    
    # Extraire les résultats
    generation = final_state.get("generation", "")
    sources = final_state.get("sources", [])
    response_lang = final_state.get("response_lang", "fr")
    
    # Métriques COV-RAG
    similarity_score = float(final_state.get("similarity_score", 0.0))
    confidence_score = float(final_state.get("final_confidence", final_state.get("confidence_score", 0.0)))
    quality_pass = final_state.get("quality_pass", False)
    escalate = final_state.get("escalate", False)
    hallucination_detected = final_state.get("hallucination_detected", False)
    corrections_made = final_state.get("corrections_made", 0)
    cites_ok = final_state.get("cites_ok", False)
    
    # Vérifications CoVE
    verification_results = final_state.get("verification_results", [])
    verifications = [
        VerificationInfo(
            claim=v.get("claim", ""),
            is_verified=v.get("is_verified", False),
            confidence=v.get("confidence", 0.0),
            evidence=v.get("evidence"),
            correction=v.get("correction")
        )
        for v in verification_results
    ] if verification_results else None
    
    # Réponse initiale (avant correction)
    initial_answer = final_state.get("initial_generation")
    
    # Déterminer le mode
    if final_state.get("escalated"):
        mode = "human_review"
    elif quality_pass:
        mode = "cov_rag"
    else:
        mode = "cov_rag_fallback"
    
    # Mapper les sources
    mapped_sources = []
    for s in sources:
        mapped_sources.append(SourceInfo(
            id=s.get("id"),
            score=round(float(s.get("score", 0.0)), 3),
            source=s.get("source", "unknown"),
            lang=s.get("lang", "unknown"),
            type=s.get("type", "unknown")
        ))
    
    response_obj = ChatResponse(
        question=payload.question,
        answer=generation,
        language=response_lang,
        similarity_score=round(similarity_score, 3),
        confidence_score=round(confidence_score, 3),
        sources=mapped_sources,
        mode=mode,
        quality_pass=quality_pass,
        escalate=escalate,
        cites_ok=cites_ok,
        hallucination=hallucination_detected,
        # COV-RAG specific
        cove_enabled=True,
        hallucination_detected=hallucination_detected,
        corrections_made=corrections_made,
        verifications=verifications,
        initial_answer=initial_answer if initial_answer != generation else None
    )
    
    # Log
    try:
        print(f"[chatbot] COV-RAG result: mode={mode} confidence={confidence_score:.2f} hallucination={hallucination_detected} corrections={corrections_made}")
    except Exception:
        pass
    
    # Mise en cache
    try:
        payload_json = response_obj.model_dump_json()
        if _redis:
            _redis.setex(cache_key, ttl, payload_json)
        else:
            _local_cache.set(cache_key, payload_json)
    except Exception:
        pass
    
    return response_obj


async def _run_standard_rag_pipeline(payload: ChatQuery, cache_key: str, ttl: int) -> ChatResponse:
    """
    Exécute le pipeline RAG standard (sans CoVE).
    
    Plus rapide mais sans vérification des hallucinations.
    """
    print("[chatbot] Using standard RAG pipeline")
    
    # Collect outputs from the RAG workflow (LAZY LOADED)
    last_generate = None
    last_fallback = None
    last_evaluate = None
    last_human = None

    rag_app = get_rag_app()  # Charge le workflow à la première requête
    for output in rag_app.stream({
        "question": payload.question,
        "collection": payload.collection,
        "sources_filter": payload.sources_filter,
    }):
        if "generate" in output:
            last_generate = output["generate"]
        if "fallback" in output:
            last_fallback = output["fallback"]
        if "evaluate_response" in output:
            last_evaluate = output["evaluate_response"]
        if "human_review" in output:
            last_human = output["human_review"]

    # Decide final payload based on evaluation
    chosen = None
    mode = "fallback"
    similarity_score = 0.0
    confidence_score = 0.0

    if last_evaluate is not None:
        if last_evaluate.get("quality_pass"):
            chosen = last_generate or last_fallback
            mode = "generate"
            similarity_score = float(last_evaluate.get("similarity_score", 0.0))
            confidence_score = float(last_evaluate.get("confidence_score", 0.0))
        else:
            if last_evaluate.get("escalate") and last_human is not None:
                chosen = last_human
                mode = "human_review"
                similarity_score = float(last_evaluate.get("similarity_score", 0.0))
                confidence_score = float(last_evaluate.get("confidence_score", 0.0))
            else:
                chosen = last_fallback or last_generate
                mode = "fallback"
                similarity_score = float(last_evaluate.get("similarity_score", 0.0))
                confidence_score = float(last_evaluate.get("confidence_score", 0.0))
    else:
        if last_generate is not None:
            chosen = last_generate
            mode = "generate"
            srcs = chosen.get("sources", [])
            if srcs:
                try:
                    avg_score = sum(float(s.get("score", 0.0)) for s in srcs) / len(srcs)
                    similarity_score = round(avg_score, 3)
                    confidence_score = round(avg_score * 0.8, 3)
                except Exception:
                    similarity_score = 0.0
                    confidence_score = 0.0
        elif last_fallback is not None:
            chosen = last_fallback
            mode = "fallback"

    if not chosen:
        raise HTTPException(status_code=500, detail="Aucune réponse générée")

    gen_content = chosen.get("generation")
    sources = chosen.get("sources", [])
    response_lang = chosen.get("response_lang") if chosen.get("response_lang") is not None else (last_generate or {}).get("response_lang", "en")

    if isinstance(gen_content, dict):
        answer_text = gen_content.get("answer", "")
    else:
        answer_text = str(gen_content)

    mapped_sources = []
    for s in sources:
        mapped_sources.append(SourceInfo(
            id=s.get("id"),
            score=round(s.get("score", 0.0), 3),
            source=s.get("source", "unknown"),
            lang=s.get("lang", "unknown"),
            type=s.get("type", "unknown")
        ))

    eval_meta = last_evaluate or {}

    response_obj = ChatResponse(
        question=payload.question,
        answer=answer_text,
        language=response_lang,
        similarity_score=similarity_score,
        confidence_score=confidence_score,
        sources=mapped_sources,
        mode=mode,
        quality_pass=eval_meta.get("quality_pass") if isinstance(eval_meta, dict) else None,
        escalate=eval_meta.get("escalate") if isinstance(eval_meta, dict) else None,
        cites_ok=eval_meta.get("cites_ok") if isinstance(eval_meta, dict) else None,
        overlap_ratio=eval_meta.get("overlap_ratio") if isinstance(eval_meta, dict) else None,
        hallucination=eval_meta.get("hallucination") if isinstance(eval_meta, dict) else None,
        cove_enabled=False
    )

    try:
        print(f"[chatbot] Standard RAG result: mode={mode} similarity={similarity_score} confidence={confidence_score}")
    except Exception:
        pass

    # Mise en cache
    try:
        payload_json = response_obj.model_dump_json()
        if _redis:
            _redis.setex(cache_key, ttl, payload_json)
        else:
            _local_cache.set(cache_key, payload_json)
    except Exception:
        pass

    return response_obj
