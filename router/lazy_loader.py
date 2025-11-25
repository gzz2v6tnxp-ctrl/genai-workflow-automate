"""
Lazy loader pour les modules lourds.
Permet de réduire la consommation RAM au démarrage.
Les modules sont chargés uniquement à la première utilisation.
"""

from typing import Any, Optional
import sys

# Cache des modules chargés
_loaded_modules: dict = {}


def get_rag_app():
    """Charge le workflow RAG uniquement à la demande."""
    if "rag_app" not in _loaded_modules:
        print("[LazyLoader] Chargement du workflow RAG...")
        from agents.graph import app
        _loaded_modules["rag_app"] = app
        print("[LazyLoader] Workflow RAG chargé.")
    return _loaded_modules["rag_app"]


def get_document_retriever():
    """Charge le retriever uniquement à la demande."""
    if "retriever_class" not in _loaded_modules:
        print("[LazyLoader] Chargement du DocumentRetriever...")
        from scripts.vector_store.retrieve import DocumentRetriever
        _loaded_modules["retriever_class"] = DocumentRetriever
        print("[LazyLoader] DocumentRetriever chargé.")
    return _loaded_modules["retriever_class"]


def preload_on_first_request():
    """
    Précharge les modules au premier appel API.
    Appelé par un middleware ou le premier endpoint.
    """
    get_rag_app()


def get_memory_usage_mb() -> float:
    """Retourne l'utilisation mémoire actuelle en Mo."""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024  # Convert KB to MB (Linux)
    except ImportError:
        # Windows fallback
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return -1


def cleanup_memory():
    """Force le garbage collection pour libérer la RAM."""
    import gc
    gc.collect()
