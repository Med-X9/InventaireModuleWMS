# API CountingDetail - Support des Lots et Validation

## Vue d'ensemble

L'API CountingDetail a été étendue pour supporter :
- **Création en lot** : Traitement de plusieurs enregistrements en une seule requête
- **Validation en lot** : Validation de données sans création d'enregistrements
- **Détection et mise à jour automatique** : Vérification des enregistrements existants et mise à jour si nécessaire

## Endpoints

### POST `/mobile/api/counting-detail/`

#### Création d'un seul enregistrement

```json
{
    "counting_id": 1,
    "location_id": 1,
    "quantity_inventoried": 10,
    "assignment_id": 1,
    "product_id": 1,
    "dlc": "2024-12-31",
    "n_lot": "LOT123",
    "numeros_serie": [
        {"n_serie": "NS001"},
        {"n_serie": "NS002"}
    ]
}
```

#### Création en lot

```json
{
    "batch": true,
    "data": [
        {
            "counting_id": 1,
            "location_id": 1,
            "quantity_inventoried": 10,
            "assignment_id": 1,
            "product_id": 1,
            "dlc": "2024-12-31",
            "n_lot": "LOT123",
            "numeros_serie": [{"n_serie": "NS001"}]
        },
        {
            "counting_id": 1,
            "location_id": 2,
            "quantity_inventoried": 5,
            "assignment_id": 1,
            "product_id": 2
        }
    ]
}
```

### PUT `/mobile/api/counting-detail/`

#### Validation en lot

```json
{
    "data": [
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
}
```

## Réponses API

### Création en lot - Succès (201)

```json
{
    "success": true,
    "data": {
        "success": true,
        "total_processed": 2,
        "successful": 2,
        "failed": 0,
        "results": [
            {
                "index": 0,
                "data": {...},
                "result": {
                    "action": "created",
                    "counting_detail": {
                        "id": 123,
                        "reference": "CD-20241201-001",
                        "quantity_inventoried": 10,
                        "product_id": 1,
                        "location_id": 1,
                        "counting_id": 1,
                        "created_at": "2024-12-01T10:00:00Z",
                        "updated_at": "2024-12-01T10:00:00Z"
                    },
                    "numeros_serie": [
                        {
                            "id": 456,
                            "n_serie": "NS001",
                            "reference": "NS-20241201-001"
                        }
                    ]
                }
            }
        ],
        "errors": []
    }
}
```

### Validation en lot - Succès (200)

```json
{
    "success": true,
    "data": {
        "success": true,
        "total_processed": 2,
        "valid": 2,
        "invalid": 0,
        "results": [
            {
                "index": 0,
                "data": {...},
                "valid": true,
                "exists": false,
                "existing_id": null,
                "action_needed": "create"
            },
            {
                "index": 1,
                "data": {...},
                "valid": true,
                "exists": true,
                "existing_id": 123,
                "action_needed": "update"
            }
        ],
        "errors": []
    }
}
```

## Logique de détection des enregistrements existants

L'API utilise les critères suivants pour détecter un enregistrement existant :
- `counting_id` + `location_id` + `product_id` (si fourni)

Si un enregistrement existant est trouvé :
- **Création** : L'enregistrement est mis à jour au lieu d'être créé
- **Validation** : L'API indique que l'enregistrement existe et qu'une mise à jour sera nécessaire

## Gestion des numéros de série

Lors de la mise à jour d'un enregistrement existant :
1. Les anciens numéros de série sont supprimés
2. Les nouveaux numéros de série sont créés
3. La référence des numéros de série est régénérée

## Gestion des erreurs

### Erreur de validation

```json
{
    "success": false,
    "error": "Description de l'erreur",
    "error_type": "validation_error"
}
```

### Erreur en lot avec certains échecs

```json
{
    "success": true,
    "data": {
        "success": true,
        "total_processed": 3,
        "successful": 2,
        "failed": 1,
        "results": [...],
        "errors": [
            {
                "index": 2,
                "data": {...},
                "error": "Description de l'erreur"
            }
        ]
    }
}
```

## Types d'erreurs

- `validation_error` : Erreur de validation des données
- `product_property_error` : Erreur de validation des propriétés du produit
- `assignment_error` : Erreur de validation de l'assignment
- `job_detail_error` : Erreur de validation du JobDetail
- `numero_serie_error` : Erreur de validation des numéros de série
- `counting_mode_error` : Erreur de validation du mode de comptage

## Exemples d'utilisation

### 1. Validation avant création

```bash
# Étape 1: Valider les données
curl -X PUT "http://localhost:8000/mobile/api/counting-detail/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "counting_id": 1,
        "location_id": 1,
        "quantity_inventoried": 10,
        "assignment_id": 1,
        "product_id": 1
      }
    ]
  }'

# Étape 2: Créer si validation OK
curl -X POST "http://localhost:8000/mobile/api/counting-detail/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "batch": true,
    "data": [
      {
        "counting_id": 1,
        "location_id": 1,
        "quantity_inventoried": 10,
        "assignment_id": 1,
        "product_id": 1
      }
    ]
  }'
```

### 2. Création en lot avec mise à jour automatique

```bash
curl -X POST "http://localhost:8000/mobile/api/counting-detail/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "batch": true,
    "data": [
      {
        "counting_id": 1,
        "location_id": 1,
        "quantity_inventoried": 15,
        "assignment_id": 1,
        "product_id": 1,
        "dlc": "2024-12-31"
      },
      {
        "counting_id": 1,
        "location_id": 2,
        "quantity_inventoried": 8,
        "assignment_id": 1,
        "product_id": 2
      }
    ]
  }'
```

## Avantages

1. **Performance** : Traitement en lot réduit les appels réseau
2. **Cohérence** : Détection automatique des enregistrements existants
3. **Flexibilité** : Support des opérations individuelles et en lot
4. **Validation** : Possibilité de valider avant création
5. **Robustesse** : Gestion des erreurs partielles en lot

## Migration depuis l'ancienne API

L'ancienne API reste compatible. Pour utiliser les nouvelles fonctionnalités :
- Ajoutez `"batch": true` dans le body pour la création en lot
- Utilisez la méthode PUT pour la validation en lot
- Les enregistrements existants sont automatiquement détectés et mis à jour
