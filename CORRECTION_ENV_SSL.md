# Correction du fichier .env pour SSL sur VPS Dev

## 🔧 Corrections à Appliquer

Remplacez les anciennes adresses IP et les configurations HTTP par les valeurs HTTPS pour le VPS de dev (147.93.55.221).

## ❌ Anciennes Valeurs (à supprimer)

```bash
# Security Settings
CSRF_TRUSTED_ORIGINS=http://44.212.20.168,http://174.129.143.211
DJANGO_CSRF_TRUSTED_ORIGINS=http://44.212.20.168,http://174.129.143.211
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://44.212.20.168,http://174.129.143.211
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*
```

## ✅ Nouvelles Valeurs (à utiliser)

```bash
# ============================================
# Sécurité SSL/TLS - ACTIVÉ
# ============================================
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Origines CSRF autorisées (HTTPS uniquement)
CSRF_TRUSTED_ORIGINS=https://147.93.55.221

# IMPORTANT : Si derrière Nginx (reverse proxy)
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================
# CORS - Configuration sécurisée
# ============================================
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://147.93.55.221
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=authorization,content-type
```

## 📝 Commandes sur le VPS

### 1. Éditer le fichier .env

```bash
cd /tmp/deployment/backend
nano .env
```

### 2. Remplacer les sections suivantes

#### Section Security Settings

**Remplacer :**
```bash
CSRF_TRUSTED_ORIGINS=http://44.212.20.168,http://174.129.143.211
DJANGO_CSRF_TRUSTED_ORIGINS=http://44.212.20.168,http://174.129.143.211
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
```

**Par :**
```bash
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CSRF_TRUSTED_ORIGINS=https://147.93.55.221
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
```

#### Section CORS Settings

**Remplacer :**
```bash
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://44.212.20.168,http://174.129.143.211
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*
```

**Par :**
```bash
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://147.93.55.221
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=authorization,content-type
```

### 3. Mettre à jour ALLOWED_HOSTS

```bash
DJANGO_ALLOWED_HOSTS=147.93.55.221,localhost,127.0.0.1
```

### 4. Redémarrer les containers

```bash
cd /tmp/deployment/backend
docker-compose down
docker-compose up -d
```

## 🔍 Vérification

### Vérifier que les changements sont appliqués

```bash
# Vérifier les variables d'environnement dans le container
docker-compose exec web env | grep -E "SECURE_|CORS_|CSRF_"

# Devrait afficher :
# SECURE_SSL_REDIRECT=True
# SESSION_COOKIE_SECURE=True
# CSRF_COOKIE_SECURE=True
# CSRF_TRUSTED_ORIGINS=https://147.93.55.221
# CORS_ALLOW_ALL_ORIGINS=False
# CORS_ALLOWED_ORIGINS=https://147.93.55.221
```

### Tester HTTPS

```bash
# Tester avec curl
curl -I https://147.93.55.221

# Devrait retourner les headers de sécurité
```

## 📋 Checklist

- [ ] Anciennes adresses IP supprimées (44.212.20.168, 174.129.143.211)
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] `CSRF_TRUSTED_ORIGINS=https://147.93.55.221`
- [ ] `SECURE_PROXY_SSL_HEADER` configuré
- [ ] `CORS_ALLOW_ALL_ORIGINS=False`
- [ ] `CORS_ALLOWED_ORIGINS=https://147.93.55.221`
- [ ] `DJANGO_ALLOWED_HOSTS` mis à jour avec 147.93.55.221
- [ ] Containers redémarrés
- [ ] Test HTTPS réussi

## 💡 Note

Le fichier `.env.dev.ssl` dans le repository contient la configuration complète corrigée que vous pouvez utiliser comme référence.

