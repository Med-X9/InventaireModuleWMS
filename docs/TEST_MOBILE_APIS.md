# Guide de Test des APIs Mobile

## Table des matières
1. [Prérequis](#prérequis)
2. [Tests avec curl](#tests-avec-curl)
3. [Tests avec Python](#tests-avec-python)
4. [Tests manuels](#tests-manuels)
5. [Dépannage](#dépannage)

---

## Prérequis

### 1. Démarrer le serveur Django
```bash
python manage.py runserver
```

### 2. Vérifier que les URLs sont configurées
Le fichier `config/urls.py` doit contenir :
```python
path('api/mobile/', include('apps.mobile.urls')),
```

### 3. Créer un utilisateur de test (optionnel)
```bash
python manage.py createsuperuser
```

---

## Tests avec curl

### 1. Test de connexion
```bash
curl -X POST http://localhost:8000/api/mobile/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 2. Test de synchronisation (avec token)
```bash
# Remplacez <TOKEN> par le token obtenu du login
curl -X GET http://localhost:8000/api/mobile/sync/data/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>"
```

### 3. Test d'upload (avec token)
```bash
curl -X POST http://localhost:8000/api/mobile/sync/upload/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "sync_id": "test_sync_123456789",
    "countings": [
      {
        "detail_id": "detail_123456789",
        "quantite_comptee": 25,
        "product_web_id": 1,
        "location_web_id": 1,
        "numero_lot": "LOT-TEST-2024",
        "numero_serie": null,
        "dlc": "2024-12-31",
        "compte_par_web_id": 1,
        "date_comptage": "2024-01-15T14:30:00Z"
      }
    ],
    "assignments": [
      {
        "assignment_web_id": 1,
        "status": "ENTAME",
        "entame_date": "2024-01-15T14:30:00Z",
        "date_start": "2024-01-15T14:30:00Z"
      }
    ]
  }'
```

### 4. Test de déconnexion
```bash
curl -X POST http://localhost:8000/api/mobile/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Tests avec Python

### 1. Installer les dépendances
```bash
pip install requests
```

### 2. Exécuter le script de test
```bash
python test_mobile_apis_simple.py
```

### 3. Exécuter le script de test complet
```bash
python test_mobile_apis.py
```

---

## Tests manuels

### 1. Test avec Postman ou Insomnia

#### Login
- **Method:** POST
- **URL:** `http://localhost:8000/api/mobile/auth/login/`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

#### Sync Data
- **Method:** GET
- **URL:** `http://localhost:8000/api/mobile/sync/data/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <TOKEN>`

#### Upload Data
- **Method:** POST
- **URL:** `http://localhost:8000/api/mobile/sync/upload/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <TOKEN>`
- **Body:**
```json
{
  "sync_id": "test_sync_123456789",
  "countings": [
    {
      "detail_id": "detail_123456789",
      "quantite_comptee": 25,
      "product_web_id": 1,
      "location_web_id": 1,
      "numero_lot": "LOT-TEST-2024",
      "numero_serie": null,
      "dlc": "2024-12-31",
      "compte_par_web_id": 1,
      "date_comptage": "2024-01-15T14:30:00Z"
    }
  ],
  "assignments": [
    {
      "assignment_web_id": 1,
      "status": "ENTAME",
      "entame_date": "2024-01-15T14:30:00Z",
      "date_start": "2024-01-15T14:30:00Z"
    }
  ]
}
```

---

## Dépannage

### Erreurs courantes

#### 1. "Inventory object has no attribute 'warehouse'"
**Solution:** ✅ Corrigé dans le code - l'entrepôt est maintenant récupéré via les jobs

#### 2. "ModuleNotFoundError: No module named 'apps.mobile.models'"
**Solution:** ✅ Supprimé l'utilisation des modèles mobile pour éviter les erreurs

#### 3. "Authentication credentials were not provided"
**Solution:** Vérifiez que le header Authorization est correct :
```
Authorization: Bearer <TOKEN>
```

#### 4. "Invalid token"
**Solution:** 
- Vérifiez que le token n'a pas expiré
- Régénérez un nouveau token via le login

#### 5. "ObjectDoesNotExist"
**Solution:** 
- Vérifiez que les IDs utilisés dans les tests existent dans la base de données
- Remplacez les IDs de test par des IDs valides

### Vérification des données

#### 1. Vérifier les inventaires
```python
from apps.inventory.models import Inventory
Inventory.objects.all()
```

#### 2. Vérifier les jobs
```python
from apps.inventory.models import Job
Job.objects.all()
```

#### 3. Vérifier les produits
```python
from apps.masterdata.models import Product
Product.objects.filter(Product_Status='ACTIVE')
```

#### 4. Vérifier les emplacements
```python
from apps.masterdata.models import Location
Location.objects.filter(is_active=True)
```

---

## Résultats attendus

### Login réussi
```json
{
  "success": true,
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "user_id": 1,
    "nom": "Admin",
    "prenom": "User"
  }
}
```

### Sync Data réussi
```json
{
  "success": true,
  "sync_id": "sync_1_1642345678",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "inventories": [...],
    "jobs": [...],
    "assignments": [...],
    "countings": [...],
    "products": [...],
    "locations": [...],
    "stocks": [...]
  }
}
```

### Upload réussi
```json
{
  "success": true,
  "sync_id": "test_sync_123456789",
  "uploaded_count": 2,
  "errors": [],
  "conflicts": []
}
```

---

## Notes importantes

1. **Authentification obligatoire** : Toutes les APIs (sauf login) nécessitent un token valide
2. **IDs de test** : Remplacez les IDs de test par des IDs valides de votre base de données
3. **Données de test** : Assurez-vous d'avoir des données de test dans votre base de données
4. **Logs** : Les logs sont affichés dans la console Django
5. **Performance** : L'API sync_data peut être lente avec beaucoup de données 