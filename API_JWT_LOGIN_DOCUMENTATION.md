# API JWT Login - Documentation

## 🎯 Vue d'ensemble

Cette API hérite directement de `TokenObtainPairView` de `SIMPLE_JWT` et retourne une réponse formatée selon vos spécifications. Elle combine la puissance de SIMPLE_JWT avec un format de réponse personnalisé.

## 🔗 Endpoint

```
POST /api/mobile/auth/jwt-login/
```

## 📋 Paramètres de requête

### Body (JSON)

```json
{
  "username": "string",    // Nom d'utilisateur (obligatoire)
  "password": "string"     // Mot de passe (obligatoire)
}
```

## 📤 Réponse

### Succès (200 OK)

```json
{
  "success": true,
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "user_id": 5,
    "nom": "Dupont",
    "prenom": "Jean"
  }
}
```

### Erreur (400 Bad Request)

```json
{
  "success": false,
  "error": "Identifiants invalides",
  "details": {
    "username": ["Ce champ est obligatoire."],
    "password": ["Ce champ est obligatoire."]
  }
}
```

### Erreur serveur (500 Internal Server Error)

```json
{
  "success": false,
  "error": "Erreur interne du serveur",
  "details": "Message d'erreur détaillé"
}
```

## 🏗️ Architecture

### Classes impliquées

1. **`JWTLoginView`** : Vue principale qui hérite de `TokenObtainPairView`
2. **`CustomTokenObtainPairSerializer`** : Serializer personnalisé qui étend `TokenObtainPairSerializer`

### Flux de traitement

1. **Réception de la requête** → `JWTLoginView.post()`
2. **Validation des données** → `CustomTokenObtainPairSerializer.validate()`
3. **Authentification SIMPLE_JWT** → Génération des tokens
4. **Formatage de la réponse** → Ajout des informations utilisateur
5. **Retour de la réponse** → Format JSON personnalisé

## 🔐 Sécurité

- **Héritage SIMPLE_JWT** : Bénéficie de toutes les fonctionnalités de sécurité de SIMPLE_JWT
- **Validation automatique** : Validation des identifiants par Django
- **Gestion des erreurs** : Gestion sécurisée des erreurs sans fuite d'informations
- **Tokens JWT** : Tokens sécurisés et signés

## 📱 Utilisation

### cURL

```bash
curl -X POST http://localhost:8000/api/mobile/auth/jwt-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### JavaScript (Fetch)

```javascript
const response = await fetch('/api/mobile/auth/jwt-login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});

const data = await response.json();
console.log(data);
```

### Python (requests)

```python
import requests

response = requests.post(
    'http://localhost:8000/api/mobile/auth/jwt-login/',
    json={
        'username': 'admin',
        'password': 'admin123'
    }
)

data = response.json()
print(data)
```

## 🧪 Tests

### Test avec identifiants valides

```bash
python test_jwt_login_api.py
```

### Test manuel

1. Démarrer le serveur Django : `python manage.py runserver`
2. Utiliser cURL ou Postman pour tester l'endpoint
3. Vérifier le format de la réponse

## 🔧 Configuration

### Dépendances requises

- `djangorestframework-simplejwt`
- `django-rest-framework`

### Fichiers de configuration

- **Vue** : `apps/mobile/views/auth/jwt_login_view.py`
- **URL** : `apps/mobile/urls.py`
- **Import** : `apps/mobile/views/auth/__init__.py`

## 🚀 Avantages

1. **Héritage SIMPLE_JWT** : Bénéficie de toutes les fonctionnalités avancées
2. **Format de réponse personnalisé** : Réponse exactement selon vos spécifications
3. **Sécurité renforcée** : Validation et gestion d'erreurs robustes
4. **Maintenance facile** : Code clair et bien structuré
5. **Extensibilité** : Facile d'ajouter de nouveaux champs utilisateur

## 🔍 Dépannage

### Erreurs courantes

1. **500 Internal Server Error** : Vérifier la configuration SIMPLE_JWT
2. **400 Bad Request** : Vérifier le format des données envoyées
3. **401 Unauthorized** : Vérifier les identifiants utilisateur

### Logs

Les erreurs sont loggées dans la console Django. Vérifiez les logs pour plus de détails.

## 📈 Évolutions futures

- Ajout de champs utilisateur supplémentaires
- Support de l'authentification à deux facteurs
- Intégration avec des services d'authentification externes
- Métriques et monitoring des connexions

## 📞 Support

Pour toute question ou problème avec cette API, consultez :
- La documentation SIMPLE_JWT
- Les logs Django
- Le code source de la vue et du serializer
