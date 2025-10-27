# 📱 Documentation des APIs Mobile

## Vue d'ensemble

Documentation complète des APIs mobiles pour l'application WMS. Toutes les APIs sont accessibles via le préfixe `/mobile/api/` et utilisent l'authentification JWT Bearer.

**Base URL:** `http://localhost:8000/mobile/api/` (Développement)  
**Production URL:** `https://api.smatch.com/mobile/api/`

---

## 📚 Table des matières

1. [Authentification](#authentification)
2. [Synchronisation](#synchronisation)
3. [Données utilisateur](#données-utilisateur)
4. [Assignments](#assignments)
5. [Comptage](#comptage)
6. [Upload de données](#upload-de-données)

---

## 🔐 Authentification

### 1. Connexion JWT

**Endpoint:** `POST /mobile/api/auth/jwt-login/`  
**Authentification:** Non requise

#### Description
Authentifie un utilisateur et retourne un token JWT pour l'authentification des requêtes suivantes.

#### Requête

```json
{
  "username": "john.doe",
  "password": "password123"
}
```

#### Schéma JSON de la requête

```json
{
  "type": "object",
  "required": ["username", "password"],
  "properties": {
    "username": {
      "type": "string",
      "description": "Nom d'utilisateur",
      "example": "john.doe"
    },
    "password": {
      "type": "string",
      "description": "Mot de passe",
      "example": "password123"
    }
  }
}
```

#### Réponse Succès (200)

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

#### Schéma JSON de la réponse (200)

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": true
    },
    "access": {
      "type": "string",
      "description": "Token JWT d'accès",
      "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "refresh": {
      "type": "string",
      "description": "Token JWT de rafraîchissement",
      "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "user": {
      "type": "object",
      "properties": {
        "user_id": {
          "type": "integer",
          "example": 1
        },
        "nom": {
          "type": "string",
          "example": "Doe"
        },
        "prenom": {
          "type": "string",
          "example": "John"
        }
      }
    }
  }
}
```

#### Réponse Erreur (400/401)

```json
{
  "success": false,
  "error": "Identifiants invalides",
  "details": {}
}
```

#### Schéma JSON de la réponse (400)

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": false
    },
    "error": {
      "type": "string",
      "example": "Identifiants invalides"
    },
    "details": {
      "type": "object"
    }
  }
}
```

---

### 2. Rafraîchissement du token

**Endpoint:** `POST /mobile/api/auth/refresh/`  
**Authentification:** Non requise

#### Description
Rafraîchit le token d'accès en utilisant le refresh token.

#### Requête

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Schéma JSON de la requête

```json
{
  "type": "object",
  "required": ["refresh"],
  "properties": {
    "refresh": {
      "type": "string",
      "description": "Token de rafraîchissement",
      "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

#### Réponse Succès (200)

```json
{
  "success": true,
  "access": "nouveau_token_jwt",
  "refresh": "nouveau_refresh_token"
}
```

#### Schéma JSON de la réponse (200)

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": true
    },
    "access": {
      "type": "string",
      "description": "Nouveau token d'accès",
      "example": "nouveau_token_jwt"
    },
    "refresh": {
      "type": "string",
      "description": "Nouveau token de rafraîchissement",
      "example": "nouveau_refresh_token"
    }
  }
}
```

---

## 🔄 Synchronisation

### Synchronisation complète des données

**Endpoint:** `GET /mobile/api/sync/data/`  
**Authentification:** Bearer Token requis

#### Description
Récupère toutes les données nécessaires en une seule requête pour optimiser les performances. Inclut inventaires, comptages, jobs, assignments, produits, emplacements et stocks.

#### Headers requis

```
Authorization: Bearer {access_token}
```

#### Paramètres de requête (optionnels)

- `inventory_id` (int): ID d'inventaire spécifique à synchroniser

#### Exemple d'URL

```
GET /mobile/api/sync/data/
GET /mobile/api/sync/data/?inventory_id=5
```

#### Réponse Succès (200)

```json
{
  "success": true,
  "inventories": [
    {
      "id": 1,
      "reference": "INV-2024-001",
      "label": "Inventaire Janvier 2024",
      "status": "EN_REALISATION"
    }
  ],
  "countings": [
    {
      "id": 1,
      "inventory_id": 1,
      "status": "ENTAME"
    }
  ],
  "jobs": [
    {
      "id": 1,
      "reference": "JOB-001",
      "status": "VALIDE"
    }
  ],
  "assignments": [
    {
      "id": 1,
      "user_id": 1,
      "job_id": 1,
      "status": "EN_ATTENTE"
    }
  ],
  "products": [
    {
      "id": 1,
      "Internal_Product_Code": "PROD-001",
      "Short_Description": "Produit exemple"
    }
  ],
  "locations": [
    {
      "id": 1,
      "location_reference": "LOC-001",
      "description": "Emplacement A1"
    }
  ],
  "stocks": [
    {
      "id": 1,
      "product_id": 1,
      "location_id": 1,
      "quantity": 100
    }
  ]
}
```

#### Schéma JSON de la réponse (200)

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": true
    },
    "inventories": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Liste des inventaires actifs"
    },
    "countings": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Liste des comptages associés"
    },
    "jobs": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Liste des jobs"
    },
    "assignments": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Liste des assignments"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Liste des produits"
    },
    "locations": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Liste des emplacements"
    },
    "stocks": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Liste des stocks"
    }
  }
}
```

#### Réponse Erreur (400)

```json
{
  "success": false,
  "error": "Paramètre invalide",
  "error_type": "INVALID_PARAMETER"
}
```

---

## 👤 Données utilisateur

### 1. Produits de l'utilisateur

**Endpoint:** `GET /mobile/api/user/{user_id}/products/`  
**Authentification:** Bearer Token requis

#### Description
Récupère la liste des produits appartenant au même compte qu'un utilisateur.

#### Headers requis

```
Authorization: Bearer {access_token}
```

#### Paramètres d'URL

- `user_id` (int): ID de l'utilisateur

#### Réponse Succès (200)

```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": 1,
        "Internal_Product_Code": "PROD-001",
        "Short_Description": "Produit exemple",
        "Product_Family": {}
      }
    ]
  }
}
```

#### Schéma JSON de la réponse (200)

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": true
    },
    "data": {
      "type": "object",
      "properties": {
        "products": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": {
                "type": "integer",
                "example": 1
              },
              "Internal_Product_Code": {
                "type": "string",
                "example": "PROD-001"
              },
              "Short_Description": {
                "type": "string",
                "example": "Produit exemple"
              },
              "Product_Family": {
                "type": "object"
              }
            }
          }
        }
      }
    }
  }
}
```

