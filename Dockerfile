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

# Création de l'utilisateur d'abord
RUN useradd -m -u 1000 app_user

# Copie du code de l'application avec le bon propriétaire
COPY --chown=app_user:app_user . .

# Création des dossiers nécessaires avec les bonnes permissions
RUN mkdir -p /app/static /app/media /app/logs \
    && chown -R app_user:app_user /app \
    && chmod -R 755 /app/static /app/media /app/logs

# Passage à l'utilisateur non-root
USER app_user

# Exposition du port
EXPOSE 8000

# Commande par défaut pour la production
CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"] 
