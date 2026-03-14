# Stage 1: Builder
FROM python:3.12.1-slim as builder

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Installation des dépendances système pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python dans un environnement virtuel
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Stage 2: Runtime
FROM python:3.12.1-slim

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copie de l'environnement virtuel du builder
COPY --from=builder /opt/venv /opt/venv

# Copie du code de l'application
COPY . .

# Création des dossiers nécessaires
RUN mkdir -p /app/static /app/media /app/logs /app/data \
    && chmod -R 755 /app/static /app/media /app/data \
    && chmod -R 777 /app/logs \
    && useradd -U app_user \
    && chown -R app_user:app_user /app

# Créer le dossier data s'il n'existe pas (pour le cas où il n'est pas dans le repo)
RUN mkdir -p /app/data && chmod 755 /app/data

# Passage à l'utilisateur non-root
USER app_user

# Exposition du port
EXPOSE 8000

# Commande par défaut pour la production
# CMD pour production
CMD exec gunicorn project.wsgi:application \
    -b 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --timeout 300 \
    --preload \
    --log-level info
