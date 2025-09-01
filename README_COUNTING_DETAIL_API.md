# API CountingDetail et NumeroSerie

## Vue d'ensemble

Cette API permet de créer des `CountingDetail` et leurs `NumeroSerie` associés, avec validation automatique selon le mode de comptage. Elle respecte l'architecture existante de l'application mobile en utilisant des use cases et des services.

## Endpoint principal

### Création de CountingDetail et NumeroSerie

**URL:** `POST /mobile/api/counting-detail/`

**Description:** Crée un CountingDetail et ses NumeroSerie associés selon le mode de comptage

**Headers requis:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

## Règles de validation selon le mode de comptage

### 1. Mode "en vrac"
- **Article:** Non obligatoire
- **Numéros de série:** Optionnels (si activés dans le comptage)
- **Autres champs:** Optionnels

### 2. Mode "par article"
- **Article:** **OBLIGATOIRE**
- **Validation des propriétés du produit:**
  - Si `product.dlc = True` → **DLC obligatoire** (null et chaînes vides non acceptés)
  - Si `product.n_lot = True` → **Numéro de lot obligatoire** (null et chaînes vides non acceptés)
  - Si `product.n_serie = True` → **Numéros de série obligatoires** (null et listes vides non acceptés)
- **Validation des numéros de série:**
  - **Vérification d'existence :** Les numéros de série doivent exister dans `masterdata.NSerie` pour l'article
  - **Vérification de duplication :** Les numéros de série ne doivent pas être déjà utilisés dans les CountingDetail existants
- **Numéros de série:** Optionnels (selon les propriétés du produit)
- **Autres champs:** Optionnels

### 3. Mode "image de stock"
- **Article:** Non obligatoire
- **Numéros de série:** Optionnels (si activés dans le comptage)
- **Autres champs:** Optionnels

## Structure du body

### Champs obligatoires
```json
{
    "counting_id": 1,                    // ID du comptage (obligatoire)
    "location_id": 1,                    // ID de l'emplacement (obligatoire)
    "quantity_inventoried": 10,          // Quantité inventoriée (obligatoire)
    "assignment_id": 1                   // ID de l'assignment (obligatoire)
}
```

### Champs optionnels
```json
{
    "product_id": 1,                     // ID du produit (selon le mode)
    "dlc": "2024-12-31",                // Date limite de consommation
    "n_lot": "LOT123",                  // Numéro de lot
    "numeros_serie": [                   // Numéros de série (si activés)
        {"n_serie": "NS001-2024"},
        {"n_serie": "NS002-2024"}
    ],
    "job_detail_id": 1                  // ID du JobDetail (pour mise à jour du statut)
}
```

## Exemples d'utilisation

### 1. Comptage en vrac (article non obligatoire)
```json
{
    "counting_id": 1,
    "location_id": 1,
    "quantity_inventoried": 10,
    "assignment_id": 1,
    "dlc": "2024-12-31",
    "n_lot": "LOT123"
}
```

### 2. Comptage par article (article obligatoire)
```json
{
    "counting_id": 2,
    "location_id": 1,
    "quantity_inventoried": 5,
    "assignment_id": 1,
    "product_id": 1,
    "dlc": "2024-12-31"
}
```

### 3. Comptage avec numéros de série
```json
{
    "counting_id": 3,
    "location_id": 1,
    "quantity_inventoried": 3,
    "assignment_id": 1,
    "product_id": 1,
    "numeros_serie": [
        {"n_serie": "NS001-2024"},
        {"n_serie": "NS002-2024"},
        {"n_serie": "NS003-2024"}
    ]
}
```

## Réponse de succès (201)

```json
{
    "success": true,
    "data": {
        "counting_detail": {
            "id": 1,
            "reference": "CD-1-20241215-ABC123",
            "quantity_inventoried": 10,
            "product_id": 1,
            "location_id": 1,
            "counting_id": 1,
            "created_at": "2024-12-15T10:30:00Z",
            "updated_at": "2024-12-15T10:30:00Z"
        },
        "numeros_serie": [
            {
                "id": 1,
                "reference": "NS-1-20241215-DEF456",
                "n_serie": "NS001-2024"
            }
        ],
        "message": "CountingDetail créé avec 1 numéro(s) de série"
    }
}
```

## Récupération des données (GET)

### Récupérer par comptage
```
GET /mobile/api/counting-detail/?counting_id=1
```

### Récupérer par emplacement
```
GET /mobile/api/counting-detail/?location_id=1
```

### Récupérer par produit
```
GET /mobile/api/counting-detail/?product_id=1
```

## Utilisation avec cURL

### Création d'un CountingDetail
```bash
curl -X POST \
  http://localhost:8000/mobile/api/counting-detail/ \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "counting_id": 1,
    "location_id": 1,
    "quantity_inventoried": 10,
    "assignment_id": 1,
    "product_id": 1
  }'
```

### Récupération des CountingDetail
```bash
curl -X GET \
  'http://localhost:8000/mobile/api/counting-detail/?counting_id=1' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

## Codes d'erreur

- **400:** Données invalides ou validation échouée
- **401:** Authentification requise
- **500:** Erreur interne du serveur

## Messages d'erreur courants

### Validation du mode de comptage
```json
{
    "success": false,
    "error": "Le produit est obligatoire pour le mode de comptage 'par article'",
    "error_type": "counting_mode_error"
}
```

### Validation des propriétés du produit
```json
{
    "success": false,
    "error": "Le produit nécessite une DLC (Date Limite de Consommation) - null n'est pas accepté",
    "error_type": "product_property_error"
}
```

```json
{
    "success": false,
    "error": "Le produit nécessite un numéro de lot - null n'est pas accepté",
    "error_type": "product_property_error"
}
```

```json
{
    "success": false,
    "error": "Le produit nécessite des numéros de série - null n'est pas accepté",
    "error_type": "product_property_error"
}
```

### Validation des numéros de série dupliqués
```json
{
    "success": false,
    "error": "Numéro de série NS001-2024 déjà utilisé pour ce produit",
    "error_type": "product_property_error"
}
```

### Validation des numéros de série inexistants dans masterdata
```json
{
    "success": false,
    "error": "Numéro de série NS999-INEXISTANT n'existe pas dans masterdata pour ce produit",
    "error_type": "product_property_error"
}
```

### Champs manquants
```json
{
    "success": false,
    "error": "Le champ 'counting_id' est obligatoire",
    "error_type": "validation_error"
}
```

### Comptage non trouvé
```json
{
    "success": false,
    "error": "Comptage avec l'ID 999 non trouvé",
    "error_type": "validation_error"
}
```

## Architecture technique

### Use Case
- **`CountingDetailCreationUseCase`** : Gère la logique métier et la validation

### Service
- **`CountingDetailService`** : Interface avec le use case et gestion des erreurs

### Vue
- **`CountingDetailView`** : Gestion des requêtes HTTP et réponses

### Modèles
- **`CountingDetail`** : Détail du comptage
- **`NSerie`** : Numéros de série associés
- **`Counting`** : Configuration du comptage
- **`JobDetail`** : Détail du job (mise à jour du statut)

## Test

Pour tester l'API, exécutez :
```bash
python test_counting_detail_api.py
```

**Note:** Remplacez les IDs par des valeurs valides dans votre base de données.

## Fonctionnalités

- ✅ Validation automatique selon le mode de comptage
- ✅ Création automatique des numéros de série
- ✅ Mise à jour automatique du statut des JobDetail
- ✅ Transaction atomique pour garantir la cohérence
- ✅ Gestion des erreurs détaillée
- ✅ Logging complet des opérations
- ✅ Respect de l'architecture existante
