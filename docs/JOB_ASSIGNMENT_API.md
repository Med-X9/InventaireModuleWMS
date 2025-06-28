# API d'Affectation des Jobs de Comptage

## Vue d'ensemble

Cette API permet d'affecter des jobs de comptage à des sessions d'opérateurs avec une date de début spécifique. L'API respecte les règles métier concernant les modes de comptage et les affectations de sessions.

## Endpoints

### 1. Affecter des jobs à un comptage

**POST** `/api/inventory/assign-jobs/`

#### Description
Affecte une liste de jobs à un comptage spécifique avec une session d'opérateur et une date de début.

#### Corps de la requête
```json
{
    "job_ids": [1, 2, 3],
    "counting_order": 1,
    "session_id": 5,
    "date_start": "2024-01-15T10:00:00Z"
}
```

#### Paramètres
- `job_ids` (array, obligatoire) : Liste des IDs des jobs à affecter
- `counting_order` (integer, obligatoire) : Ordre du comptage (1, 2, ou 3)
- `session_id` (integer, optionnel) : ID de la session d'opérateur
- `date_start` (datetime, optionnel) : Date de début de l'affectation

#### Réponse de succès (201)
```json
{
    "success": true,
    "message": "3 jobs affectés avec succès",
    "assignments_created": 3,
    "counting_order": 1,
    "inventory_id": 123,
    "timestamp": "2024-01-15T10:00:00Z"
}
```

#### Réponse d'erreur (400)
```json
{
    "success": false,
    "message": "Erreur de validation",
    "error": "Impossible d'affecter une session au comptage d'ordre 1 avec le mode 'image stock'"
}
```

### 2. Récupérer les règles d'affectation

**GET** `/api/inventory/assignment-rules/`

#### Description
Récupère les règles métier pour l'affectation des jobs.

#### Réponse (200)
```json
{
    "rules": {
        "counting_modes": {
            "image_stock": {
                "description": "Comptage basé sur l'image de stock",
                "session_required": false,
                "automatic": true
            },
            "en_vrac": {
                "description": "Comptage en lot",
                "session_required": true,
                "automatic": false
            },
            "par_article": {
                "description": "Comptage article par article",
                "session_required": true,
                "automatic": false
            }
        },
        "counting_orders": {
            "1": "Premier comptage",
            "2": "Deuxième comptage",
            "3": "Troisième comptage"
        },
        "session_rules": {
            "image_stock": "Pas d'affectation de session (automatique)",
            "en_vrac": "Affectation de session obligatoire",
            "par_article": "Affectation de session obligatoire"
        }
    }
}
```

## Règles Métier

### 1. Modes de Comptage

#### Image Stock
- **Description** : Comptage basé sur l'image de stock existante
- **Session requise** : Non (automatique)
- **Affectation** : Impossible d'affecter une session manuellement

#### En Vrac
- **Description** : Comptage en lot
- **Session requise** : Oui
- **Affectation** : Session obligatoire

#### Par Article
- **Description** : Comptage article par article
- **Session requise** : Oui
- **Affectation** : Session obligatoire

### 2. Ordres de Comptage

- **1** : Premier comptage
- **2** : Deuxième comptage
- **3** : Troisième comptage

### 3. Règles d'Affectation

1. **Tous les jobs doivent appartenir au même inventaire**
2. **Un job ne peut avoir qu'une seule affectation**
3. **Pour le mode "image stock"** : Pas d'affectation de session possible
4. **Pour les modes "en vrac" et "par article"** : Session obligatoire
5. **La session doit être un opérateur valide**

## Exemples d'Utilisation

### Exemple 1 : Affectation pour comptage "en vrac"

```bash
curl -X POST http://localhost:8000/api/inventory/assign-jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "job_ids": [1, 2, 3],
    "counting_order": 2,
    "session_id": 5,
    "date_start": "2024-01-15T10:00:00Z"
  }'
```

### Exemple 2 : Affectation pour comptage "image stock"

```bash
curl -X POST http://localhost:8000/api/inventory/assign-jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "job_ids": [4, 5, 6],
    "counting_order": 1
  }'
```

## Codes d'Erreur

| Code | Description |
|------|-------------|
| 400 | Données invalides ou règle métier non respectée |
| 401 | Non authentifié |
| 404 | Ressource non trouvée |
| 500 | Erreur interne du serveur |

## Messages d'Erreur Courants

- `"La liste des IDs des jobs est obligatoire"`
- `"L'ordre du comptage doit être 1, 2 ou 3"`
- `"Tous les jobs doivent appartenir au même inventaire"`
- `"Le job JOB123 a déjà une affectation"`
- `"Impossible d'affecter une session au comptage d'ordre 1 avec le mode 'image stock'"`
- `"Session avec l'ID 5 non trouvée ou n'est pas un opérateur"` 