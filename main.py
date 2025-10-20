# main.py
from fastapi import FastAPI
from router import ingestion

app = FastAPI(
    title="GenAI Workflow Automate API",
    description="API pour piloter le pipeline d'ingestion et de génération de réponses.",
    version="1.0.0",
)

# Inclure le routeur d'ingestion
app.include_router(ingestion.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bienvenue sur l'API du pipeline GenAI Workflow Automate."}

# Pour lancer l'API, utilisez la commande :
# uvicorn main:app --reload