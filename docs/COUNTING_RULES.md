# Règles Métier - Modes de Comptage d'Inventaire

## Vue d'ensemble

Un inventaire contient **exactement 3 comptages** avec des règles métier strictes concernant les combinaisons de modes autorisées.

## Modes de Comptage Disponibles

1. **"en vrac"** - Comptage en lot
2. **"par article"** - Comptage article par article  
3. **"image stock"** - Comptage basé sur l'image de stock

## Règles Métier

### Règle 1 : Nombre de Comptages
- **Obligatoire** : Exactement 3 comptages par inventaire
- **Ordre** : Les comptages doivent avoir les ordres 1, 2, 3

### Règle 2 : Position du Mode "image stock"
- **"image stock"** ne peut être utilisé que dans le **1er comptage** (order=1)
- **Interdiction** : "image stock" ne peut pas être utilisé dans les 2e ou 3e comptages

### Règle 3 : Combinaisons Autorisées

#### Scénario A : Premier comptage = "image stock"
```
1er comptage : "image stock"
2e comptage  : "en vrac" OU "par article"
3e comptage  : Même mode que le 2e comptage
```

**Exemples valides :**
- `image stock` → `en vrac` → `en vrac`
- `image stock` → `par article` → `par article`

**Exemples invalides :**
- `image stock` → `en vrac` → `par article` ❌ (modes différents)
- `image stock` → `image stock` → `en vrac` ❌ (image stock en 2e position)

#### Scénario B : Premier comptage ≠ "image stock"
```
1er comptage : "en vrac" OU "par article"
2e comptage  : "en vrac" OU "par article"
3e comptage  : "en vrac" OU "par article"
```

**Exemples valides :**
- `en vrac` → `en vrac` → `en vrac`
- `par article` → `par article` → `par article`
- `en vrac` → `par article` → `en vrac`
- `par article` → `en vrac` → `par article`

**Exemples invalides :**
- `en vrac` → `image stock` → `par article` ❌ (image stock en 2e position)

## Validation Technique

### Niveaux de Validation

1. **Serializer** (`InventoryCreateSerializer`) : Validation des données d'entrée
2. **Use Case** (`InventoryCreationUseCase`) : Validation métier complète
3. **Service** (`CountingService`) : Validation de cohérence

### Messages d'Erreur

- `"Un inventaire doit contenir exactement 3 comptages"`
- `"Les comptages doivent avoir les ordres 1, 2, 3"`
- `"Si le premier comptage est 'image stock', les 2e et 3e comptages doivent avoir le même mode"`
- `"Si le premier comptage n'est pas 'image stock', tous les comptages doivent être 'en vrac' ou 'par article'"`

## Architecture

### Use Cases
- `CountingByInBulk` : Gestion du mode "en vrac"
- `CountingByArticle` : Gestion du mode "par article"
- `CountingByStockimage` : Gestion du mode "image stock"

### Dispatcher
- `CountingDispatcher` : Route vers le bon use case selon le mode

### Validation
- Validation déclarative par règles dans chaque use case
- Validation de cohérence globale dans le service
- Validation des données d'entrée dans le serializer

## Exemples d'Utilisation API

### Exemple 1 : Image Stock + En Vrac
```json
{
  "label": "Inventaire Test",
  "date": "2024-01-15",
  "account_id": 1,
  "warehouse": [
    {"id": 1, "date": "2024-01-15"}
  ],
  "comptages": [
    {"order": 1, "count_mode": "image stock"},
    {"order": 2, "count_mode": "en vrac"},
    {"order": 3, "count_mode": "en vrac"}
  ]
}
```

### Exemple 2 : Tous En Vrac
```json
{
  "label": "Inventaire Test",
  "date": "2024-01-15",
  "account_id": 1,
  "warehouse": [
    {"id": 1, "date": "2024-01-15"}
  ],
  "comptages": [
    {"order": 1, "count_mode": "en vrac"},
    {"order": 2, "count_mode": "en vrac"},
    {"order": 3, "count_mode": "en vrac"}
  ]
}
```

### Exemple 3 : Mixte Par Article
```json
{
  "label": "Inventaire Test",
  "date": "2024-01-15",
  "account_id": 1,
  "warehouse": [
    {"id": 1, "date": "2024-01-15"}
  ],
  "comptages": [
    {"order": 1, "count_mode": "par article"},
    {"order": 2, "count_mode": "en vrac"},
    {"order": 3, "count_mode": "par article"}
  ]
}
``` 