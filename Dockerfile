# Backend FastAPI optimisé pour RAM limitée (Render Free Tier)
# Cible: ~512 Mo RAM max

FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copier et installer les dépendances de production uniquement
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# ---- Production Stage ----
FROM python:3.11-slim

# Metadata
LABEL maintainer="genai-workflow" \
      description="Optimized FastAPI backend for low RAM environments"

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/archives/*

WORKDIR /app

# Copier les packages Python depuis le builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copier uniquement le code nécessaire (pas les tests, notebooks, data)
COPY main.py start.py ./
COPY router/ ./router/
COPY agents/ ./agents/
COPY scripts/ ./scripts/

# Variables d'environnement pour optimiser Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=2 \
    MALLOC_TRIM_THRESHOLD_=100000

# Exposer le port FastAPI
EXPOSE 8000

# Health check léger
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Script de démarrage optimisé
CMD ["python", "start.py"]
