# API d'Affectation des Jobs de Comptage

## Vue d'ensemble

Cette API permet d'affecter des jobs de comptage à des sessions d'opérateurs avec une date de début spécifique. L'API respecte les règles métier concernant les modes de comptage et les affectations de sessions.

**Note importante** : 
- Si un job a déjà une affectation, l'API mettra à jour l'affectation existante au lieu de lever une erreur.
- **Une même session peut être affectée à plusieurs jobs différents** (un opérateur peut gérer plusieurs jobs).

## Endpoints

### 1. Affecter des jobs à un comptage

**POST** `/api/inventory/{inventory_id}/assign-jobs/`

#### Description
Affecte une liste de jobs à un comptage spécifique avec une session d'opérateur et une date de début. Si un job a déjà une affectation, elle sera mise à jour.

#### Paramètres d'URL
- `inventory_id` (integer, obligatoire) : ID de l'inventaire

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
- `counting_order` (integer, obligatoire) : Ordre du comptage (1 ou 2)
- `session_id` (integer, optionnel) : ID de la session d'opérateur
- `date_start` (datetime, optionnel) : Date de début de l'affectation

#### Réponse de succès (201)
```json
{
    "success": true,
    "message": "2 affectations créées, 1 affectation mise à jour",
    "assignments_created": 2,
    "assignments_updated": 1,
    "total_assignments": 3,
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

#### Réponse d'erreur (400) - Statut de job invalide
```json
{
    "success": false,
    "message": "Erreur de validation",
    "error": "Les jobs en statut 'EN ATTENTE' ne peuvent pas être affectés. Ils doivent d'abord être validés. Jobs invalides : Job JOB123456 (statut: EN ATTENTE)"
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
            "2": "Deuxième comptage"
        },
        "session_rules": {
            "image_stock": "Pas d'affectation de session (automatique)",
            "en_vrac": "Affectation de session obligatoire",
            "par_article": "Affectation de session obligatoire"
        }
    }
}
```

### 3. Récupérer les affectations d'une session

**GET** `/api/inventory/session/{session_id}/assignments/`

#### Description
Récupère toutes les affectations d'une session spécifique.

#### Paramètres d'URL
- `session_id` (integer, obligatoire) : ID de la session

#### Réponse (200)
```json
{
    "success": true,
    "session_id": 5,
    "assignments_count": 3,
    "assignments": [
        {
            "id": 1,
            "reference": "ASS123456",
            "job_id": 1,
            "job_reference": "JOB123456",
            "counting_id": 1,
            "counting_order": 1,
            "counting_mode": "image stock",
            "date_start": "2024-01-15T10:00:00Z",
            "session_id": 5,
            "session_username": "mobile1",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        },
        {
            "id": 2,
            "reference": "ASS789012",
            "job_id": 2,
            "job_reference": "JOB789012",
            "counting_id": 2,
            "counting_order": 2,
            "counting_mode": "en vrac",
            "date_start": "2024-01-15T10:00:00Z",
            "session_id": 5,
            "session_username": "mobile1",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
    ]
}
```

### 4. Supprimer des jobs

**DELETE** `/api/inventory/jobs/delete/`

#### Description
Supprime définitivement une liste de jobs. Seuls les jobs en statut "EN ATTENTE" peuvent être supprimés.

#### Corps de la requête
```json
{
    "job_ids": [1, 2, 3]
}
```

#### Paramètres
- `job_ids` (array, obligatoire) : Liste des IDs des jobs à supprimer

#### Réponse de succès (200)
```json
{
    "success": true,
    "message": "3 jobs supprimés avec succès",
    "results": [
        {
            "job_id": 1,
            "success": true,
            "data": {
                "job_id": 1,
                "job_reference": "JOB123456",
                "deleted_assigments_count": 2,
                "deleted_job_details_count": 3
            }
        }
    ]
}
```

#### Réponse d'erreur (400) - Validation échouée
```json
{
    "success": false,
    "message": "Impossible de supprimer les jobs. Vérifications échouées.",
    "errors": [
        "Job JOB789012 (ID: 2) ne peut pas être supprimé. Statut actuel : VALIDE",
        "Job avec l'ID 4 non trouvé"
    ]
}
```

**Note importante** : Si un seul job ne peut pas être supprimé (statut incorrect, job inexistant, etc.), **aucun job ne sera supprimé**. L'opération est atomique - soit tous les jobs sont supprimés, soit aucun.

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

### 3. Règles d'Affectation

1. **Tous les jobs doivent appartenir au même inventaire**
2. **Si un job a déjà une affectation** : L'affectation existante sera mise à jour
3. **Une session peut être affectée à plusieurs jobs** : Un opérateur peut gérer plusieurs jobs simultanément
4. **Seuls les jobs en statut "EN ATTENTE" ne peuvent pas être affectés** : Tous les autres statuts (VALIDE, AFFECTE, PRET, TRANSFERT, ENTAME, TERMINE) peuvent être affectés
5. **Pour le mode "image stock"** : Pas d'affectation de session possible
6. **Pour les modes "en vrac" et "par article"** : Session obligatoire
7. **La session doit être un mobile valide**

### 4. Comportement de Mise à Jour

- **Nouvelle affectation** : Si le job n'a pas d'affectation pour ce comptage spécifique, une nouvelle est créée
- **Mise à jour** : Si le job a déjà une affectation pour ce comptage, elle est mise à jour avec les nouvelles données
- **Indépendance des comptages** : Les affectations pour différents comptages (1 et 2) sont indépendantes. Affecter un job au comptage 1 n'affecte pas son affectation au comptage 2
- **Statut du job** : Toujours mis à jour vers "AFFECTE" avec la date d'affectation
- **Gestion des doublons** : Si plusieurs affectations existent pour le même job et le même comptage, seule la plus récente est conservée

### 5. Règles de Suppression

1. **Seuls les jobs en statut "EN ATTENTE" peuvent être supprimés**
2. **Suppression en cascade** : Les affectations et job details associés sont également supprimés
3. **Suppression multiple** : Plusieurs jobs peuvent être supprimés en une seule requête
4. **Gestion des erreurs** : Si certains jobs ne peuvent pas être supprimés, l'API retourne un statut 207 avec les détails

## Exemples d'Utilisation

### Exemple 1 : Affectation pour comptage "en vrac"

```bash
curl -X POST http://localhost:8000/api/inventory/123/assign-jobs/ \
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
curl -X POST http://localhost:8000/api/inventory/123/assign-jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "job_ids": [4, 5, 6],
    "counting_order": 1
  }'
