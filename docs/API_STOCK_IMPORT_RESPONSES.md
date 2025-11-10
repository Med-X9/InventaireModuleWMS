# Documentation des Réponses - API Import de Stocks

## 📍 Endpoint

```
POST /api/inventory/inventory/<inventory_id>/stocks/import/
```

**Content-Type**: `multipart/form-data`  
**Body**: Fichier Excel (`file`) avec colonnes requises : `article`, `emplacement`, `quantite`

---

## ✅ Réponses de Succès

### 1. Import Réussi (201 Created)

```json
{
  "success": true,
  "message": "Import terminé avec succès",
  "inventory_type": "GENERAL",
  "summary": {
    "total_rows": 150,
    "valid_rows": 150,
    "invalid_rows": 0
  },
  "imported_stocks": [
    {
      "id": 123,
      "product": "ARTL-001507",
      "location": "A-01-01",
      "quantity": 25.5
    },
    {
      "id": 124,
      "product": "ARTL-001508",
      "location": "A-01-02",
      "quantity": 10.0
    }
  ]
}
```

**Statut HTTP**: `201 Created`

**Description**: L'import s'est terminé avec succès. Tous les stocks ont été importés correctement.

---

## ❌ Réponses d'Erreur (400 Bad Request)

### 2. Aucun fichier fourni

