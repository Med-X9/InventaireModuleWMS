# 📱 API de Synchronisation Mobile - Schéma Complet

## 🔗 **Endpoints**

### 1. **Synchronisation Générale**
```
GET /mobile/api/sync/data/
GET /mobile/api/sync/data/user/{user_id}/
```

### 2. **Upload de Données**
```
POST /mobile/api/sync/upload/
```

---

## 📋 **Paramètres**

### **Paramètres d'URL**
| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `user_id` | `integer` | Non | ID de l'utilisateur pour la synchronisation |

### **Paramètres de Requête**
| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `inventory_id` | `integer` | Non | ID d'inventaire spécifique à synchroniser |

---

## 🔐 **Authentification**

**Type :** Bearer Token (JWT)
```http
Authorization: Bearer <access_token>
```

---

## 📤 **Réponses**

### ✅ **200 - Succès**

```json
{
  "success": true,
  "sync_id": "sync_123_1703123456",
  "timestamp": "2023-12-21T10:30:45.123456Z",
  "data": {
    "inventories": [
      {
        "id": 1,
        "label": "Inventaire L'Oréal",
        "reference": "INV-2023-001",
        "status": "en_realisation",
        "inventory_type": "complet",
        "date": "2023-12-21",
        "created_at": "2023-12-20T09:00:00Z",
        "updated_at": "2023-12-21T10:30:45Z",
        "en_preparation_status_date": "2023-12-20T09:00:00Z",
        "en_realisation_status_date": "2023-12-21T08:00:00Z",
        "termine_status_date": null,
        "cloture_status_date": null,
        "warehouse": {
          "id": 1,
          "warehouse_name": "Entrepôt Central",
          "warehouse_code": "EC001"
        },
        "account": {
          "id": 1,
          "account_name": "L'Oréal France",
          "account_code": "LOR001"
        }
      }
    ],
    "jobs": [
      {
        "id": 1,
        "inventory_id": 1,
        "job_name": "Job Zone A",
        "status": "active",
        "created_at": "2023-12-21T08:00:00Z",
        "updated_at": "2023-12-21T10:30:45Z"
      }
    ],
    "assignments": [
      {
        "id": 1,
        "job_id": 1,
        "user_id": 123,
        "status": "assigned",
        "assigned_at": "2023-12-21T08:30:00Z",
        "completed_at": null,
        "user": {
          "id": 123,
          "username": "john.doe",
          "first_name": "John",
          "last_name": "Doe",
          "email": "john.doe@example.com"
        }
      }
    ],
    "countings": [
      {
        "id": 1,
        "inventory_id": 1,
        "count_mode": "manuel",
        "status": "en_cours",
        "created_at": "2023-12-21T09:00:00Z",
        "updated_at": "2023-12-21T10:30:45Z"
      }
    ]
  }
}
```

### ❌ **400 - Erreur de Paramètre**

```json
{
  "success": false,
  "error": "Paramètre invalide: user_id doit être un entier",
  "error_type": "INVALID_PARAMETER"
}
```

### ❌ **401 - Non Authentifié**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### ❌ **404 - Utilisateur Non Trouvé**

```json
{
  "success": false,
  "error": "Utilisateur non trouvé",
  "error_type": "NOT_FOUND"
}
```

### ❌ **500 - Erreur Interne**

```json
{
  "success": false,
  "error": "Erreur interne du serveur",
  "error_type": "INTERNAL_ERROR"
}
```

---

## 📊 **Structures de Données Détaillées**

### **Inventory**
```json
{
  "id": "integer",
  "label": "string",
  "reference": "string", 
  "status": "string (en_preparation|en_realisation|termine|cloture)",
  "inventory_type": "string (complet|partiel)",
  "date": "date (YYYY-MM-DD)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "en_preparation_status_date": "datetime (ISO 8601) | null",
  "en_realisation_status_date": "datetime (ISO 8601) | null", 
  "termine_status_date": "datetime (ISO 8601) | null",
  "cloture_status_date": "datetime (ISO 8601) | null",
  "warehouse": {
    "id": "integer",
    "warehouse_name": "string",
    "warehouse_code": "string"
  },
  "account": {
    "id": "integer", 
    "account_name": "string",
    "account_code": "string"
  }
}
```

### **Job**
```json
{
  "id": "integer",
  "inventory_id": "integer",
  "job_name": "string",
  "status": "string (active|inactive|completed)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### **Assignment**
```json
{
  "id": "integer",
  "job_id": "integer", 
  "user_id": "integer",
  "status": "string (assigned|in_progress|completed|cancelled)",
  "assigned_at": "datetime (ISO 8601)",
  "completed_at": "datetime (ISO 8601) | null",
  "user": {
    "id": "integer",
    "username": "string",
    "first_name": "string",
    "last_name": "string", 
    "email": "string"
  }
}
```

### **Counting**
```json
{
  "id": "integer",
  "inventory_id": "integer",
  "count_mode": "string (manuel|automatique)",
  "status": "string (en_cours|termine|annule)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

---

## 🔄 **Comportement de l'API**

### **Logique de Synchronisation**

1. **Si `user_id` est fourni dans l'URL :**
   - Récupère les inventaires du même compte que cet utilisateur
   - Utilise `user_id` comme utilisateur cible

2. **Si `user_id` n'est pas fourni :**
   - Utilise l'utilisateur connecté (`request.user.id`)
   - Récupère les inventaires du même compte que l'utilisateur connecté

3. **Si `inventory_id` est fourni en paramètre :**
   - Synchronise uniquement cet inventaire spécifique
   - Ignore la logique de compte utilisateur

### **Gestion des Erreurs**

- **Erreurs de traitement individuelles :** Loggées mais n'interrompent pas la synchronisation
- **Erreurs critiques :** Interrompent la synchronisation et retournent une erreur 400/500
- **Données manquantes :** Arrays vides retournés pour les sections non disponibles

---

## 📝 **Exemples d'Utilisation**

### **Synchronisation pour l'utilisateur connecté**
```http
GET /mobile/api/sync/data/
Authorization: Bearer <token>
```

### **Synchronisation pour un utilisateur spécifique**
```http
GET /mobile/api/sync/data/user/123/
Authorization: Bearer <token>
```

### **Synchronisation d'un inventaire spécifique**
```http
GET /mobile/api/sync/data/?inventory_id=456
Authorization: Bearer <token>
```

### **Synchronisation complète avec utilisateur et inventaire**
```http
GET /mobile/api/sync/data/user/123/?inventory_id=456
Authorization: Bearer <token>
```

---

## 🏷️ **Tags Swagger**

- **Tag :** `Synchronisation Mobile`
- **Sécurité :** `Bearer Token`
- **Version :** `1.0.0`

---

## ⚡ **Optimisations**

- **Synchronisation en une seule requête** pour optimiser les performances mobile
- **Gestion des erreurs individuelles** sans interruption de la synchronisation globale
- **Logging détaillé** pour le debugging
- **Support des inventaires spécifiques** pour les cas d'usage ciblés
