# Formats JSON - APIs Mobile Inventaire

## Table des matières
1. [Authentification](#authentification)
2. [Synchronisation - Téléchargement](#synchronisation---téléchargement)
3. [Synchronisation - Upload](#synchronisation---upload)
4. [Gestion des conflits](#gestion-des-conflits)
5. [Statut de synchronisation](#statut-de-synchronisation)
6. [Logs et monitoring](#logs-et-monitoring)
7. [Gestion des erreurs](#gestion-des-erreurs)

---

## Authentification

### Login
**Endpoint:** `POST /api/mobile/auth/login/`

**Request:**
```json
{
  "username": "string",
  "password": "string",
}
```

**Response:**
```json
{
  "success": true,
  "access": "string",
  "refresh": "string",
  "user":{
    "user_id":5,
    "nom":"string",
    "prenom":"string"
  }
}
```

### Logout
**Endpoint:** `POST /api/mobile/auth/logout/`



### Refresh Token
**Endpoint:** `POST /api/mobile/auth/refresh/`

**Request:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "success": true,
  "token": "string",
}
```

---

## Synchronisation - Téléchargement

### Inventaires disponibles
**Endpoint:** `GET /api/mobile/sync/inventories/`

**Response:**
```json
{
  "success": true,
  "data": 
    {
      "web_id": 123,
      "reference": "INV-123-4567-ABCD",
      "label": "Inventaire Janvier 2024",
      "date": "2024-01-15T10:00:00Z",
      "status": "EN REALISATION",
      "inventory_type": "GENERAL",
      "warehouse_web_id": 456,
      "warehouse_name": "Entrepôt Principal",
      "en_preparation_status_date": "2024-01-10T08:00:00Z",
      "en_realisation_status_date": "2024-01-15T10:00:00Z",
      "termine_status_date": null,
      "cloture_status_date": null,
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }

}
```

### Jobs par inventaire
**Endpoint:** `GET /api/mobile/sync/jobs/{inventory_web_id}/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "web_id": 789,
      "reference": "JOB-789-1234-EFGH",
      "status": "AFFECTE",
      "inventory_web_id": 123,
      "warehouse_web_id": 456,
      "en_attente_date": "2024-01-15T10:00:00Z",
      "affecte_date": "2024-01-15T11:00:00Z",
      "pret_date": null,
      "transfert_date": null,
      "entame_date": null,
      "valide_date": null,
      "termine_date": null,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

### Assignations par job
**Endpoint:** `GET /api/mobile/sync/assignments/{job_web_id}/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "web_id": 101,
      "reference": "ASS-101-5678-IJKL",
      "status": "AFFECTE",
      "job_web_id": 789,
      "personne_web_id": 202,
      "personne_two_web_id": null,
      "counting_web_id": 303,
      "transfert_date": null,
      "entame_date": null,
      "affecte_date": "2024-01-15T11:00:00Z",
      "pret_date": null,
      "date_start": null,
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

### Détails des jobs
**Endpoint:** `GET /api/mobile/sync/job-details/{job_web_id}/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "web_id": 404,
      "reference": "JBD-404-9012-MNOP",
      "location_web_id": 505,
      "job_web_id": 789,
      "status": "EN ATTENTE",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Comptages par inventaire
**Endpoint:** `GET /api/mobile/sync/countings/{inventory_web_id}/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "web_id": 303,
      "reference": "CNT-303-3456-QRST",
      "order": 1,
      "count_mode": "PRODUIT_PAR_PRODUIT",
      "unit_scanned": true,
      "entry_quantity": true,
      "is_variant": false,
      "n_lot": true,
      "n_serie": false,
      "dlc": true,
      "show_product": true,
      "stock_situation": true,
      "quantity_show": true,
      "inventory_web_id": 123,
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-10T08:00:00Z"
    }
  ]
}
```

### Produits
**Endpoint:** `GET /api/mobile/sync/products/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "web_id": 606,
      "reference": "PROD-606-7890-UVWX",
      "internal_product_code": "INT-001",
      "short_description": "Produit Test",
      "barcode": "1234567890123",
      "product_group": "GROUP1",
      "stock_unit": "PIECE",
      "product_status": "ACTIVE",
      "product_family_web_id": 707,
      "is_variant": false,
      "n_lot": true,
      "n_serie": false,
      "dlc": true,
      "parent_product_web_id": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Emplacements
**Endpoint:** `GET /api/mobile/sync/locations/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "web_id": 505,
      "reference": "LOC-505-2345-YZAB",
      "location_reference": "A01-B02-C03",
      "sous_zone_web_id": 808,
      "location_type_web_id": 909,
      "capacity": 100,
      "is_active": true,
      "description": "Emplacement Aisle 1",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Stocks
**Endpoint:** `GET /api/mobile/sync/stocks/{inventory_web_id}/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "web_id": 1010,
      "reference": "STK-1010-4567-CDEF",
      "location_web_id": 505,
      "product_web_id": 606,
      "quantity_available": 50,
      "quantity_reserved": 5,
      "quantity_in_transit": 0,
      "quantity_in_receiving": 0,
      "unit_of_measure_web_id": 1111,
      "inventory_web_id": 123,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```


---

## Synchronisation - Upload

### Upload des comptages
**Endpoint:** `POST /api/mobile/sync/upload-countings/`

**Request:**
```json
{
  "sync_id": "sync-123456789",
  "countings": [
    {
      "detail_id": "detail-123456789",
      "quantite_comptee": 45,
      "product_web_id": 606,
      "location_web_id": 505,
      "numero_lot": "LOT-2024-001",
      "numero_serie": null,
      "dlc": "2024-12-31",
      "compte_par_web_id": 202,
      "date_comptage": "2024-01-15T14:30:00Z",
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "sync_id": "sync-123456789",
  "uploaded_count": 1,
  "errors": [],
  "conflicts": [],
}
```

### Upload des numéros de série
**Endpoint:** `POST /api/mobile/sync/upload-serial-numbers/`

**Request:**
```json
{
  "sync_id": "sync-987654321",
  "serial_numbers": [
    {
      "numero_serie": "SN-2024-001",
      "counting_detail_web_id": 1212,
      "timestamp_sync": "2024-01-15T14:30:00Z"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "sync_id": "sync-987654321",
  "uploaded_count": 1,
  "errors": [],
  "web_ids_mapping": {
    "SN-2024-001": 1313
  }
}
```

### Upload des statuts d'assignation
**Endpoint:** `POST /api/mobile/sync/upload-launching-status/{assignement_id}`

**Request:**
```json
{
  "sync_id": "sync-555666777",
  "assignments": [
    {
      "assignment_web_id": 101,
      "status": "ENTAME",
      "entame_date": "2024-01-15T14:30:00Z",
      "date_start": "2024-01-15T14:30:00Z"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "sync_id": "sync-555666777",
  "updated_count": 1,
  "errors": []
}
```

---

## Gestion des conflits

### Récupération des conflits
**Endpoint:** `GET /api/mobile/sync/conflicts/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "conflit_id": "conflict-123456789",
      "type_entite": "Comptage",
      "web_id_entite": 1212,
      "donnees_locales": {
        "quantite_comptee": 45,
        "date_comptage": "2024-01-15T14:30:00Z",
        "numero_lot": "LOT-2024-001"
      },
      "donnees_serveur": {
        "quantite_comptee": 50,
        "date_comptage": "2024-01-15T15:00:00Z",
        "numero_lot": "LOT-2024-002"
      },
      "status_resolution": "Non résolu",
      "date_detection": "2024-01-15T16:00:00Z",
      "date_resolution": null,
      "commentaire_resolution": null
    }
  ]
}
```

### Résolution de conflit
**Endpoint:** `POST /api/mobile/sync/resolve-conflict/`

**Request:**
```json
{
  "conflit_id": "conflict-123456789",
  "resolution": "local", // ou "serveur" ou "fusion"
  "commentaire": "Utilisation de la valeur locale"
}
```

**Response:**
```json
{
  "success": true,
  "conflit_id": "conflict-123456789",
  "status_resolution": "Résolu local",
  "date_resolution": "2024-01-15T16:30:00Z"
}
```

### Fusion de données
**Endpoint:** `POST /api/mobile/sync/merge-data/`

**Request:**
```json
{
  "conflit_id": "conflict-123456789",
  "merged_data": {
    "quantite_comptee": 47,
    "date_comptage": "2024-01-15T14:45:00Z",
    "numero_lot": "LOT-2024-001",
    "commentaire": "Moyenne des deux valeurs"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conflit_id": "conflict-123456789",
  "status_resolution": "Fusion",
  "date_resolution": "2024-01-15T16:30:00Z",
  "merged_web_id": 1212
}
```

---

## Statut de synchronisation

### Statut de la connexion
**Endpoint:** `GET /api/mobile/sync/connection-status/`

**Response:**
```json
{
  "success": true,
  "data": {
    "type_connexion": "WiFi",
    "force_signal": -45,
    "adresse_ip": "192.168.1.100",
    "serveur_connecte": "https://api.example.com",
    "derniere_verification": "2024-01-15T16:00:00Z",
    "status_connexion": "Connecté",
    "message_erreur": null
  }
}
```

### Configuration de synchronisation
**Endpoint:** `GET /api/mobile/sync/config/`

**Response:**
```json
{
  "success": true,
  "data": {
    "intervalle_sync": 300,
    "max_jours_hors_ligne": 7,
    "taille_max_donnees": 10485760,
    "tentatives_max": 3,
    "delai_entre_tentatives": 60,
    "timeout_connexion": 30,
    "compression_active": true,
    "chiffrement_active": true
  }
}
```

### Mise à jour de la configuration
**Endpoint:** `POST /api/mobile/sync/config/`

**Request:**
```json
{
  "intervalle_sync": 600,
  "max_jours_hors_ligne": 14,
  "compression_active": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration mise à jour"
}
```

### Statut de synchronisation global
**Endpoint:** `GET /api/mobile/sync/status/`

**Response:**
```json
{
  "success": true,
  "data": {
    "derniere_sync": "2024-01-15T16:00:00Z",
    "prochaine_sync": "2024-01-15T16:05:00Z",
    "nb_comptages_en_attente": 5,
    "nb_conflits_non_resolus": 2,
    "taille_donnees_locales": 1048576,
    "espace_disponible": 1073741824,
    "status_sync": "En attente"
  }
}
```

---

## Logs et monitoring

### Logs de synchronisation
**Endpoint:** `GET /api/mobile/sync/logs/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "log_id": "log-123456789",
      "niveau": "Info",
      "message": "Synchronisation terminée avec succès",
      "type_operation": "Upload",
      "web_id_entite": 1212,
      "donnees_contexte": {
        "sync_id": "sync-123456789",
        "nb_records": 1,
        "taille_donnees": 1024
      },
      "timestamp": "2024-01-15T16:00:00Z",
      "user_web_id": 202
    }
  ]
}
```

### Statistiques de synchronisation
**Endpoint:** `GET /api/mobile/sync/stats/`

**Response:**
```json
{
  "success": true,
  "data": {
    "periode": "2024-01-01 à 2024-01-15",
    "nb_syncs_reussies": 150,
    "nb_syncs_echouees": 3,
    "nb_comptages_uploades": 1250,
    "nb_conflits_resolus": 25,
    "temps_moyen_sync": 2.5,
    "taille_moyenne_donnees": 5120,
    "taux_reussite": 98.0
  }
}
```

### Nettoyage des logs
**Endpoint:** `POST /api/mobile/sync/clean-logs/`

**Request:**
```json
{
  "jours_a_conserver": 30
}
```

**Response:**
```json
{
  "success": true,
  "nb_logs_supprimes": 150,
  "espace_libere": 1048576
}
```

---

## Gestion des erreurs

### Format d'erreur standard
```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Identifiants invalides",
    "details": {
      "field": "username",
      "reason": "Utilisateur non trouvé"
    },
    "timestamp": "2024-01-15T16:00:00Z"
  }
}
```

### Codes d'erreur courants

| Code | Description |
|------|-------------|
| `AUTHENTICATION_FAILED` | Échec d'authentification |
| `TOKEN_EXPIRED` | Token expiré |
| `INVALID_REQUEST` | Requête invalide |
| `SYNC_CONFLICT` | Conflit de synchronisation |
| `NETWORK_ERROR` | Erreur réseau |
| `SERVER_ERROR` | Erreur serveur |
| `DATA_VALIDATION_ERROR` | Erreur de validation des données |
| `QUOTA_EXCEEDED` | Quota dépassé |
| `MAINTENANCE_MODE` | Mode maintenance |

### Exemple d'erreur de validation
```json
{
  "success": false,
  "error": {
    "code": "DATA_VALIDATION_ERROR",
    "message": "Données invalides",
    "details": {
      "field": "quantite_comptee",
      "reason": "La quantité doit être un nombre positif",
      "value": -5
    },
    "timestamp": "2024-01-15T16:00:00Z"
  }
}
```

### Exemple d'erreur de conflit
```json
{
  "success": false,
  "error": {
    "code": "SYNC_CONFLICT",
    "message": "Conflit de synchronisation détecté",
    "details": {
      "conflit_id": "conflict-123456789",
      "type_entite": "Comptage",
      "web_id_entite": 1212
    },
    "timestamp": "2024-01-15T16:00:00Z"
  }
}
```

---

## Headers d'authentification

Toutes les requêtes API (sauf authentification) doivent inclure le header d'autorisation :

```
Authorization: Bearer <token>
```

## Headers de synchronisation

Pour les requêtes de synchronisation, inclure également :

```
X-Sync-ID: <sync_id>
X-Device-ID: <device_id>
X-App-Version: <version_app>
```

## Pagination

Pour les endpoints retournant des listes, utiliser la pagination :

```
GET /api/mobile/sync/products/?page=1&page_size=50
```

**Response avec pagination :**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 1250,
    "total_pages": 25,
    "has_next": true,
    "has_previous": false
  }
}
``` 