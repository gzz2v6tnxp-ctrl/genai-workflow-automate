# main.py
from fastapi import FastAPI
from router import ingestion, retriever, chatbot

app = FastAPI(
    title="GenAI Workflow Automate API",
    description="API pour piloter le pipeline d'ingestion et de génération de réponses.",
    version="1.0.0",
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