```

### Exemple 3 : Affectations indépendantes par comptage

```bash
# Première affectation : comptage 1
curl -X POST http://localhost:8000/api/inventory/123/assign-jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "job_ids": [1, 2],
    "counting_order": 1,
    "session_id": 5,
    "date_start": "2024-01-15T10:00:00Z"
  }'

# Deuxième affectation : comptage 2 (indépendante)
curl -X POST http://localhost:8000/api/inventory/123/assign-jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "job_ids": [1, 2],
    "counting_order": 2,
    "session_id": 6,
    "date_start": "2024-01-16T10:00:00Z"
  }'

# Mise à jour : comptage 1 (n'affecte pas le comptage 2)
curl -X POST http://localhost:8000/api/inventory/123/assign-jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "job_ids": [1],
    "counting_order": 1,
    "session_id": 7,
    "date_start": "2024-01-17T10:00:00Z"
  }'
```

**Résultat** : Le job 1 aura 2 affectations indépendantes :
- Une pour le comptage 1 (session 7, date 2024-01-17)
- Une pour le comptage 2 (session 6, date 2024-01-16)

### Exemple 4 : Récupérer les affectations d'une session

```bash
curl -X GET http://localhost:8000/api/inventory/session/5/assignments/ \
  -H "Authorization: Bearer <token>"
```

### Exemple 5 : Supprimer plusieurs jobs

```bash
curl -X DELETE http://localhost:8000/api/inventory/jobs/delete/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "job_ids": [1, 2, 3]
  }'
```

**Réponse de succès (200)**
```json
{
    "success": true,
    "message": "3 jobs supprimés avec succès",
    "results": [
        {
            "job_id": 1,
            "success": true,
            "data": {
                "job_id": 1,
                "job_reference": "JOB123456",
                "deleted_assigments_count": 2,
                "deleted_job_details_count": 3
            }
        }
    ]
}
```

**Réponse d'erreur (400) - Validation échouée**
```json
{
    "success": false,
    "message": "Impossible de supprimer les jobs. Vérifications échouées.",
    "errors": [
        "Job JOB789012 (ID: 2) ne peut pas être supprimé. Statut actuel : VALIDE",
        "Job avec l'ID 4 non trouvé"
    ]
}
```

**Note importante** : Si un seul job ne peut pas être supprimé (statut incorrect, job inexistant, etc.), **aucun job ne sera supprimé**. L'opération est atomique - soit tous les jobs sont supprimés, soit aucun.

## Codes d'Erreur

| Code | Description |
|------|-------------|
| 200 | Succès complet |
| 201 | Ressource créée |
| 207 | Succès partiel (certaines opérations ont échoué) |
| 400 | Données invalides ou règle métier non respectée |
| 401 | Non authentifié |
| 404 | Ressource non trouvée |
| 500 | Erreur interne du serveur |

## Messages d'Erreur Courants

- `"La liste des IDs des jobs est obligatoire"`
- `"L'ordre du comptage doit être 1 ou 2"`
- `"Tous les jobs doivent appartenir au même inventaire"`
- `"Impossible d'affecter une session au comptage d'ordre 1 avec le mode 'image stock'"`
- `"Session avec l'ID 5 non trouvée ou n'est pas un mobile"`
- `"Seuls les jobs en attente peuvent être supprimés"`

## Champs de Réponse

### Réponse d'Affectation

| Champ | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indique si l'opération a réussi |
| `message` | string | Message descriptif du résultat |
| `assignments_created` | integer | Nombre d'affectations créées |
| `assignments_updated` | integer | Nombre d'affectations mises à jour |
| `total_assignments` | integer | Nombre total d'affectations traitées |
| `counting_order` | integer | Ordre du comptage utilisé |
| `inventory_id` | integer | ID de l'inventaire |
| `timestamp` | datetime | Horodatage de l'opération |

### Réponse des Affectations par Session

| Champ | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indique si l'opération a réussi |
| `session_id` | integer | ID de la session |
| `assignments_count` | integer | Nombre d'affectations de la session |
| `assignments` | array | Liste des affectations avec détails |

### Réponse de Suppression de Jobs

| Champ | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indique si l'opération a réussi |
| `message` | string | Message descriptif du résultat |
| `results` | array | Détails de chaque suppression (succès/échec) | 