```json
{
  "success": false,
  "message": "Aucun fichier fourni. Utilisez le champ \"file\" pour uploader le fichier Excel."
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le champ `file` est manquant dans la requête multipart/form-data.

---

### 3. Format de fichier invalide

```json
{
  "success": false,
  "message": "Le fichier doit être au format Excel (.xlsx ou .xls)"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le fichier fourni n'est pas au format Excel (.xlsx ou .xls).

---

### 4. Validation - Inventaire TOURNANT avec stocks existants

```json
{
  "success": false,
  "message": "Cet inventaire de type TOURNANT a déjà 50 stocks importés. Pour importer de nouveaux stocks, vous devez supprimer cet inventaire et en créer un nouveau.",
  "inventory_type": "TOURNANT",
  "existing_stocks_count": 50,
  "action_required": "DELETE_AND_RECREATE"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Pour un inventaire de type TOURNANT, un seul import est autorisé. Si des stocks existent déjà, l'import est refusé.

**Action requise**: Supprimer l'inventaire et en créer un nouveau.

---

### 5. Validation - Aucun compte lié à l'inventaire

```json
{
  "success": false,
  "message": "Aucun compte lié à cet inventaire.",
  "inventory_type": "GENERAL",
  "existing_stocks_count": 0,
  "action_required": "FIX_LOCATIONS"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: L'inventaire n'a aucun compte associé via les liens AWI.

**Action requise**: Lier un compte à l'inventaire.

---

### 6. Validation - Aucun regroupement d'emplacement

```json
{
  "success": false,
  "message": "Aucun regroupement d'emplacement trouvé pour le compte ACC-001.",
  "inventory_type": "GENERAL",
  "existing_stocks_count": 0,
  "action_required": "FIX_LOCATIONS"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le compte lié à l'inventaire n'a pas de regroupement d'emplacement configuré.

**Action requise**: Créer un regroupement d'emplacement pour le compte.

---

### 7. Validation - Aucun emplacement actif

```json
{
  "success": false,
  "message": "Aucun emplacement actif trouvé dans le regroupement du compte ACC-001.",
  "inventory_type": "GENERAL",
  "existing_stocks_count": 0,
  "action_required": "FIX_LOCATIONS"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le regroupement d'emplacement du compte n'a aucun emplacement actif.

**Action requise**: Ajouter des emplacements actifs au regroupement.

---

### 8. Erreurs de validation du fichier Excel

```json
{
  "success": false,
  "message": "Import échoué: 3 lignes invalides",
  "inventory_type": "GENERAL",
  "summary": {
    "total_rows": 150,
    "valid_rows": 147,
    "invalid_rows": 3
  },
  "errors": [
    {
      "row": 5,
      "errors": [
        "La référence du produit est obligatoire",
        "La quantité doit être un nombre positif"
      ],
      "data": {
        "article": null,
        "emplacement": "A-01-01",
        "quantite": -5
      }
    },
    {
      "row": 12,
      "errors": [
        "Le produit avec la référence 'INEXISTANT-123' n'existe pas"
      ],
      "data": {
        "article": "INEXISTANT-123",
        "emplacement": "A-01-02",
        "quantite": 10
      }
    },
    {
      "row": 25,
      "errors": [
        "L'emplacement avec la référence 'LOC-999' n'existe pas"
      ],
      "data": {
        "article": "ARTL-001507",
        "emplacement": "LOC-999",
        "quantite": 15
      }
    }
  ]
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le fichier Excel contient des erreurs de validation sur certaines lignes.

**Erreurs possibles**:
- Référence de produit manquante ou invalide
- Référence d'emplacement manquante ou invalide
- Quantité manquante, négative ou invalide
- Produit ou emplacement n'existe pas en base de données

**Note**: L'import échoue si au moins une ligne est invalide (pas d'import partiel).

---

### 9. Structure du fichier Excel invalide

```json
{
  "success": false,
  "message": "Colonnes manquantes dans le fichier Excel: quantite. Colonnes requises: article, emplacement, quantite"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le fichier Excel ne contient pas toutes les colonnes requises.

**Colonnes requises**:
- `article` : Référence du produit
- `emplacement` : Référence de l'emplacement
- `quantite` : Quantité disponible

---

### 10. Fichier Excel vide

```json
{
  "success": false,
  "message": "Le fichier Excel est vide"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le fichier Excel ne contient aucune ligne de données (seulement l'en-tête éventuellement).

---

### 11. Emplacements non appartenant au regroupement

```json
{
  "success": false,
  "message": "Les emplacements suivants ne font pas partie du regroupement 'Regroupement Principal' du compte 'ACC-001': LOC-999, LOC-888"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Certains emplacements dans le fichier Excel n'appartiennent pas au regroupement d'emplacement du compte lié à l'inventaire.

**Action requise**: Utiliser uniquement les emplacements du regroupement du compte.

---

### 12. Doublons détectés dans le fichier

```json
{
  "success": false,
  "message": "Import échoué: doublons détectés dans le fichier à la ligne(s) 5, 12",
  "inventory_type": "GENERAL",
  "summary": {
    "total_rows": 150,
    "valid_rows": 0,
    "invalid_rows": 0
  },
  "errors": []
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le fichier contient des doublons (même produit au même emplacement sur plusieurs lignes).

**Action requise**: Supprimer les doublons du fichier avant l'import.

---

### 13. Doublons existants pour inventaire TOURNANT

```json
{
  "success": false,
  "message": "Import échoué: un stock existe déjà pour le produit ARTL-001507 à l'emplacement A-01-01 pour cet inventaire de type TOURNANT.",
  "inventory_type": "TOURNANT",
  "summary": {
    "total_rows": 150,
    "valid_rows": 0,
    "invalid_rows": 0
  },
  "errors": []
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Pour un inventaire TOURNANT, un stock existe déjà pour la même combinaison produit/emplacement.

**Action requise**: Vérifier les stocks existants avant l'import.

---

### 14. Erreur de lecture du fichier Excel

```json
{
  "success": false,
  "message": "Impossible de lire le fichier Excel: File is corrupted"
}
```

**Statut HTTP**: `400 Bad Request`

**Cause**: Le fichier Excel est corrompu ou ne peut pas être lu.

---

## 🔍 Réponses d'Erreur (404 Not Found)

### 15. Inventaire non trouvé

```json
{
  "success": false,
  "message": "L'inventaire avec l'ID 999 n'existe pas"
}
```

**Statut HTTP**: `404 Not Found`

**Cause**: L'ID de l'inventaire fourni dans l'URL n'existe pas en base de données.

---

## ⚠️ Réponses d'Erreur (500 Internal Server Error)

### 16. Erreur serveur inattendue

```json
{
  "success": false,
  "message": "Une erreur inattendue s'est produite lors de l'import"
}
```

**Statut HTTP**: `500 Internal Server Error`

**Cause**: Une erreur technique s'est produite côté serveur (base de données, système de fichiers, etc.).

---

## 📊 Structure des Champs de Réponse

### Champs communs

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `success` | `boolean` | Indique si l'opération a réussi | ✅ Oui |
| `message` | `string` | Message descriptif du résultat | ✅ Oui |

### Champs pour validation d'inventaire

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `inventory_type` | `string` | Type d'inventaire (`GENERAL` ou `TOURNANT`) | ⚠️ Si erreur de validation |
| `existing_stocks_count` | `integer` | Nombre de stocks existants | ⚠️ Si erreur de validation |
| `action_required` | `string\|null` | Action requise (`DELETE_AND_RECREATE`, `FIX_LOCATIONS`, ou `null`) | ⚠️ Si erreur de validation |

### Champs pour import réussi

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `inventory_type` | `string` | Type d'inventaire (`GENERAL` ou `TOURNANT`) | ✅ Oui |
| `summary` | `object` | Résumé de l'import | ✅ Oui |
| `summary.total_rows` | `integer` | Nombre total de lignes dans le fichier | ✅ Oui |
| `summary.valid_rows` | `integer` | Nombre de lignes valides | ✅ Oui |
| `summary.invalid_rows` | `integer` | Nombre de lignes invalides | ✅ Oui |
| `imported_stocks` | `array` | Liste des stocks importés | ⚠️ Si succès |

### Champs pour stocks importés

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `imported_stocks[].id` | `integer` | ID du stock créé en base | ✅ Oui |
| `imported_stocks[].product` | `string` | Référence du produit (`Internal_Product_Code`) | ✅ Oui |
| `imported_stocks[].location` | `string` | Référence de l'emplacement (`location_reference`) | ✅ Oui |
| `imported_stocks[].quantity` | `float` | Quantité disponible | ✅ Oui |

### Champs pour erreurs de validation

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `errors` | `array` | Liste des erreurs de validation | ⚠️ Si erreurs |
| `errors[].row` | `integer` | Numéro de ligne dans Excel (commence à 2, ligne 1 = header) | ✅ Oui |
| `errors[].errors` | `array` | Liste des messages d'erreur pour cette ligne | ✅ Oui |
| `errors[].data` | `object` | Données de la ligne en erreur | ✅ Oui |

---

## 📋 Messages d'Erreur de Validation Possibles

### Erreurs de produit

- `"La référence du produit est obligatoire"`
- `"Le produit avec la référence 'XXX' n'existe pas"`

### Erreurs d'emplacement

- `"La référence de l'emplacement est obligatoire"`
- `"L'emplacement avec la référence 'XXX' n'existe pas"`

### Erreurs de quantité

- `"La quantité est obligatoire"`
- `"La quantité doit être un nombre positif"`

### Erreurs d'inventaire

- `"L'ID de l'inventaire est obligatoire"`

---

## 🔄 Actions Requises (`action_required`)

### `DELETE_AND_RECREATE`

L'inventaire de type TOURNANT a déjà des stocks importés. Pour importer de nouveaux stocks, vous devez :
1. Supprimer l'inventaire existant
2. Créer un nouvel inventaire
3. Importer les stocks dans le nouvel inventaire

### `FIX_LOCATIONS`

Problème de configuration des emplacements. Actions possibles :
1. Vérifier qu'un compte est lié à l'inventaire
2. Créer un regroupement d'emplacement pour le compte
3. Ajouter des emplacements actifs au regroupement
4. Utiliser uniquement les emplacements du regroupement dans le fichier Excel

### `null`

Aucune action particulière requise (cas de succès ou erreurs autres).

---

## 📝 Exemple de Fichier Excel Valide

| article | emplacement | quantite |
|---------|-------------|----------|
| ARTL-001507 | A-01-01 | 25.5 |
| ARTL-001508 | A-01-02 | 10.0 |
| ARTL-001509 | A-01-03 | 15.0 |

**Note**: Les noms des colonnes doivent être exactement : `article`, `emplacement`, `quantite` (sans accents ni majuscules)

---

## 🎯 Règles Métier Importantes

1. **Inventaire TOURNANT**: 
   - Un seul import autorisé
   - Si des stocks existent déjà, l'import est refusé
   - Pas de doublons autorisés (même dans le fichier)

2. **Inventaire GENERAL**: 
   - Import autorisé à tout moment
   - Les stocks existants sont remplacés par les nouveaux
   - Pas de doublons autorisés dans le fichier

3. **Validation des emplacements**: 
   - Tous les emplacements doivent appartenir au regroupement du compte lié à l'inventaire
   - Seuls les emplacements actifs sont acceptés

4. **Validation stricte**: 
   - Si au moins une ligne est invalide, l'import échoue complètement
   - Pas d'import partiel autorisé

5. **Colonnes requises**: 
   - `article` : Référence du produit (obligatoire)
   - `emplacement` : Référence de l'emplacement (obligatoire)
   - `quantite` : Quantité disponible (obligatoire, nombre positif)

---

## 🔗 Fichiers Liés

- Vue : `apps/inventory/views/inventory_views.py` - `StockImportView`
- Service : `apps/inventory/services/stock_service.py` - `StockService`
- Use Case : `apps/inventory/usecases/stock_import_validation.py` - `StockImportValidationUseCase`
- URLs : `apps/inventory/urls.py` - ligne 47

---

**Version**: 1.0  
**Date**: 2025-01-15  
**Auteur**: Documentation API WMS

