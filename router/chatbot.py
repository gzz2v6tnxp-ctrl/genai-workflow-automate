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

from agents.graph import app as rag_app  # workflow compilé

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

class SourceInfo(BaseModel):
    id: Any
    score: float
    source: str
    lang: str
    type: str

class ChatResponse(BaseModel):
    question: str
    answer: str
    language: str
    similarity_score: float  # Score de similarité brut (0-1)
    confidence_score: float  # Score de confiance ajusté (×0.8)
    sources: List[SourceInfo]
    mode: str
    # Quality evaluation fields (optional, used by frontend for subtle UX)
    quality_pass: Optional[bool] = None
    escalate: Optional[bool] = None
    cites_ok: Optional[bool] = None
    overlap_ratio: Optional[float] = None
    hallucination: Optional[bool] = None

@router.post("/query", response_model=ChatResponse)
async def query_chatbot(payload: ChatQuery):
    """Interroge le workflow RAG pour une question utilisateur."""
    try:
        # Log reçu (debug) : afficher le payload tel que reçu par l'API
        try:
            print(f"[chatbot] received payload: collection={payload.collection} sources_filter={payload.sources_filter} output_format={payload.output_format}")
        except Exception:
            pass

        # Clé de cache (inclure sources_filter pour éviter résultats partagés entre filtres)
        sf = ",".join(sorted(payload.sources_filter)) if payload.sources_filter else ""
        key_base = f"{payload.collection}:{sf}:{payload.output_format}:{payload.question.strip().lower()}"
        cache_key = "chat:" + hashlib.sha256(key_base.encode("utf-8")).hexdigest()

        # Debug: afficher la clé de cache calculée
        try:
            print(f"[chatbot] cache_key={cache_key} key_base={key_base}")
        except Exception:
            pass

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

        # Collect outputs from the RAG workflow
        last_generate = None
        last_fallback = None
        last_evaluate = None
        last_human = None

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
                # evaluation node returns quality_pass/confidence/escalate
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
                # not quality_pass
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
            # no evaluation node present -> fallback to generate or fallback
            if last_generate is not None:
                chosen = last_generate
                mode = "generate"
                # derive scores from sources if possible
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
                similarity_score = 0.0
                confidence_score = 0.0

        if not chosen:
            raise HTTPException(status_code=500, detail="Aucune réponse générée")

        gen_content = chosen.get("generation")
        sources = chosen.get("sources", [])
        response_lang = chosen.get("response_lang") if chosen.get("response_lang") is not None else (last_generate or {}).get("response_lang", "en")

        # Normalisation de la réponse (string ou dict)
        if isinstance(gen_content, dict):
            answer_text = gen_content.get("answer", "")
        else:
            answer_text = str(gen_content)

        # Mapper sources vers modèle Pydantic
        mapped_sources = []
        for s in sources:
            mapped_sources.append(SourceInfo(
                id=s.get("id"),
                score=round(s.get("score", 0.0), 3),
                source=s.get("source", "unknown"),
                lang=s.get("lang", "unknown"),
                type=s.get("type", "unknown")
            ))

        # Attach evaluation metadata if present
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
        )

        # Debug log to console for tracing which branch was chosen
        try:
            print(f"[chatbot] chosen_mode={mode} similarity={similarity_score} confidence={confidence_score} response_lang={response_lang} sources_filter={payload.sources_filter}")
        except Exception:
            pass

        # Extra debug: print the actual chosen payload returned by the workflow
        try:
            # show a trimmed preview (avoid huge dumps) but include keys
            if isinstance(chosen, dict):
                preview = {
                    k: (v if k != 'generation' else (v[:600] + ('...' if len(v) > 600 else ''))) for k, v in chosen.items()
                }
                print(f"[chatbot] chosen_payload_preview={json.dumps(preview, ensure_ascii=False)}")
            else:
                print(f"[chatbot] chosen_payload_type={type(chosen)}")
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
