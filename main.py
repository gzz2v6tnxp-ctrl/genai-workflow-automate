# main.py (optimisé pour RAM limitée)
from fastapi import FastAPI
from router import chatbot
from fastapi.middleware.cors import CORSMiddleware
import os
import gc

app = FastAPI(
    title="GenAI Workflow Automate API",
    description="API pour piloter le pipeline d'ingestion et de génération de réponses.",
    version="1.0.0",
)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "https://gzz2v6tnxp-ctrl.github.io",
]

# Autoriser des origins supplémentaires via env var (p.ex. "https://example.com,https://app.example.com")
if os.getenv("ALLOWED_ORIGINS"):
    extra = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
    ALLOWED_ORIGINS.extend(extra)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint léger pour vérifier que l'API est vivante."""
    return {"status": "ok"}


@app.get("/health/memory", tags=["Health"])
async def memory_check():
    """Endpoint pour monitorer l'utilisation mémoire (debug OOM)."""
    import sys
    
    # Forcer le garbage collection
    gc.collect()
    
    memory_info = {
        "status": "ok",
        "python_version": sys.version,
    }
    
    # Essayer d'obtenir les infos mémoire
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        memory_info["memory_mb"] = round(usage.ru_maxrss / 1024, 2)  # Linux: KB -> MB
    except ImportError:
        pass
    
    return memory_info


# Include routers
app.include_router(chatbot.router)
