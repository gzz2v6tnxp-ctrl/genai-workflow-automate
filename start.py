#!/usr/bin/env python3
"""
Script de démarrage robuste pour le backend GenAI Workflow.
Effectue des vérifications avant de lancer le serveur.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Vérifier l'environnement et les variables requises."""
    print("=== Diagnostic de démarrage ===")
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
    """Tester les imports critiques."""
    print("\n=== Test des imports ===")
    try:
        import main
        print("✓ main.py import successful")
        
        import fastapi
        print("✓ FastAPI available")
        
        import qdrant_client
        print("✓ Qdrant client available")
        
        import openai
        print("✓ OpenAI client available")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def start_server():
    """Démarrer le serveur uvicorn."""
    port = os.getenv('PORT', '8000')
    print(f"\n=== Démarrage du serveur sur le port {port} ===")
    
    cmd = [
        'uvicorn', 
        'main:app', 
        '--host', '0.0.0.0', 
        '--port', port,
        '--log-level', 'info'
    ]
    
    print(f"Commande: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    check_environment()
    
    if test_imports():
        start_server()
    else:
        print("Erreur: impossible de démarrer à cause des imports manqués")
        sys.exit(1)