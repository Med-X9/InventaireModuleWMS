# Configuration Frontend/Backend - Même Serveur, Containers Séparés

Ce guide explique comment configurer le frontend et le backend sur le même serveur mais dans des containers Docker séparés.

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│         Serveur (Même IP)            │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  Frontend    │  │  Backend    │ │
│  │  Container   │  │  Container  │ │
│  │  Port: 3000  │  │  Port: 8000 │ │
│  └──────┬───────┘  └──────┬───────┘ │
│         │                │          │
│         └──────┬─────────┘          │
│                │                    │
│         ┌──────▼──────┐             │
│         │   Nginx    │             │
│         │  Reverse   │             │
│         │   Proxy    │             │
│         │ Port: 80/443│            │
│         └────────────┘             │
└─────────────────────────────────────┘
```

## 📋 Configuration Docker Compose

### Exemple de `docker-compose.yml` complet

```yaml
version: '3.8'

networks:
  inventaire-net:
    external: true

services:
  # Backend Django
  web:
    image: smatchdigital/backend-app:${IMAGE_TAG:-dev-latest}
    container_name: inventaire-web
    networks:
      - inventaire-net
    command: >
      sh -c "python manage.py migrate --noinput && 
            python manage.py collectstatic --noinput --clear --verbosity=0 && 
            exec gunicorn project.wsgi:application -b 0.0.0.0:8000 
            --workers 2 --threads 4 --timeout 300 --preload --log-level info
          "
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - logs_volume:/app/logs
      - static_dir:/app/static
    ports:
      - "8000:8000"
    env_file: .env
    restart: unless-stopped
    environment:
      DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}
      DJANGO_DEBUG: ${DJANGO_DEBUG}
      DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS}
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
      CORS_ALLOW_ALL_ORIGINS: ${CORS_ALLOW_ALL_ORIGINS}
      CORS_ALLOWED_ORIGINS: ${CORS_ALLOWED_ORIGINS}
      POSTGRES_HOST: postgres
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_PORT: ${POSTGRES_PORT}

  # Frontend (exemple avec React/Vue)
  frontend:
    image: smatchdigital/frontend-app:${IMAGE_TAG:-dev-latest}
    container_name: inventaire-frontend
    networks:
      - inventaire-net
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://web:8000
      # ou pour Vue: VUE_APP_API_URL=http://web:8000
    restart: unless-stopped
    depends_on:
      - web

  # Base de données PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: inventaire-postgres
    networks:
      - inventaire-net
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    build: ./nginx
    container_name: inventaire-nginx
    networks:
      - inventaire-net
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
  logs_volume:
  static_dir:
```

## ⚙️ Configuration du fichier `.env`

### Variables importantes pour la communication entre containers

```bash
# ============================================
# Configuration Django
# ============================================
IS_PRODUCTION=False
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here

# Hosts autorisés - utiliser le nom du domaine ou l'IP du serveur
# Si vous avez un domaine: votre-domaine.com,www.votre-domaine.com
# Si vous utilisez l'IP: SERVER_IP (remplacer par l'IP réelle)
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# ============================================
# CORS - Configuration pour Frontend
# ============================================
# Option 1: Autoriser toutes les origines (pour développement)
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=

# Option 2: Spécifier les origines (recommandé pour production)
# CORS_ALLOW_ALL_ORIGINS=False
# CORS_ALLOWED_ORIGINS=http://frontend:3000,http://localhost:3000,https://votre-domaine.com

CORS_ALLOW_CREDENTIALS=True

# ============================================
# Base de données
# ============================================
# Utiliser le nom du service Docker 'postgres' pour la connexion entre containers
POSTGRES_DB=inventairedb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-strong-password
POSTGRES_HOST=postgres  # Nom du service Docker
POSTGRES_PORT=5432

