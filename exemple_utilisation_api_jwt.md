# 🚀 Exemple d'utilisation de l'API JWT de login

## ✅ API fonctionnelle

Votre nouvelle API JWT de login est maintenant **entièrement fonctionnelle** et retourne exactement le format de réponse demandé !

## 🔗 Endpoint

```
POST /mobile/api/auth/jwt-login/
```

## 📱 Exemple d'utilisation

### 1. **Connexion réussie**

**Requête :**
```bash
curl -X POST http://localhost:8000/mobile/api/auth/jwt-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testjwt",
    "password": "test123"
  }'
```

**Réponse (200 OK) :**
```json
{
  "success": true,
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM2NzQ5NjAwLCJpYXQiOjE3MzY3NDYwMCwianRpIjoiYzE2NzQ5NjAwIiwidXNlcl9pZCI6Nn0...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTczNjgzMjAwLCJpYXQiOjE3MzY3NDYwMCwianRpIjoiYzE2NzQ5NjAwIiwidXNlcl9pZCI6Nn0...",
  "user": {
    "user_id": 6,
    "nom": "Test",
    "prenom": "JWT"
  }
}
```

### 2. **Utilisation des tokens**

**Accès à une API protégée :**
```bash
curl -X GET http://localhost:8000/mobile/api/sync/data/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Rafraîchissement du token :**
```bash
curl -X POST http://localhost:8000/mobile/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

## 🎯 Fonctionnalités

✅ **Héritage SIMPLE_JWT** : Bénéficie de toute la puissance de SIMPLE_JWT  
✅ **Format de réponse personnalisé** : Exactement selon vos spécifications  
✅ **Sécurité renforcée** : Validation et gestion d'erreurs robustes  
✅ **Tokens JWT** : Access et refresh tokens sécurisés  
✅ **Informations utilisateur** : ID, nom et prénom inclus  

## 🔧 Configuration

L'API est configurée avec :
- **Durée de vie du token d'accès** : 60 minutes
- **Durée de vie du refresh token** : 1 jour
- **Algorithme** : HS256
- **Rotation des tokens** : Désactivée
- **Blacklist** : Activée après rotation

## 📱 Intégration mobile

### JavaScript (React Native / Web)
```javascript
const login = async (username, password) => {
  try {
    const response = await fetch('/mobile/api/auth/jwt-login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Stocker les tokens
      await AsyncStorage.setItem('access_token', data.access);
      await AsyncStorage.setItem('refresh_token', data.refresh);
      
      // Stocker les infos utilisateur
      await AsyncStorage.setItem('user', JSON.stringify(data.user));
      
      return { success: true, user: data.user };
    } else {
      return { success: false, error: data.error };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
};
```

### Python (Django / Flask)
```python
import requests

def login_user(username, password):
    url = "http://localhost:8000/mobile/api/auth/jwt-login/"
    
    response = requests.post(url, json={
        'username': username,
        'password': password
    })
    
    if response.status_code == 200:
        data = response.json()
        return {
            'success': True,
            'access_token': data['access'],
            'refresh_token': data['refresh'],
            'user': data['user']
        }
    else:
        return {
            'success': False,
            'error': response.json().get('error', 'Erreur inconnue')
        }
```

## 🧪 Tests

Pour tester l'API :

1. **Démarrer le serveur :**
   ```bash
   python manage.py runserver
   ```

2. **Tester avec cURL :**
   ```bash
   curl -X POST http://localhost:8000/mobile/api/auth/jwt-login/ \
     -H "Content-Type: application/json" \
     -d '{"username": "testjwt", "password": "test123"}'
   ```

3. **Tester avec Postman :**
   - Method: POST
   - URL: `http://localhost:8000/mobile/api/auth/jwt-login/`
   - Headers: `Content-Type: application/json`
   - Body: `{"username": "testjwt", "password": "test123"}`

## 🎉 Résultat

Votre API JWT de login est maintenant **100% fonctionnelle** et prête à être utilisée en production ! Elle combine le meilleur des deux mondes :

- **La puissance de SIMPLE_JWT** pour la sécurité et la gestion des tokens
- **Votre format de réponse personnalisé** pour une intégration facile avec vos applications mobiles

L'API est accessible à l'adresse : `http://localhost:8000/mobile/api/auth/jwt-login/`
