# Validation d'Import de Stock selon le Type d'Inventaire

## Vue d'ensemble

Cette fonctionnalité ajoute une validation métier pour l'import de stocks selon le type d'inventaire (TOURNANT ou GENERAL).

## Règles Métier

### Inventaire de Type TOURNANT
- **Règle principale** : Un inventaire de type TOURNANT ne peut avoir qu'un seul import de stock
- **Vérification** : Si des stocks existent déjà pour cet inventaire, l'import est refusé
- **Message d'erreur** : "Cet inventaire de type TOURNANT a déjà X stocks importés. Pour importer de nouveaux stocks, vous devez supprimer cet inventaire et en créer un nouveau."
- **Action requise** : DELETE_AND_RECREATE

### Inventaire de Type GENERAL
- **Règle principale** : Aucune restriction sur l'import de stock
- **Comportement** : Les stocks existants sont remplacés par les nouveaux
- **Message** : "Import autorisé pour cet inventaire de type GENERAL. X stocks existants seront remplacés."

## API Disponible

### Import de Stock avec Validation
**Endpoint** : `POST /api/inventory/{inventory_id}/stocks/import/`

**Comportement** :
1. Vérification du type d'inventaire
2. Pour TOURNANT : validation qu'aucun stock n'existe déjà
3. Pour GENERAL : import autorisé (remplacement des stocks existants)
4. Import du fichier Excel si autorisé

**Réponse d'erreur (TOURNANT avec stocks existants)** :
```json
{
    "success": false,
    "message": "Cet inventaire de type TOURNANT a déjà 150 stocks importés. Pour importer de nouveaux stocks, vous devez supprimer cet inventaire et en créer un nouveau.",
    "inventory_type": "TOURNANT",
    "existing_stocks_count": 150,
    "action_required": "DELETE_AND_RECREATE"
}
```

**Réponse de succès** :
```json
{
    "success": true,
    "message": "Import terminé avec succès",
    "inventory_type": "GENERAL",
    "summary": {
        "total_rows": 100,
        "valid_rows": 98,
        "invalid_rows": 2
    },
    "imported_stocks": [
        {
            "id": 1,
            "product": "PROD001",
            "location": "LOC001",
            "quantity": 10
        }
    ]
}
```

## Architecture

### Use Case : StockImportValidationUseCase
- **Fichier** : `apps/inventory/usecases/stock_import_validation.py`
- **Responsabilité** : Validation métier selon le type d'inventaire
- **Méthodes principales** :
  - `validate_stock_import(inventory_id)` : Validation complète
  - `get_inventory_stock_info(inventory_id)` : Informations détaillées des stocks

### Vue : StockImportView (Modifiée)
- **Fichier** : `apps/inventory/views/inventory_views.py`
- **Modification** : Ajout de la validation via le use case avant l'import



## Utilisation

### Importer des stocks
```bash
POST /api/inventory/1/stocks/import/
Content-Type: multipart/form-data

file: [fichier Excel]
```

## Gestion des Erreurs

### Inventaire Non Trouvé
```json
{
    "success": false,
    "message": "L'inventaire avec l'ID 1 n'existe pas."
}
```

### Type d'Inventaire Non Supporté
```json
{
    "success": false,
    "message": "Type d'inventaire non supporté: AUTRE_TYPE"
}
```

## Logs

Toutes les opérations sont loggées avec les niveaux appropriés :
- `INFO` : Import réussi
- `WARNING` : Inventaire non trouvé, validation échouée
- `ERROR` : Erreurs inattendues

## Tests

### Scénarios de Test Recommandés

1. **Inventaire TOURNANT sans stocks** : Import autorisé
2. **Inventaire TOURNANT avec stocks** : Import refusé
3. **Inventaire GENERAL sans stocks** : Import autorisé
4. **Inventaire GENERAL avec stocks** : Import autorisé (remplacement)
5. **Inventaire inexistant** : Erreur 404
6. **Fichier invalide** : Erreur de validation du fichier 