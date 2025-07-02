# API d'Importation - Inventaires et Stocks

Ce document décrit les APIs d'importation disponibles pour les inventaires et les stocks.

## 1. Importation d'Inventaires

### Endpoint
```
POST /api/inventory/import/
```

### Description
Permet d'importer des inventaires en lot via API avec validation et création.

### Format de la requête

#### Structure JSON
```json
{
    "inventories": [
        {
            "label": "Inventaire trimestriel Q1 2023",
            "date": "2024-03-20",
            "account_id": 2,
            "warehouse": [
                {"id": 1, "date": "12/12/2025"},
                {"id": 2, "date": "12/12/2025"}
            ],
            "comptages": [
                {
                    "order": 1,
                    "count_mode": "en vrac",
                    "unit_scanned": true,
                    "entry_quantity": false,
                    "is_variant": false,
                    "stock_situation": false,
                    "quantity_show": true,
                    "show_product": true,
                    "dlc": false,
                    "n_serie": false,
                    "n_lot": false
                }
            ]
        }
    ],
    "options": {
        "validate_only": false,
        "stop_on_error": true,
        "return_details": true
    }
}
```

#### Options d'importation
- `validate_only` (bool, défaut: false): Si true, valide seulement sans créer
- `stop_on_error` (bool, défaut: true): Si true, arrête l'import au premier erreur
- `return_details` (bool, défaut: true): Si true, retourne les détails des résultats

### Réponse

#### Succès (201 Created)
```json
{
    "success": true,
    "summary": {
        "total": 2,
        "success_count": 2,
        "error_count": 0
    },
    "results": [
        {
            "index": 0,
            "status": "created",
            "message": "Inventaire créé avec succès",
            "inventory_id": 123
        }
    ]
}
```

#### Erreurs partielles (207 Multi-Status)
```json
{
    "success": false,
    "summary": {
        "total": 3,
        "success_count": 1,
        "error_count": 2
    },
    "results": [
        {
            "index": 0,
            "status": "created",
            "message": "Inventaire créé avec succès",
            "inventory_id": 123
        }
    ],
    "errors": [
        {
            "index": 1,
            "data": {...},
            "errors": {
                "label": ["Ce champ est requis."]
            }
        }
    ]
}
```

## 2. Importation de Stocks

### Endpoint
```
POST /api/inventory/{inventory_id}/stocks/import/
```

### Description
Permet d'importer des stocks depuis un fichier Excel pour un inventaire spécifique.

### Format de la requête

#### Headers
```
Content-Type: multipart/form-data
```

#### Body (Form Data)
- `file`: Fichier Excel (.xlsx ou .xls)

#### Structure du fichier Excel
Le fichier Excel doit contenir les colonnes suivantes :

| Colonne | Description | Obligatoire |
|---------|-------------|-------------|
| `article` | Référence du produit | Oui |
| `emplacement` | Référence de l'emplacement | Oui |
| `quantite` | Quantité disponible | Oui |

#### Exemple de contenu Excel
```
| article | emplacement | quantite |
|---------|-------------|----------|
| PROD001 | LOC-A1     | 10       |
| PROD002 | LOC-B2     | 25       |
| PROD003 | LOC-C3     | 0        |
```

### Réponse

#### Succès (201 Created)
```json
{
    "success": true,
    "message": "Import terminé avec succès",
    "summary": {
        "total_rows": 3,
        "valid_rows": 3,
        "invalid_rows": 0
    },
    "imported_stocks": [
        {
            "id": 1,
            "product": "Produit A",
            "location": "Emplacement A1",
            "quantity": 10
        }
    ]
}
```

#### Erreurs (400 Bad Request)
```json
{
    "success": false,
    "message": "Import échoué: 2 lignes invalides",
    "summary": {
        "total_rows": 3,
        "valid_rows": 1,
        "invalid_rows": 2
    },
    "errors": [
        {
            "row": 3,
            "errors": [
                "Le produit avec la référence 'PROD999' n'existe pas"
            ],
            "data": {
                "article": "PROD999",
                "emplacement": "LOC-X1",
                "quantite": 5
            }
        }
    ]
}
```

## 3. Codes de statut HTTP

| Code | Description |
|------|-------------|
| 200 | Succès (opération terminée) |
| 201 | Créé (ressource créée avec succès) |
| 207 | Multi-Status (résultats partiels) |
| 400 | Bad Request (données invalides) |
| 404 | Not Found (inventaire non trouvé) |
| 500 | Internal Server Error (erreur serveur) |

## 4. Gestion des erreurs

### Types d'erreurs courantes

#### Validation des données
- Champs obligatoires manquants
- Formats de données invalides
- Références de produits/emplacements inexistantes

#### Fichier Excel
- Format de fichier non supporté
- Colonnes manquantes
- Fichier vide ou corrompu

#### Contraintes métier
- Inventaire inexistant
- Doublons de stocks
- Quantités négatives

## 5. Exemples d'utilisation

### Import d'inventaires avec validation uniquement
```bash
curl -X POST http://localhost:8000/api/inventory/import/ \
  -H "Content-Type: application/json" \
  -d '{
    "inventories": [...],
    "options": {
      "validate_only": true,
      "stop_on_error": false,
      "return_details": true
    }
  }'
```

### Import de stocks
```bash
curl -X POST http://localhost:8000/api/inventory/123/stocks/import/ \
  -F "file=@stocks.xlsx"
```

## 6. Architecture

### Composants utilisés

#### Services
- `InventoryService`: Gestion des inventaires
- `StockService`: Gestion des stocks

#### Repositories
- `InventoryRepository`: Accès aux données d'inventaires
- `StockRepository`: Accès aux données de stocks

#### Interfaces
- `IStockService`: Contrat du service de stocks

#### Exceptions
- `InventoryValidationError`: Erreurs de validation d'inventaire
- `StockValidationError`: Erreurs de validation de stock
- `StockNotFoundError`: Stock non trouvé
- `StockImportError`: Erreurs d'import de stock

### Flux de traitement

1. **Validation du format** de la requête
2. **Validation des données** via les serializers
3. **Traitement en lot** avec gestion d'erreurs
4. **Création en base** avec transactions
5. **Retour des résultats** avec résumé

## 7. Bonnes pratiques

### Performance
- Utiliser `bulk_create` pour les imports en lot
- Valider avant création pour éviter les erreurs partielles
- Utiliser des transactions pour la cohérence

### Sécurité
- Valider les types de fichiers
- Limiter la taille des fichiers
- Sanitiser les données d'entrée

### Monitoring
- Logger les opérations d'import
- Tracer les erreurs avec contexte
- Mesurer les performances d'import 