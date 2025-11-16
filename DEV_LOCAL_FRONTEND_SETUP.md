# Configuration Backend Dev (147.93.55.221) + Frontend Local

Guide pour configurer le backend sur le serveur de dev (147.93.55.221) avec HTTPS, tout en permettant au frontend de se développer localement (localhost).

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  Serveur Dev (147.93.55.221)    │
│  Backend Django (HTTPS)          │
│  https://147.93.55.221/api/     │
└─────────────────────────────────┘
              ▲
              │ HTTPS
              │
┌─────────────┴─────────────┐
│  Machine Locale            │
│  Frontend (localhost:3000) │
│  http://localhost:3000     │
└────────────────────────────┘
```

## ⚙️ Configuration Backend (Serveur Dev)

### Fichier `.env` sur le serveur (147.93.55.221)

```bash
# Aller sur le serveur
ssh root@147.93.55.221
cd /tmp/deployment/backend
nano .env
```

### Configuration complète pour `.env` :

```bash
# ============================================
# Configuration Django - DEV
# ============================================
IS_PRODUCTION=False
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=votre-clé-secrète-ici
DJANGO_ALLOWED_HOSTS=147.93.55.221,localhost,127.0.0.1

# ============================================
# Sécurité SSL/TLS - ACTIVÉ
# ============================================
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Origines CSRF autorisées
# HTTPS pour le serveur + HTTP pour localhost (développement)
CSRF_TRUSTED_ORIGINS=https://147.93.55.221,http://localhost:3000,http://127.0.0.1:3000

# IMPORTANT : Si derrière Nginx
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================
# CORS - Configuration pour Frontend Local
# ============================================
CORS_ALLOW_ALL_ORIGINS=False

# Origines autorisées :
# - HTTPS pour le serveur dev
# - HTTP localhost pour le frontend en développement local
# - Ports communs : 3000 (React), 5173 (Vite), 8080 (Vue CLI)
CORS_ALLOWED_ORIGINS=https://147.93.55.221,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://localhost:8080

CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=authorization,content-type
```

### Points importants :

1. **CORS_ALLOWED_ORIGINS** : Inclut `http://localhost:3000` (ou le port de votre frontend)
2. **CSRF_TRUSTED_ORIGINS** : Inclut aussi `http://localhost:3000` pour les requêtes POST
3. **CORS_ALLOW_CREDENTIALS=True** : Nécessaire pour envoyer les cookies/tokens

## 🖥️ Configuration Frontend Local

### Variables d'environnement Frontend

Créez un fichier `.env` dans votre projet frontend :

#### React (.env)
```bash
REACT_APP_API_URL=https://147.93.55.221
REACT_APP_API_BASE_URL=https://147.93.55.221/api
```

#### Vue (.env)
```bash
VUE_APP_API_URL=https://147.93.55.221
VUE_APP_API_BASE_URL=https://147.93.55.221/api
```

#### Next.js (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://147.93.55.221
NEXT_PUBLIC_API_BASE_URL=https://147.93.55.221/api
```

### Configuration Axios/Fetch

#### Exemple avec Axios (React/Vue)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'https://147.93.55.221',
  withCredentials: true, // Important pour envoyer les cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Ajouter le token JWT si disponible
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Gestion des erreurs CORS

Si vous rencontrez des erreurs CORS :

1. **Vérifier que le backend autorise votre origine** :
   ```bash
   # Sur le serveur, vérifier les logs
   docker-compose logs web | grep CORS
   ```

2. **Vérifier les headers dans la réponse** :
   ```javascript
   // Dans la console du navigateur
   fetch('https://147.93.55.221/api/endpoint', {
     credentials: 'include'
   })
   .then(r => {
     console.log('CORS Headers:', r.headers.get('Access-Control-Allow-Origin'));
   });
   ```

## 🔧 Ajustements dans project/settings.py

Les settings sont déjà configurés pour supporter cette configuration. Vérifiez que :

1. **CORS_ALLOW_CREDENTIALS** est bien lu depuis `.env`
2. **CORS_ALLOWED_ORIGINS** accepte les origines locales
3. **CSRF_TRUSTED_ORIGINS** inclut les origines locales

## ✅ Checklist

### Sur le serveur (147.93.55.221)

- [ ] Fichier `.env` configuré avec les origines locales
- [ ] `CORS_ALLOWED_ORIGINS` inclut `http://localhost:3000`
- [ ] `CSRF_TRUSTED_ORIGINS` inclut `http://localhost:3000`
- [ ] `CORS_ALLOW_CREDENTIALS=True`
- [ ] Containers redémarrés : `docker-compose restart`

### En local (Frontend)

- [ ] Fichier `.env` créé avec `API_URL=https://147.93.55.221`
- [ ] Configuration Axios/Fetch avec `withCredentials: true`
- [ ] Port du frontend correspond à celui dans `CORS_ALLOWED_ORIGINS`
- [ ] Test de connexion au backend

## 🧪 Test de connexion

### Depuis le frontend local

```javascript
// Test simple
fetch('https://147.93.55.221/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // Important !
  body: JSON.stringify({
    username: 'test',
    password: 'test'
  })
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

### Vérifier les headers CORS

Dans la console du navigateur (F12) :
```javascript
fetch('https://147.93.55.221/api/', {
  credentials: 'include'
})
.then(r => {
  console.log('Access-Control-Allow-Origin:', r.headers.get('Access-Control-Allow-Origin'));
  console.log('Access-Control-Allow-Credentials:', r.headers.get('Access-Control-Allow-Credentials'));
});
```

## 🐛 Dépannage

### Erreur : "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solution** :
1. Vérifier que `CORS_ALLOWED_ORIGINS` dans `.env` inclut votre origine locale
2. Vérifier que le port correspond (ex: `http://localhost:3000`)
3. Redémarrer les containers : `docker-compose restart`

### Erreur : "Credentials flag is true, but 'Access-Control-Allow-Credentials' header is ''"

**Solution** :
1. Vérifier que `CORS_ALLOW_CREDENTIALS=True` dans `.env`
2. Vérifier que `CORS_ALLOW_ALL_ORIGINS=False` (ne peut pas être True avec credentials)

### Erreur : "CSRF token missing or incorrect"

**Solution** :
1. Ajouter `http://localhost:3000` à `CSRF_TRUSTED_ORIGINS` dans `.env`
2. Pour les requêtes API, utiliser les tokens JWT au lieu de CSRF

## 📝 Notes importantes

1. **HTTPS sur le serveur, HTTP en local** : C'est normal pour le développement
2. **Cookies sécurisés** : Les cookies `SESSION_COOKIE_SECURE=True` ne fonctionneront pas avec HTTP local. Utilisez JWT tokens à la place.
3. **Ports du frontend** : Ajustez `CORS_ALLOWED_ORIGINS` selon le port utilisé (3000, 5173, 8080, etc.)

## 🎯 Résultat attendu

- ✅ Backend accessible via `https://147.93.55.221`
- ✅ Frontend local peut appeler le backend
- ✅ Authentification JWT fonctionne
- ✅ Pas d'erreurs CORS
- ✅ Développement frontend fluide en local

