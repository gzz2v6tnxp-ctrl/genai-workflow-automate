#!/usr/bin/env python3
"""
Script de démarrage optimisé pour RAM limitée (Render Free Tier).
Lance Uvicorn avec des paramètres adaptés à 512 Mo RAM.
"""

import os
import sys
import gc

def check_environment():
    """Vérifier l'environnement et les variables requises."""
    print("=== Diagnostic de démarrage (Low RAM Mode) ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"PORT: {os.getenv('PORT', 'not set (will use 8000)')}")
    
    # Vérifier les variables d'environnement critiques
    env_vars = [
        'OPENAI_API_KEY',
        'QDRANT_CLOUD_URL', 
        'QDRANT_API_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"{var}: {'*' * min(len(value), 10)} (set)")
        else:
            print(f"{var}: NOT SET - service might not work fully")

def test_imports():
    """Tester les imports critiques SANS charger les modules lourds."""
    print("\n=== Test des imports (mode léger) ===")
    try:
        # Ne PAS importer agents.graph ici - c'est le lazy loading
        import fastapi
        print("✓ FastAPI available")
        
        import qdrant_client
        print("✓ Qdrant client available")
        
        import openai
        print("✓ OpenAI client available")
        
        # Forcer le garbage collection
        gc.collect()
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def start_server():
    """Démarrer le serveur uvicorn avec paramètres optimisés RAM."""
    import uvicorn
    
    port = int(os.getenv('PORT', '8000'))
    print(f"\n=== Démarrage du serveur sur le port {port} (Low RAM Mode) ===")
    
    # Configuration optimisée pour Render Free Tier (512 Mo RAM)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1,  # IMPORTANT: 1 seul worker pour économiser la RAM
        loop="uvloop" if sys.platform != "win32" else "asyncio",
        http="httptools" if sys.platform != "win32" else "h11",
        log_level="info",
        access_log=False,  # Désactiver les logs d'accès pour économiser RAM
        limit_concurrency=10,  # Limiter les connexions simultanées
        limit_max_requests=1000,  # Recycler le worker après N requêtes
        timeout_keep_alive=30,  # Réduire le timeout
    )

if __name__ == "__main__":
    check_environment()
    
    if test_imports():
        start_server()
    else:
        print("Erreur: impossible de démarrer à cause des imports manqués")
        sys.exit(1)