# Corrections apportées à project/settings.py

## ✅ Corrections effectuées

### 1. Configuration SECURE_PROXY_SSL_HEADER

**Avant :**
```python
# Si derrière un reverse proxy (nginx), décommenter et configurer :
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

**Après :**
```python
# Configuration du proxy SSL (pour Nginx reverse proxy)
# Si SECURE_PROXY_SSL_HEADER est défini dans .env, l'utiliser
# Format attendu dans .env: SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_PROXY_SSL_HEADER_STR = config('SECURE_PROXY_SSL_HEADER', default=None)
if SECURE_PROXY_SSL_HEADER_STR:
    try:
        # Évaluer la chaîne comme un tuple Python
        SECURE_PROXY_SSL_HEADER = eval(SECURE_PROXY_SSL_HEADER_STR)
    except (SyntaxError, ValueError):
        # Si l'évaluation échoue, utiliser la valeur par défaut
        SECURE_PROXY_SSL_HEADER = None
else:
    SECURE_PROXY_SSL_HEADER = None
```

**Avantages :**
- Lit automatiquement depuis le fichier `.env`
- Gestion d'erreur si le format est incorrect
- Plus besoin de décommenter manuellement

### 2. Configuration CORS complète

**Avant :**
```python
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())
CORS_ALLOW_HEADERS = list(default_headers) + [
    'authorization',
]
```

**Après :**
```python
# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())
CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)

# CORS Methods - lire depuis .env ou utiliser les valeurs par défaut
CORS_ALLOW_METHODS_STR = config('CORS_ALLOW_METHODS', default='GET,POST,PUT,PATCH,DELETE,OPTIONS')
CORS_ALLOW_METHODS = [method.strip() for method in CORS_ALLOW_METHODS_STR.split(',') if method.strip()]

# CORS Headers - lire depuis .env ou utiliser les valeurs par défaut
CORS_ALLOW_HEADERS_STR = config('CORS_ALLOW_HEADERS', default='')
if CORS_ALLOW_HEADERS_STR:
    # Si défini dans .env, utiliser la liste fournie
    CORS_ALLOW_HEADERS = [header.strip() for header in CORS_ALLOW_HEADERS_STR.split(',') if header.strip()]
else:
    # Sinon, utiliser les headers par défaut + authorization
    CORS_ALLOW_HEADERS = list(default_headers) + ['authorization']
```

**Avantages :**
- `CORS_ALLOW_CREDENTIALS` lisible depuis `.env`
- `CORS_ALLOW_METHODS` configurable via `.env`
- `CORS_ALLOW_HEADERS` configurable via `.env`
- Valeurs par défaut sensées si non définies

## 📋 Variables d'environnement supportées

### Sécurité SSL/TLS

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `IS_PRODUCTION` | bool | `False` | Mode production |
| `SECURE_SSL_REDIRECT` | bool | `IS_PRODUCTION` | Redirection HTTPS |
| `SESSION_COOKIE_SECURE` | bool | `IS_PRODUCTION` | Cookies de session sécurisés |
| `CSRF_COOKIE_SECURE` | bool | `IS_PRODUCTION` | Cookies CSRF sécurisés |
| `SECURE_HSTS_SECONDS` | int | `31536000` si prod, `0` sinon | Durée HSTS |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | bool | `IS_PRODUCTION` | HSTS inclut sous-domaines |
| `SECURE_HSTS_PRELOAD` | bool | `IS_PRODUCTION` | HSTS preload |
| `CSRF_TRUSTED_ORIGINS` | CSV | `''` | Origines CSRF autorisées |
| `SECURE_PROXY_SSL_HEADER` | str | `None` | Header proxy SSL (tuple) |

### CORS

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `CORS_ALLOW_ALL_ORIGINS` | bool | `False` | Autoriser toutes les origines |
| `CORS_ALLOWED_ORIGINS` | CSV | `''` | Origines autorisées |
| `CORS_ALLOW_CREDENTIALS` | bool | `True` | Autoriser les credentials |
| `CORS_ALLOW_METHODS` | CSV | `GET,POST,PUT,PATCH,DELETE,OPTIONS` | Méthodes autorisées |
| `CORS_ALLOW_HEADERS` | CSV | `''` | Headers autorisés (défaut: headers standards + authorization) |

## 🔧 Exemple de configuration .env

```bash
# Sécurité SSL/TLS
IS_PRODUCTION=True
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://147.93.55.221
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://147.93.55.221
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=authorization,content-type
```

## ✅ Vérification

Pour vérifier que les settings sont correctement chargés :

```bash
# Dans le container Django
docker-compose exec web python manage.py shell

# Puis dans le shell Python :
from django.conf import settings
print("SECURE_SSL_REDIRECT:", settings.SECURE_SSL_REDIRECT)
print("SECURE_PROXY_SSL_HEADER:", settings.SECURE_PROXY_SSL_HEADER)
print("CORS_ALLOW_ALL_ORIGINS:", settings.CORS_ALLOW_ALL_ORIGINS)
print("CORS_ALLOWED_ORIGINS:", settings.CORS_ALLOWED_ORIGINS)
print("CORS_ALLOW_METHODS:", settings.CORS_ALLOW_METHODS)
print("CORS_ALLOW_HEADERS:", settings.CORS_ALLOW_HEADERS)
```

## 🎯 Résultat

Maintenant, toutes les configurations de sécurité et CORS peuvent être gérées via le fichier `.env` sans modifier le code Python, ce qui est plus sécurisé et plus flexible pour différents environnements (dev, test, production).

