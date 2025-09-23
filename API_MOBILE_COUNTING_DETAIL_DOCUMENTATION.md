# API CountingDetail Mobile - Support des Lots et Validation

## Vue d'ensemble

L'API CountingDetail mobile a été créée dans `apps/mobile` avec les fonctionnalités suivantes :
- **Création en lot** : Traitement de plusieurs enregistrements en une seule requête
- **Validation en lot** : Validation de données sans création d'enregistrements
- **Détection et mise à jour automatique** : Vérification des enregistrements existants et mise à jour si nécessaire

## Structure des Fichiers

### Services
- **`apps/mobile/services/counting_detail_service.py`** : Service principal pour la gestion des CountingDetail

### Exceptions
- **`apps/mobile/exceptions/counting_detail_exceptions.py`** : Exceptions spécifiques aux CountingDetail

### Vues
- **`apps/mobile/views/counting/counting_detail_view.py`** : Vue API pour les CountingDetail

### Tests
- **`test_mobile_counting_detail_api.py`** : Script de test complet pour l'API mobile

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

## Service CountingDetailService

### Méthodes Principales

#### `create_counting_detail(data)`
Crée un seul CountingDetail et ses NumeroSerie associés.

#### `create_counting_details_batch(data_list)`
Crée plusieurs CountingDetail en lot avec détection automatique des enregistrements existants.

#### `validate_counting_details_batch(data_list)`
Valide plusieurs CountingDetail sans les créer.

#### `_find_existing_counting_detail(data)`
Recherche un CountingDetail existant basé sur les critères de matching.

#### `_update_counting_detail(counting_detail, data)`
Met à jour un CountingDetail existant.

### Logique de Détection des Enregistrements Existants

L'API utilise les critères suivants pour détecter un enregistrement existant :
- `counting_id` + `location_id` + `product_id` (si fourni)

Si un enregistrement existant est trouvé :
- **Création** : L'enregistrement est mis à jour au lieu d'être créé
- **Validation** : L'API indique que l'enregistrement existe et qu'une mise à jour sera nécessaire

## Gestion des Numéros de Série

Lors de la mise à jour d'un enregistrement existant :
1. Les anciens numéros de série sont supprimés
2. Les nouveaux numéros de série sont créés
3. La référence des numéros de série est régénérée

## Exceptions

### Types d'Exceptions Disponibles

- `CountingDetailValidationError` : Erreur de validation des données
- `ProductPropertyValidationError` : Erreur de validation des propriétés du produit
- `CountingAssignmentValidationError` : Erreur de validation de l'assignment
- `JobDetailValidationError` : Erreur de validation du JobDetail
- `NumeroSerieValidationError` : Erreur de validation des numéros de série
- `CountingModeValidationError` : Erreur de validation du mode de comptage
- `CountingDetailBatchError` : Erreur dans le traitement en lot
- `CountingDetailNotFoundError` : CountingDetail non trouvé
- `CountingDetailUpdateError` : Erreur de mise à jour

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

## Exemples d'Utilisation

### 1. Validation avant Création

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

### 2. Création en Lot avec Mise à Jour Automatique

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

## Tests

### Exécution des Tests

```bash
python test_mobile_counting_detail_api.py
```

### Résultats des Tests

Les tests incluent :
1. **Import du service mobile** : Vérification de l'importation des modules
2. **Validation en lot** : Test de validation de plusieurs enregistrements
3. **Création d'un seul enregistrement** : Test de création individuelle
4. **Création en lot** : Test de création en lot avec gestion d'erreurs

## Avantages de la Structure Mobile

1. **Séparation des responsabilités** : Code mobile séparé du code inventory
2. **Maintenabilité** : Structure claire et organisée
3. **Réutilisabilité** : Services et exceptions réutilisables
4. **Testabilité** : Tests spécifiques à l'app mobile
5. **Performance** : Traitement en lot optimisé
6. **Robustesse** : Gestion d'erreurs complète

## Migration depuis l'API Inventory

L'API mobile est indépendante de l'API inventory et peut être utilisée directement. Pour migrer :

1. Utilisez les endpoints `/mobile/api/counting-detail/`
2. Importez les services depuis `apps.mobile.services`
3. Utilisez les exceptions depuis `apps.mobile.exceptions`
4. Adaptez vos tests avec `test_mobile_counting_detail_api.py`

## Statut

✅ **API Mobile CountingDetail prête pour la production !**

Toutes les fonctionnalités demandées ont été implémentées avec succès dans la structure mobile.
