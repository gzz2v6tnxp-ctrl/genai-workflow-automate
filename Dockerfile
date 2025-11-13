# Backend FastAPI + Qdrant client
# Compatible avec : Local dev, Docker Compose, Railway.app

FROM python:3.11-slim

WORKDIR /app

# Copier requirements et installer dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port FastAPI
EXPOSE 8000

# Lancer FastAPI (compatible avec Railway PORT env var)
# Railway affecte la variable PORT, donc on la lit ici
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]