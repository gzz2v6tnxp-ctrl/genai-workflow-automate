# main.py (extrait corrigé)
from fastapi import FastAPI
from router import ingestion, retriever, chatbot
from fastapi.middleware.cors import CORSMiddleware
import os

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

# Include routers
# app.include_router(ingestion.router)
# app.include_router(retriever.router)
app.include_router(chatbot.router)
