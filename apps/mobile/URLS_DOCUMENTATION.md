# 📱 API Mobile - Documentation Complète des URLs

## 🏗️ **Architecture des URLs**

L'API mobile est organisée en modules fonctionnels avec des URLs RESTful :

```
/mobile/api/
├── auth/           # Authentification
├── sync/           # Synchronisation
├── inventory/      # Gestion des inventaires
├── user/           # Données utilisateur
├── assignment/     # Assignations
└── counting/       # Comptages
```

---

## 🔐 **1. AUTHENTIFICATION (`/mobile/api/auth/`)**

### **1.1 Connexion Standard**
```
POST /mobile/api/auth/login/
```
**Description :** Authentification avec nom d'utilisateur et mot de passe  
**Permissions :** `AllowAny` (pas d'authentification requise)  
**Body :**
```json
{
  "username": "mobile",
  "password": "user1234"
}
```
**Réponse (200) :**
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

### **1.2 Connexion JWT**
```
POST /mobile/api/auth/jwt-login/
```
**Description :** Authentification JWT avec informations utilisateur étendues  
**Permissions :** `AllowAny`  
**Body :** Identique à `/login/`  
**Réponse :** Tokens JWT + informations utilisateur complètes

### **1.3 Déconnexion**
```
POST /mobile/api/auth/logout/
```
**Description :** Déconnexion sécurisée de l'utilisateur  
**Permissions :** `IsAuthenticated`  
**Headers :** `Authorization: Bearer <token>`

### **1.4 Rafraîchissement de Token**
```
POST /mobile/api/auth/refresh/
```
**Description :** Renouvellement d'un token d'accès expiré  
**Permissions :** `AllowAny`  
**Body :**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## 🔄 **2. SYNCHRONISATION (`/mobile/api/sync/`)**

### **2.1 Synchronisation Générale**
```
GET /mobile/api/sync/data/
```
**Description :** Récupère toutes les données nécessaires pour l'application mobile  
**Permissions :** `IsAuthenticated`  
**Headers :** `Authorization: Bearer <token>`  
**Query Parameters :**
- `inventory_id` (int, optionnel) : ID d'inventaire spécifique

**Réponse (200) :**
```json
{
  "success": true,
  "sync_id": "sync_123_1703123456",
  "timestamp": "2023-12-21T10:30:45.123456Z",
  "data": {
    "inventories": [...],
    "jobs": [...],
    "assignments": [...],
    "countings": [...]
  }
}
```

### **2.2 Synchronisation par Utilisateur**
```
GET /mobile/api/sync/data/user/{user_id}/
```
**Description :** Synchronisation pour un utilisateur spécifique  
**Permissions :** `IsAuthenticated`  
**URL Parameters :**
- `user_id` (int) : ID de l'utilisateur

### **2.3 Upload de Données**
```
POST /mobile/api/sync/upload/
```
**Description :** Upload des données modifiées côté mobile  
**Permissions :** `IsAuthenticated`  
**Body :**
```json
{
  "sync_id": "sync_123_1703123456",
  "countings": [
    {
      "counting_id": 1,
      "product_id": 1,
      "location_id": 1,
      "quantity": 10,
      "status": "COMPLETED"
    }
  ],
  "assignments": [
    {
      "assignment_id": 1,
      "status": "COMPLETED",
      "completion_date": "2024-01-01T10:00:00Z"
    }
  ]
}
```

---

## 📦 **3. INVENTAIRES (`/mobile/api/inventory/`)**

### **3.1 Utilisateurs d'un Inventaire**
```
GET /mobile/api/inventory/{inventory_id}/users/
```
**Description :** Récupère les utilisateurs du même compte qu'un inventaire  
**Permissions :** `IsAuthenticated`  
**URL Parameters :**
- `inventory_id` (int) : ID de l'inventaire

**Réponse (200) :**
```json
{
  "success": true,
  "inventory_id": 1,
  "timestamp": "2023-12-21T10:30:45Z",
  "data": {
    "users": [
      {
        "id": 1,
        "username": "john.doe",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com"
      }
    ]
  }
}
```

---

## 👤 **4. DONNÉES UTILISATEUR (`/mobile/api/user/`)**

### **4.1 Produits d'un Utilisateur**
```
GET /mobile/api/user/{user_id}/products/
```
**Description :** Récupère les produits du même compte qu'un utilisateur  
**Permissions :** `IsAuthenticated`  
**URL Parameters :**
- `user_id` (int) : ID de l'utilisateur

### **4.2 Emplacements d'un Utilisateur**
```
GET /mobile/api/user/{user_id}/locations/
```
**Description :** Récupère les emplacements du même compte qu'un utilisateur  
**Permissions :** `IsAuthenticated`  
**URL Parameters :**
- `user_id` (int) : ID de l'utilisateur

### **4.3 Stocks d'un Utilisateur**
```
GET /mobile/api/user/{user_id}/stocks/
```
**Description :** Récupère les stocks du même compte qu'un utilisateur  
**Permissions :** `IsAuthenticated`  
**URL Parameters :**
- `user_id` (int) : ID de l'utilisateur

---

## 📋 **5. ASSIGNATIONS (`/mobile/api/assignment/`)**

### **5.1 Mise à Jour du Statut d'Assignation**
```
PUT /mobile/api/user/{user_id}/assignment/{assignment_id}/status/
```
**Description :** Met à jour le statut d'une assignation  
**Permissions :** `IsAuthenticated`  
**URL Parameters :**
- `user_id` (int) : ID de l'utilisateur
- `assignment_id` (int) : ID de l'assignation

**Body :**
```json
{
  "status": "COMPLETED",
  "completion_date": "2024-01-01T10:00:00Z",
  "notes": "Comptage terminé avec succès"
}
```

---

## 🔢 **6. COMPTAGES (`/mobile/api/counting/`)**

### **6.1 Gestion des Détails de Comptage**
```
POST /mobile/api/counting-detail/
GET /mobile/api/counting-detail/
PUT /mobile/api/counting-detail/
```
**Description :** CRUD pour les CountingDetail et NumeroSerie  
**Permissions :** `IsAuthenticated`  
**Fonctionnalités :**
- Création de nouveaux CountingDetail
- Mise à jour des CountingDetail existants
- Gestion des NumeroSerie associés
- Validation des données selon le mode de comptage
- Support des opérations en lot

**Body (POST) :**
```json
{
  "counting_id": 1,
  "product_id": 1,
  "location_id": 1,
  "quantity": 10,
  "status": "COMPLETED",
  "numero_series": [
    {
      "serial_number": "SN123456",
      "status": "ACTIVE"
    }
  ]
}
```

---

## 🔧 **Configuration et Utilisation**

### **Base URL**
```
http://localhost:8000/mobile/api/
```

### **Authentification**
Toutes les endpoints (sauf `/auth/login/`, `/auth/jwt-login/`, `/auth/refresh/`) nécessitent :
```http
Authorization: Bearer <access_token>
```

### **Content-Type**
```http
Content-Type: application/json
```

### **Codes de Réponse**
- **200** : Succès
- **201** : Créé avec succès
- **400** : Erreur de validation
- **401** : Non authentifié
- **404** : Ressource non trouvée
- **500** : Erreur interne du serveur

---

## 📊 **Exemples d'Utilisation**

### **1. Connexion et Synchronisation**
```bash
# 1. Connexion
curl -X POST http://localhost:8000/mobile/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "mobile", "password": "user1234"}'

# 2. Synchronisation (avec le token reçu)
curl -X GET http://localhost:8000/mobile/api/sync/data/ \
  -H "Authorization: Bearer <access_token>"
```

### **2. Upload de Données**
```bash
curl -X POST http://localhost:8000/mobile/api/sync/upload/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_id": "sync_123_1703123456",
    "countings": [{"counting_id": 1, "quantity": 10}]
  }'
```

### **3. Gestion des Assignations**
```bash
curl -X PUT http://localhost:8000/mobile/api/user/123/assignment/456/status/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "COMPLETED"}'
```

---

## 🏷️ **Tags Swagger**

- **Authentification Mobile** : Endpoints d'auth
- **Synchronisation Mobile** : Endpoints de sync
- **Gestion Mobile** : Endpoints de données

---

## ⚡ **Optimisations**

- **Synchronisation en une seule requête** pour optimiser les performances
- **Gestion des erreurs individuelles** sans interruption globale
- **Support des opérations en lot** pour les uploads
- **Validation côté serveur** pour la cohérence des données
- **Logging détaillé** pour le debugging