---

### 2. Emplacements de l'utilisateur

**Endpoint:** `GET /mobile/api/user/{user_id}/locations/`  
**Authentification:** Bearer Token requis

#### Description
Récupère la liste des emplacements accessibles à un utilisateur.

#### Headers requis

```
Authorization: Bearer {access_token}
```

#### Paramètres d'URL

- `user_id` (int): ID de l'utilisateur

#### Réponse Succès (200)

```json
{
  "success": true,
  "data": {
    "locations": [
      {
        "id": 1,
        "location_reference": "LOC-001",
        "description": "Emplacement A1",
        "sous_zone": {
          "id": 1,
          "sous_zone_name": "Zone A"
        }
      }
    ]
  }
}
```

---

### 3. Stocks de l'utilisateur

**Endpoint:** `GET /mobile/api/user/{user_id}/stocks/`  
**Authentification:** Bearer Token requis

#### Description
Récupère les stocks accessibles à un utilisateur.

#### Headers requis

```
Authorization: Bearer {access_token}
```

#### Paramètres d'URL

- `user_id` (int): ID de l'utilisateur

#### Réponse Succès (200)

```json
{
  "success": true,
  "data": {
    "stocks": [
      {
        "id": 1,
        "product_id": 1,
        "location_id": 1,
        "quantity": 100,
        "product": {
          "id": 1,
          "Internal_Product_Code": "PROD-001"
        },
        "location": {
          "id": 1,
          "location_reference": "LOC-001"
        }
      }
    ]
  }
}
```

---

## 📋 Assignments

### Mise à jour du statut d'assignment

**Endpoint:** `POST /mobile/api/user/{user_id}/assignment/{assignment_id}/status/`  
**Authentification:** Bearer Token requis

#### Description
Met à jour le statut d'un assignment et de son job associé vers "ENTAME".

#### Headers requis

```
Authorization: Bearer {access_token}
Content-Type: application/json
```

#### Paramètres d'URL

- `user_id` (int): ID de l'utilisateur assigné
- `assignment_id` (int): ID de l'assignment à mettre à jour

#### Réponse Succès (200)

```json
{
  "success": true,
  "data": {
    "assignment_id": 1,
    "job_id": 5,
    "new_status": "ENTAME",
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

#### Schéma JSON de la réponse (200)

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": true
    },
    "data": {
      "type": "object",
      "properties": {
        "assignment_id": {
          "type": "integer",
          "example": 1
        },
        "job_id": {
          "type": "integer",
          "example": 5
        },
        "new_status": {
          "type": "string",
          "example": "ENTAME"
        },
        "updated_at": {
          "type": "string",
          "format": "date-time",
          "example": "2024-01-01T10:00:00Z"
        }
      }
    }
  }
}
```

---

## 🔢 Comptage

### Gestion des CountingDetail