# ============================================
# CSRF
# ============================================
# Utiliser le même domaine/IP que ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS=http://localhost,http://SERVER_IP
```

## 🔧 Configuration Nginx pour Reverse Proxy

### Exemple de `nginx/nginx.conf`

```nginx
upstream backend {
    server web:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name _;

    # Proxy pour l'API Backend
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers (si nécessaire)
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }

    # Fichiers statiques du backend
    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }

    # Proxy pour le Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (si nécessaire)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔗 Communication entre Containers

### Backend → Frontend

Le backend peut communiquer avec le frontend via :
- **Nom du service Docker** : `http://frontend:3000` (dans le même réseau Docker)
- **IP du serveur** : `http://SERVER_IP:3000` (depuis l'extérieur)

### Frontend → Backend

Le frontend doit utiliser :
- **En développement** : `http://localhost:8000` ou `http://SERVER_IP:8000`
- **En production** : `https://votre-domaine.com/api` (via Nginx)

### Configuration Frontend

#### React (.env)
```bash
REACT_APP_API_URL=http://localhost:8000/api
# ou pour production:
# REACT_APP_API_URL=https://votre-domaine.com/api
```

#### Vue (.env)
```bash
VUE_APP_API_URL=http://localhost:8000/api
# ou pour production:
# VUE_APP_API_URL=https://votre-domaine.com/api
```

## 📝 Checklist de Configuration

### 1. Fichier `.env` Backend

- [ ] `POSTGRES_HOST=postgres` (nom du service Docker)
- [ ] `CORS_ALLOWED_ORIGINS` configuré avec les origines frontend
- [ ] `DJANGO_ALLOWED_HOSTS` configuré avec le domaine/IP du serveur
- [ ] `CSRF_TRUSTED_ORIGINS` configuré avec les origines frontend

### 2. Docker Compose

- [ ] Tous les services dans le même réseau (`inventaire-net`)
- [ ] Frontend dépend de Backend (`depends_on`)
- [ ] Nginx dépend de Backend et Frontend

### 3. Nginx

- [ ] Configuration du reverse proxy pour `/api/` vers backend
- [ ] Configuration du proxy pour `/` vers frontend
- [ ] Headers CORS configurés si nécessaire

### 4. Frontend

- [ ] Variable d'environnement `API_URL` configurée
- [ ] Requêtes API pointent vers le bon endpoint

## 🚀 Déploiement

### 1. Démarrer les services

```bash
# Créer le réseau Docker si nécessaire
docker network create inventaire-net

# Démarrer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f
```

### 2. Vérifier la communication

```bash
# Vérifier que les containers sont dans le même réseau
docker network inspect inventaire-net

# Tester la connexion backend
curl http://localhost:8000/api/

# Tester la connexion frontend
curl http://localhost:3000/

# Tester via Nginx
curl http://localhost/api/
curl http://localhost/
```

## 🔍 Dépannage

### Problème : Frontend ne peut pas accéder au Backend

**Solution 1** : Vérifier que les containers sont dans le même réseau
```bash
docker network inspect inventaire-net
```

**Solution 2** : Utiliser le nom du service Docker dans les URLs
- ✅ `http://web:8000` (dans le même réseau)
- ❌ `http://localhost:8000` (depuis l'extérieur du container)

**Solution 3** : Vérifier les variables CORS
```bash
# Dans .env backend
CORS_ALLOWED_ORIGINS=http://frontend:3000,http://localhost:3000
```

### Problème : Erreurs CORS

**Solution** : Configurer correctement CORS dans `.env`
```bash
CORS_ALLOW_ALL_ORIGINS=True  # Pour développement
# ou
CORS_ALLOWED_ORIGINS=http://frontend:3000,http://localhost:3000  # Pour production
```

### Problème : Base de données inaccessible

**Solution** : Utiliser le nom du service Docker
```bash
# Dans .env
POSTGRES_HOST=postgres  # Nom du service dans docker-compose.yml
```

## 📚 Ressources

- [Docker Networking](https://docs.docker.com/network/)
- [Nginx Reverse Proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [CORS Configuration](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

