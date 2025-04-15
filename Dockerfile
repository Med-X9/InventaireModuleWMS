FROM python:3.12.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier tout le code
COPY . .

# Lancer le serveur avec gunicorn (production)
CMD ["gunicorn", "monapp.wsgi:application", "--bind", "0.0.0.0:8000"]