**Endpoint:** `POST /mobile/api/counting-detail/`  
**Authentification:** Bearer Token requis

#### Description
Crée ou met à jour un CountingDetail (détail de comptage).

#### Headers requis

```
Authorization: Bearer {access_token}
Content-Type: application/json
```

#### Requête

```json
{
  "counting_id": 1,
  "product_id": 10,
  "location_id": 5,
  "quantity_counted": 25,
  "counting_mode": "IN_BULK",
  "notes": "Comptage terminé"
}
```

#### Schéma JSON de la requête

```json
{
  "type": "object",
  "required": ["counting_id", "product_id", "location_id", "quantity_counted"],
  "properties": {
    "counting_id": {
      "type": "integer",
      "description": "ID du comptage",
      "example": 1
    },
    "product_id": {
      "type": "integer",
      "description": "ID du produit",
      "example": 10
    },
    "location_id": {
      "type": "integer",
      "description": "ID de l'emplacement",
      "example": 5
    },
    "quantity_counted": {
      "type": "integer",
      "description": "Quantité comptée",
      "example": 25
    },
    "counting_mode": {
      "type": "string",
      "enum": ["IN_BULK", "BY_ARTICLE", "IMAGE_STOCK"],
      "description": "Mode de comptage",
      "example": "IN_BULK"
    },
    "notes": {
      "type": "string",
      "description": "Notes additionnelles",
      "example": "Comptage terminé"
    }
  }
}
```

#### Réponse Succès (201)

```json
{
  "success": true,
  "data": {
    "counting_detail_id": 100,
    "counting_id": 1,
    "product_id": 10,
    "location_id": 5,
    "quantity_counted": 25,
    "status": "COMPLETED",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

#### Schéma JSON de la réponse (201)

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": true
    },
    "data": {
      "type": "object",
      "properties": {
        "counting_detail_id": {
          "type": "integer",
          "example": 100
        },
        "counting_id": {
          "type": "integer",
          "example": 1
        },
        "product_id": {
          "type": "integer",
          "example": 10
        },
        "location_id": {
          "type": "integer",
          "example": 5
        },
        "quantity_counted": {
          "type": "integer",
          "example": 25
        },
        "status": {
          "type": "string",
          "example": "COMPLETED"
        },
        "created_at": {
          "type": "string",
          "format": "date-time",
          "example": "2024-01-01T10:00:00Z"
        }
      }
    }
  }
}
```

---

## ⬆️ Upload de données

### Upload complet

**Endpoint:** `POST /mobile/api/sync/upload/`  
**Authentification:** Bearer Token requis

#### Description
Upload tous les types de données en une seule requête (comptages, assignments, etc.)

#### Headers requis

```
Authorization: Bearer {access_token}
Content-Type: application/json
```

#### Requête

```json
{
  "sync_id": "sync_123456789",
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

#### Schéma JSON de la requête

```json
{
  "type": "object",
  "required": ["sync_id"],
  "properties": {
    "sync_id": {
      "type": "string",
      "description": "Identifiant de synchronisation",
      "example": "sync_123456789"
    },
    "countings": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Données de comptage à uploader"
    },
    "assignments": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Données d'assignment à uploader"
    }
  }
}
```

#### Réponse Succès (200)

```json
{
  "success": true,
  "message": "Upload réussi",
  "countings_processed": 5,
  "assignments_processed": 3,
  "errors": []
}
```

#### Schéma JSON de la réponse (200)

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": true
    },
    "message": {
      "type": "string",
      "example": "Upload réussi"
    },
    "countings_processed": {
      "type": "integer",
      "example": 5
    },
    "assignments_processed": {
      "type": "integer",
      "example": 3
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Liste des erreurs rencontrées"
    }
  }
}
```

---

## 📝 Codes de statut HTTP

| Code | Description |
|------|-------------|
| 200 | Succès |
| 201 | Créé avec succès |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès refusé |
| 404 | Ressource non trouvée |
| 500 | Erreur serveur |

---

## 🚨 Gestion d'erreurs

### Format standard d'erreur

```json
{
  "success": false,
  "error": "Message d'erreur",
  "error_type": "TYPE_ERREUR"
}
```

#### Schéma JSON d'erreur

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "example": false
    },
    "error": {
      "type": "string",
      "example": "Message d'erreur"
    },
    "error_type": {
      "type": "string",
      "example": "TYPE_ERREUR"
    }
  }
}
```

### Types d'erreurs courants

- `INVALID_PARAMETER` - Paramètre invalide
- `USER_NOT_FOUND` - Utilisateur non trouvé
- `NOT_AUTHENTICATED` - Non authentifié
- `VALIDATION_ERROR` - Erreur de validation
- `INTERNAL_ERROR` - Erreur interne

---

**Dernière mise à jour :** 2024-01-15