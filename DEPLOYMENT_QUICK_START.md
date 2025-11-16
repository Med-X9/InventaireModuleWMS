# Guide de Déploiement Rapide - Test et Production

Guide rapide pour déployer l'application sur les environnements TEST et PRODUCTION.

## 🚀 Déploiement Automatique (Recommandé)

Le déploiement se fait automatiquement via Jenkins lors d'un push Git :

- **Push sur branche `dev`** → Déploie automatiquement sur **TEST** (`147.93.55.221`)
- **Push sur branche `main`** → Déploie automatiquement sur **PRODUCTION** (`31.97.158.68`)

### Prérequis

1. **Jenkins configuré** avec les credentials :
   - `git-cred-company-tk` - Credentials Git
   - `docker-hub-company` - Credentials Docker Hub
   - `dev-test-creds` - Credentials serveur TEST
   - `prod-creds` - Credentials serveur PRODUCTION

2. **Fichiers d'environnement** créés sur les serveurs :
   - `.env.test` sur le serveur TEST
   - `.env.prod` sur le serveur PRODUCTION

## 📝 Configuration Initiale

### 1. Créer les fichiers d'environnement

#### Sur le serveur TEST (`147.93.55.221`)

```bash
# Se connecter au serveur
ssh user@147.93.55.221

# Créer le répertoire de déploiement
mkdir -p /tmp/deployment/backend
cd /tmp/deployment/backend

# Créer le fichier .env.test
nano .env.test
# Copier le contenu de .env.test.example et adapter les valeurs
```

#### Sur le serveur PRODUCTION (`31.97.158.68`)

```bash
# Se connecter au serveur
ssh user@31.97.158.68

# Créer le répertoire de déploiement
mkdir -p /tmp/deployment/backend
cd /tmp/deployment/backend

# Créer le fichier .env.prod
nano .env.prod
# Copier le contenu de .env.prod.example et adapter les valeurs
```

### 2. Générer les clés secrètes

```bash
# Générer une clé secrète Django
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**⚠️ Important** : Utiliser des clés différentes pour TEST et PRODUCTION !

### 3. Configurer les variables d'environnement critiques

#### TEST (.env.test)
```bash
IS_PRODUCTION=False
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=<clé-générée>
DJANGO_ALLOWED_HOSTS=147.93.55.221,localhost,127.0.0.1
IMAGE_TAG=dev-latest
```

#### PRODUCTION (.env.prod)
```bash
IS_PRODUCTION=True
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<clé-générée-UNIQUE>
DJANGO_ALLOWED_HOSTS=31.97.158.68,votre-domaine.com,www.votre-domaine.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://votre-domaine.com
IMAGE_TAG=prod-latest
```

## 🔄 Déploiement Manuel

### Déploiement sur TEST

```bash
# 1. Se connecter au serveur TEST
ssh user@147.93.55.221

# 2. Aller dans le répertoire de déploiement
cd /tmp/deployment/backend

# 3. S'assurer que .env.test existe et est renommé en .env
cp .env.test .env

# 4. Déployer
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml pull
docker-compose -f docker-compose.test.yml up -d

# 5. Vérifier les logs
docker-compose -f docker-compose.test.yml logs -f web
```

### Déploiement sur PRODUCTION

```bash
# 1. Se connecter au serveur PRODUCTION
ssh user@31.97.158.68

# 2. Aller dans le répertoire de déploiement
cd /tmp/deployment/backend

# 3. S'assurer que .env.prod existe et est renommé en .env
cp .env.prod .env

# 4. Déployer
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 5. Vérifier les logs
docker-compose -f docker-compose.prod.yml logs -f web
```

## ✅ Vérifications Post-Déploiement

### Checklist TEST

```bash
# Vérifier que les containers tournent
docker ps | grep inventaire

# Vérifier les logs
docker-compose -f docker-compose.test.yml logs --tail=50 web

# Tester l'API
curl http://147.93.55.221:8000/api/

# Vérifier les migrations
docker-compose -f docker-compose.test.yml exec web python manage.py showmigrations

