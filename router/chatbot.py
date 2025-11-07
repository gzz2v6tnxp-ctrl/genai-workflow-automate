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
    confidence: float
    sources: List[SourceInfo]
    mode: str

@router.post("/query", response_model=ChatResponse)
async def query_chatbot(payload: ChatQuery):
    """Interroge le workflow RAG pour une question utilisateur."""
    try:
        # Clé de cache
        key_base = f"{payload.collection}:{payload.output_format}:{payload.question.strip().lower()}"
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

        last_generation: Dict[str, Any] | None = None
        for output in rag_app.stream({
            "question": payload.question,
            "collection": payload.collection,
            "sources_filter": payload.sources_filter,
        }):
            if "generate" in output:
                last_generation = output["generate"]
            elif "fallback" in output:
                last_generation = output["fallback"]

        if not last_generation:
            raise HTTPException(status_code=500, detail="Aucune réponse générée")

        gen_content = last_generation.get("generation")
        sources = last_generation.get("sources", [])
        response_lang = last_generation.get("response_lang", "en")

        # Confidence = meilleur score si disponible
        confidence = 0.0
        if sources:
            try:
                confidence = round(sources[0]["score"], 3)
            except Exception:
                confidence = 0.0

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

        mode = "generate" if any(k in last_generation for k in ["response_lang", "sources"]) and sources else "fallback"

        response_obj = ChatResponse(
            question=payload.question,
            answer=answer_text,
            language=response_lang,
            confidence=confidence,
            sources=mapped_sources,
            mode=mode
        )

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
