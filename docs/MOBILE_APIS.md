# 📱 API Mobile – Documentation complète

Base URL: `/mobile/api/`

- Authentification requise: `Authorization: Bearer <token>` sur les endpoints marqués IsAuthenticated
- Format: JSON (UTF-8)

## 1) Authentification

### 1.1 POST `/auth/login/`
- Permissions: AllowAny
- Body:
```json
{
  "username": "john.doe",
  "password": "password123"
}
```
- Réponse 200:
```json
{
  "success": true,
  "user": {
    "user_id": 1,
    "nom": "Doe",
    "prenom": "John",
    "username": "john.doe"
  }
}
```
- Réponse 400:
```json
{
  "success": false,
  "error": "Identifiants invalides"
}
```

### 1.2 POST `/auth/jwt-login/`
- Permissions: AllowAny
- Body: identique à `/auth/login/`
- Réponse 200:
```json
{
  "success": true,
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "user_id": 1,
    "nom": "Doe",
    "prenom": "John"
  }
}
```
- Réponse 400/500: message d’erreur formaté

### 1.3 POST `/auth/logout/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Réponse 200:
```json
{
  "success": true,
  "message": "Déconnexion réussie"
}
```

### 1.4 POST `/auth/refresh/`
- Permissions: AllowAny
- Body:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
- Réponse 200:
```json
{
  "success": true,
  "access": "<nouveau_access>",
  "refresh": "<nouveau_refresh>"
}
```

## 2) Synchronisation

### 2.1 GET `/sync/data/user/{user_id}/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Query params optionnels:
  - `inventory_id` (int)
- Réponse 200 (exemple abrégé):
```json
{
  "success": true,
  "inventories": [ {"id": 10} ],
  "countings": [ {"id": 100} ],
  "jobs": [ {"id": 1000} ],
  "assignments": [ {"id": 2000} ],
  "products": [ {"id": 3000} ],
  "locations": [ {"id": 4000} ],
  "stocks": [ {"id": 5000} ]
}
```

### 2.2 POST `/sync/upload/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Body:
```json
{
  "sync_id": "sync_123456789",
  "countings": [
    { "counting_id": 1, "product_id": 1, "location_id": 1, "quantity": 10, "status": "COMPLETED" }
  ],
  "assignments": [
    { "assignment_id": 1, "status": "COMPLETED", "completion_date": "2024-01-01T10:00:00Z" }
  ]
}
```
- Réponse 200:
```json
{
  "success": true,
  "message": "Upload réussi",
  "countings_processed": 5,
  "assignments_processed": 3,
  "errors": []
}
```

## 3) Inventaire / Utilisateurs

### 3.1 GET `/inventory/{inventory_id}/users/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Réponse 200:
```json
{
  "success": true,
  "data": { "users": [ { "id": 1, "username": "john.doe" } ] }
}
```

## 4) Données liées à l’utilisateur

### 4.1 GET `/user/{user_id}/products/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Réponse 200:
```json
{
  "success": true,
  "data": { "products": [ { "id": 1, "short_description": "PROD A" } ] }
}
```

### 4.2 GET `/user/{user_id}/locations/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Réponse 200:
```json
{
  "success": true,
  "data": { "locations": [ { "id": 1, "code": "A-01" } ] }
}
```

### 4.3 GET `/user/{user_id}/stocks/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Réponse 200:
```json
{
  "success": true,
  "data": { "stocks": [ { "product_id": 1, "location_id": 1, "qty": 12 } ] }
}
```

## 5) Assignments & Jobs

### 5.1 POST `/user/{user_id}/job/{job_id}/status/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Effet: met l’assignment relié au job en statut `ENTAME` et synchronise le job
- Réponse 200:
```json
{
  "success": true,
  "data": {
    "assignment_id": 1,
    "job_id": 10,
    "new_status": "ENTAME",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

### 5.2 POST `/job/{job_id}/close/{assignment_id}/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Effet: clôture le job après vérification que tous les emplacements sont terminés
- Réponse 200 (exemple):
```json
{
  "success": true,
  "message": "Job clôturé",
  "job_id": 10,
  "assignment_id": 1
}
```

## 6) Comptage (Counting)

### 6.1 POST `/job/{job_id}/counting-detail/`
- Permissions: IsAuthenticated
- Headers: `Authorization: Bearer <token>`
- Body (lot d’items; un seul objet est accepté et converti en liste):
```json
[
  {
    "counting_id": 1,
    "location_id": 1,
    "quantity_inventoried": 10,
    "assignment_id": 1,
    "product_id": 1,
    "dlc": "2024-12-31",
    "n_lot": "LOT123",
    "numeros_serie": [{"n_serie": "NS001"}]
  }
]
```
- Réponse 200 (exemple abrégé):
```json
{
  "success": true,
  "data": {
    "created": 1,
    "details": [ { "counting_detail_id": 1001 } ]
  }
}
```

---

Notes:
- Tous les endpoints protégés nécessitent l’en-tête `Authorization: Bearer <token>`.
- Les erreurs retournent en général `{ "success": false, "error": "message" }` avec le code HTTP approprié (400/401/403/404/500). 