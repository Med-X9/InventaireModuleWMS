# Guide d'Implémentation CI/CD - Test et Production

Ce guide décrit comment configurer et déployer l'application sur les environnements **Test** et **Production** avec les améliorations de sécurité.

## 📋 Table des Matières

1. [Architecture CI/CD](#architecture-cicd)
2. [Configuration des Environnements](#configuration-des-environnements)
3. [Fichiers de Configuration](#fichiers-de-configuration)
4. [Variables d'Environnement par Environnement](#variables-denvironnement-par-environnement)
5. [Pipeline Jenkins](#pipeline-jenkins)
6. [Déploiement](#déploiement)
7. [Vérifications Post-Déploiement](#vérifications-post-déploiement)

## 🏗️ Architecture CI/CD

```
┌─────────────────┐
│   Git Push      │
│  (dev/main)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Jenkins       │
│   Pipeline      │
└────────┬────────┘
         │
         ├──► SonarQube Analysis
         ├──► Build Docker Image
         ├──► Push to Docker Hub
         └──► Deploy to Server
                │
                ├──► Test Environment (dev branch)
                └──► Production Environment (main branch)
```

## ⚙️ Configuration des Environnements

### Environnement TEST (dev branch)

- **Serveur**: `147.93.55.221`
- **Image Tag**: `dev-latest`
- **URL**: À configurer selon votre infrastructure
- **Debug**: `True` (pour faciliter le debugging)
- **SSL**: Optionnel (peut être désactivé)

### Environnement PRODUCTION (main branch)

- **Serveur**: `31.97.158.68`
- **Image Tag**: `prod-latest`
- **URL**: À configurer selon votre infrastructure
- **Debug**: `False` (obligatoire)
- **SSL**: Obligatoire (HTTPS uniquement)

## 📁 Fichiers de Configuration

### 1. Configuration Jenkins (`jenkins-config.yml`)

Le fichier `jenkins-config.yml` est déjà configuré avec les environnements `dev` et `main`. Voici les points importants :

```yaml
environments:
  dev:
    deploy_host: "147.93.55.221"
    deploy_creds: "dev-test-creds"
    env_name: "development"
    image_tag_suffix: "dev-latest"
  
  main:
    deploy_host: "31.97.158.68"
    deploy_creds: "prod-creds"
    env_name: "production"
    image_tag_suffix: "prod-latest"
```

### 2. Fichiers d'Environnement

Créez des fichiers `.env` spécifiques pour chaque environnement :

#### `.env.test` (pour l'environnement TEST)

```bash
# ============================================
# Configuration Django - TEST
# ============================================
IS_PRODUCTION=False
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=<clé-secrète-test>
DJANGO_ALLOWED_HOSTS=147.93.55.221,localhost,127.0.0.1

# ============================================
# Sécurité SSL/TLS - TEST (Optionnel)
# ============================================
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
CSRF_TRUSTED_ORIGINS=http://147.93.55.221

# ============================================
# CORS - TEST
# ============================================
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=

# ============================================
# Base de données - TEST
# ============================================
POSTGRES_DB=inventaire_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<mot-de-passe-test>
POSTGRES_HOST=postgres-test
POSTGRES_PORT=5432

# ============================================
# Configuration Email - TEST
# ============================================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=test@example.com
EMAIL_HOST_PASSWORD=<app-password-test>
EMAIL_USE_TLS=True

# ============================================
# Docker
# ============================================
IMAGE_TAG=dev-latest
```

#### `.env.prod` (pour l'environnement PRODUCTION)

```bash
# ============================================
# Configuration Django - PRODUCTION
# ============================================
IS_PRODUCTION=True
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<clé-secrète-production-UNIQUE>
DJANGO_ALLOWED_HOSTS=31.97.158.68,votre-domaine.com,www.votre-domaine.com

# ============================================
# Sécurité SSL/TLS - PRODUCTION (OBLIGATOIRE)
# ============================================
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com

# Si derrière nginx (reverse proxy)
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================
# CORS - PRODUCTION
# ============================================
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com

# ============================================
# Base de données - PRODUCTION
# ============================================
POSTGRES_DB=inventaire_prod
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<mot-de-passe-production-FORT>
POSTGRES_HOST=postgres-prod
POSTGRES_PORT=5432

# ============================================
# Configuration Email - PRODUCTION
# ============================================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=production@example.com
EMAIL_HOST_PASSWORD=<app-password-production>
EMAIL_USE_TLS=True

# ============================================
# Docker
# ============================================
IMAGE_TAG=prod-latest
```

### 3. Docker Compose par Environnement

#### `docker-compose.test.yml` (pour TEST)

```yaml
version: '3.8'

networks:
  inventaire-net:
    external: true

services:
  web:
    image: smatchdigital/backend-app:dev-latest
    container_name: inventaire-web-test
    networks:
      - inventaire-net
    command: >
      sh -c "python manage.py migrate --noinput && 
            python manage.py collectstatic --noinput --clear --verbosity=0 && 
            exec gunicorn project.wsgi:application -b 0.0.0.0:8000 
            --workers 2 --threads 4 --timeout 300 --preload --log-level info
          "
    volumes:
      - static_volume_test:/app/staticfiles
      - media_volume_test:/app/media
      - logs_volume_test:/app/logs
      - static_dir_test:/app/static
    ports:
      - "8000:8000"
    env_file: .env.test
    environment:
      DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}
      DJANGO_DEBUG: ${DJANGO_DEBUG}
      DJANGO_STATIC_ROOT: ${DJANGO_STATIC_ROOT}
      DJANGO_MEDIA_ROOT: ${DJANGO_MEDIA_ROOT}
      DJANGO_STATICFILES_DIRS: ${DJANGO_STATICFILES_DIRS}
      DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS}
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
      CORS_ALLOW_ALL_ORIGINS: ${CORS_ALLOW_ALL_ORIGINS}
      CORS_ALLOWED_ORIGINS: ${CORS_ALLOWED_ORIGINS}
    restart: unless-stopped

  nginx:
    networks:
      - inventaire-net
    container_name: inventaire-nginx-test
    build: ./nginx
    volumes:
      - static_volume_test:/app/staticfiles
      - media_volume_test:/app/media
    ports:
      - "80:80"
    depends_on:
      - web
    restart: unless-stopped

volumes:
  static_volume_test:
  media_volume_test:
  logs_volume_test:
  static_dir_test:
```

#### `docker-compose.prod.yml` (pour PRODUCTION)

```yaml
version: '3.8'

networks:
  inventaire-net:
    external: true

services:
  web:
    image: smatchdigital/backend-app:prod-latest
    container_name: inventaire-web-prod
    networks:
      - inventaire-net
    command: >
      sh -c "python manage.py migrate --noinput && 
            python manage.py collectstatic --noinput --clear --verbosity=0 && 
            exec gunicorn project.wsgi:application -b 0.0.0.0:8000 
            --workers 4 --threads 8 --timeout 300 --preload --log-level warning
          "
    volumes:
      - static_volume_prod:/app/staticfiles
      - media_volume_prod:/app/media
      - logs_volume_prod:/app/logs
      - static_dir_prod:/app/static
    ports:
      - "8000:8000"
    env_file: .env.prod
    environment:
      DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}
      DJANGO_DEBUG: ${DJANGO_DEBUG}
      DJANGO_STATIC_ROOT: ${DJANGO_STATIC_ROOT}
      DJANGO_MEDIA_ROOT: ${DJANGO_MEDIA_ROOT}
      DJANGO_STATICFILES_DIRS: ${DJANGO_STATICFILES_DIRS}
      DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS}
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
      CORS_ALLOW_ALL_ORIGINS: ${CORS_ALLOW_ALL_ORIGINS}
      CORS_ALLOWED_ORIGINS: ${CORS_ALLOWED_ORIGINS}
    cpus: 2
    mem_limit: 6g
    restart: unless-stopped

  nginx:
    networks:
      - inventaire-net
    container_name: inventaire-nginx-prod
    build: ./nginx
    volumes:
      - static_volume_prod:/app/staticfiles
      - media_volume_prod:/app/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: unless-stopped

volumes:
  static_volume_prod:
  media_volume_prod:
  logs_volume_prod:
  static_dir_prod:
```

## 🔄 Pipeline Jenkins

Le pipeline Jenkins (`Jenkinsfile`) est déjà configuré. Il exécute automatiquement :

1. **Load Configuration** - Charge `jenkins-config.yml`
2. **Check Branch** - Vérifie si la branche est configurée
3. **Clone Repositories** - Clone le code source
4. **SonarQube Analysis** - Analyse de qualité de code
5. **Build Docker Image** - Construit l'image Docker
6. **Push Docker Images** - Push vers Docker Hub
7. **Upload Essential Files** - Upload les fichiers nécessaires
8. **Deploy Backend** - Déploie sur le serveur

### Modification du `jenkins-config.yml` pour supporter les fichiers d'environnement

Mettez à jour la section `deployment` :

```yaml
deployment:
  remote_path: "/tmp/deployment/backend"
  
  files_to_upload:
    - "docker-compose.yml"
    - "Dockerfile"
    - "nginx/*"
  
  # Configuration par environnement
  env_files:
    dev:
      source: ".env.test"
      target: ".env"
    main:
      source: ".env.prod"
      target: ".env"
  
  # Docker compose files par environnement
  compose_files:
    dev: "docker-compose.test.yml"
    main: "docker-compose.prod.yml"
  
  deploy_commands:
    - "docker-compose -f docker-compose.${ENV_NAME}.yml down -v"
    - "docker-compose -f docker-compose.${ENV_NAME}.yml pull"
    - "docker-compose -f docker-compose.${ENV_NAME}.yml up -d"
```

## 🚀 Déploiement

### Déploiement Automatique

Le déploiement se fait automatiquement via Jenkins lors d'un push sur :
- **Branche `dev`** → Déploie sur l'environnement TEST
- **Branche `main`** → Déploie sur l'environnement PRODUCTION

### Déploiement Manuel

#### Environnement TEST

```bash
# 1. Se connecter au serveur TEST
ssh user@147.93.55.221

# 2. Aller dans le répertoire de déploiement
cd /tmp/deployment/backend

# 3. Copier le fichier .env.test vers .env
cp .env.test .env

# 4. Déployer avec docker-compose
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml pull
docker-compose -f docker-compose.test.yml up -d

# 5. Vérifier les logs
docker-compose -f docker-compose.test.yml logs -f
```

#### Environnement PRODUCTION

```bash
# 1. Se connecter au serveur PRODUCTION
ssh user@31.97.158.68

# 2. Aller dans le répertoire de déploiement
cd /tmp/deployment/backend

# 3. Copier le fichier .env.prod vers .env
cp .env.prod .env

# 4. Déployer avec docker-compose
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 5. Vérifier les logs
docker-compose -f docker-compose.prod.yml logs -f
```

## ✅ Vérifications Post-Déploiement

### Checklist TEST

- [ ] Application accessible sur `http://147.93.55.221:8000`
- [ ] API Swagger accessible
- [ ] Connexion à la base de données fonctionnelle
- [ ] Migrations appliquées
- [ ] Fichiers statiques servis correctement
- [ ] Logs sans erreurs critiques
- [ ] Rate limiting fonctionnel
- [ ] Authentification JWT fonctionnelle

### Checklist PRODUCTION

- [ ] Application accessible sur HTTPS uniquement
- [ ] `DEBUG=False` vérifié
- [ ] Headers de sécurité présents (vérifier avec [SecurityHeaders.com](https://securityheaders.com))
- [ ] SSL/TLS configuré et valide
- [ ] CORS configuré correctement
- [ ] Rate limiting actif
- [ ] Logs sans données sensibles
- [ ] Backups de base de données configurés
- [ ] Monitoring configuré
- [ ] Certificat SSL valide et non expiré

### Commandes de Vérification

```bash
# Vérifier les containers
docker ps

# Vérifier les logs
docker-compose -f docker-compose.{test|prod}.yml logs -f web

# Vérifier les variables d'environnement
docker-compose -f docker-compose.{test|prod}.yml exec web env | grep DJANGO

# Tester l'API
curl -X GET http://localhost:8000/api/health/  # Si endpoint health existe
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Vérifier les headers de sécurité
curl -I https://votre-domaine.com
```

## 🔐 Sécurité par Environnement

### TEST
- Debug activé pour faciliter le développement
- SSL optionnel
- CORS plus permissif
- Logs détaillés

### PRODUCTION
- Debug désactivé (obligatoire)
- SSL obligatoire
- CORS strict
- Headers de sécurité complets
- Rate limiting strict
- Logs sans données sensibles

## 📝 Notes Importantes

1. **Ne jamais commiter les fichiers `.env`** - Ils doivent être dans `.gitignore`
2. **Générer des clés secrètes uniques** pour chaque environnement
3. **Utiliser des mots de passe forts** pour la base de données en production
4. **Configurer les backups** réguliers en production
5. **Monitorer les logs** régulièrement
6. **Tester en TEST** avant de déployer en PRODUCTION

## 🆘 Dépannage

### Problème : Container ne démarre pas

```bash
# Vérifier les logs
docker-compose -f docker-compose.{test|prod}.yml logs web

# Vérifier les variables d'environnement
docker-compose -f docker-compose.{test|prod}.yml config
```

### Problème : Erreurs de migration

```bash
# Exécuter les migrations manuellement
docker-compose -f docker-compose.{test|prod}.yml exec web python manage.py migrate
```

### Problème : Erreurs de permissions

```bash
# Vérifier les permissions des volumes
docker-compose -f docker-compose.{test|prod}.yml exec web ls -la /app/staticfiles
```

## 📚 Ressources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [SECURITY.md](./SECURITY.md) - Guide de sécurité du projet

