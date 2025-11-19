# main.py
from fastapi import FastAPI
from router import ingestion, retriever, chatbot

from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="GenAI Workflow Automate API",
    description="API pour piloter le pipeline d'ingestion et de génération de réponses.",
    version="1.0.0",
)

# Configuration CORS adaptative
# En dev local : autoriser localhost
# En prod (GitHub Pages) : autoriser l'URL GitHub Pages
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Frontend Vite (dev)
    "http://localhost:3000",  # Alt frontend (dev)
    "http://127.0.0.1:5173",  # Localhost alt
    "https://gzz2v6tnxp-ctrl.github.io",  # GitHub Pages root
    "https://gzz2v6tnxp-ctrl.github.io/genai-workflow-automate",  # GitHub Pages repo path
]

# Autoriser des origins supplémentaires via env var (pour Railway + custom domains)
if os.getenv("ALLOWED_ORIGINS"):
    ALLOWED_ORIGINS.extend(os.getenv("ALLOWED_ORIGINS", "").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_origins=["https://gzz2v6tnxp-ctrl.github.io"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routeurs
# app.include_router(ingestion.router)
# app.include_router(retriever.router)
app.include_router(chatbot.router)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bienvenue sur l'API du pipeline GenAI Workflow Automate."}

# Pour lancer l'API, utilisez la commande :
# uvicorn main:app --reload