# Vérifier les variables d'environnement
docker-compose -f docker-compose.test.yml exec web env | grep DJANGO
```

### Checklist PRODUCTION

```bash
# Vérifier que les containers tournent
docker ps | grep inventaire

# Vérifier les logs
docker-compose -f docker-compose.prod.yml logs --tail=50 web

# Vérifier que DEBUG=False
docker-compose -f docker-compose.prod.yml exec web python -c "from django.conf import settings; print('DEBUG:', settings.DEBUG)"

# Vérifier les headers de sécurité
curl -I https://votre-domaine.com

# Tester l'API
curl https://votre-domaine.com/api/

# Vérifier que SSL est activé
curl -I https://votre-domaine.com | grep -i "strict-transport-security"
```

## 🔧 Commandes Utiles

### Voir les logs en temps réel

```bash
# TEST
docker-compose -f docker-compose.test.yml logs -f

# PRODUCTION
docker-compose -f docker-compose.prod.yml logs -f
```

### Redémarrer les services

```bash
# TEST
docker-compose -f docker-compose.test.yml restart

# PRODUCTION
docker-compose -f docker-compose.prod.yml restart
```

### Arrêter les services

```bash
# TEST
docker-compose -f docker-compose.test.yml down

# PRODUCTION
docker-compose -f docker-compose.prod.yml down
```

### Exécuter des commandes Django

```bash
# TEST
docker-compose -f docker-compose.test.yml exec web python manage.py <command>

# PRODUCTION
docker-compose -f docker-compose.prod.yml exec web python manage.py <command>
```

### Exemples de commandes Django

```bash
# Créer un superutilisateur
docker-compose -f docker-compose.{test|prod}.yml exec web python manage.py createsuperuser

# Appliquer les migrations
docker-compose -f docker-compose.{test|prod}.yml exec web python manage.py migrate

# Collecter les fichiers statiques
docker-compose -f docker-compose.{test|prod}.yml exec web python manage.py collectstatic --noinput
```

## 🐛 Dépannage

### Problème : Container ne démarre pas

```bash
# Vérifier les logs détaillés
docker-compose -f docker-compose.{test|prod}.yml logs web

# Vérifier les variables d'environnement
docker-compose -f docker-compose.{test|prod}.yml config

# Vérifier que le fichier .env existe
ls -la /tmp/deployment/backend/.env
```

### Problème : Erreurs de connexion à la base de données

```bash
# Vérifier que la base de données est accessible
docker-compose -f docker-compose.{test|prod}.yml exec web python manage.py dbshell

# Vérifier les variables d'environnement DB
docker-compose -f docker-compose.{test|prod}.yml exec web env | grep POSTGRES
```

### Problème : Erreurs de permissions

```bash
# Vérifier les permissions des volumes
docker-compose -f docker-compose.{test|prod}.yml exec web ls -la /app/staticfiles
docker-compose -f docker-compose.{test|prod}.yml exec web ls -la /app/media
```

## 📊 Monitoring

### Vérifier l'utilisation des ressources

```bash
# TEST
docker stats inventaire-web-test inventaire-nginx-test

# PRODUCTION
docker stats inventaire-web-prod inventaire-nginx-prod
```

### Vérifier l'espace disque

```bash
df -h
docker system df
```

## 🔐 Sécurité

### Vérifier les settings de sécurité en PRODUCTION

```bash
docker-compose -f docker-compose.prod.yml exec web python -c "
from django.conf import settings
print('DEBUG:', settings.DEBUG)
print('SECURE_SSL_REDIRECT:', settings.SECURE_SSL_REDIRECT)
print('SESSION_COOKIE_SECURE:', settings.SESSION_COOKIE_SECURE)
print('CSRF_COOKIE_SECURE:', settings.CSRF_COOKIE_SECURE)
"
```

## 📚 Documentation Complète

Pour plus de détails, consultez :
- [CI-CD_IMPLEMENTATION.md](./CI-CD_IMPLEMENTATION.md) - Guide complet d'implémentation
- [SECURITY.md](./SECURITY.md) - Guide de sécurité

