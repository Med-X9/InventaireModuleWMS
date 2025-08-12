# API d'Ajout d'Emplacements à un Job avec Gestion des Comptages Multiples

## Description

Cette API permet d'ajouter des emplacements à un job existant avec une logique avancée basée sur le mode de comptage du 1er comptage de l'inventaire. La logique détermine automatiquement si les emplacements doivent être dupliqués pour les deux comptages ou créés uniquement pour le 2ème comptage.

## Endpoint

```
POST /api/jobs/{job_id}/add-emplacements/
```

## Logique Métier

### Cas 1 : 1er comptage = "image de stock"

**Comportement :**
- Les emplacements sont ajoutés **uniquement** pour le 2ème comptage
- Une affectation (Assignment) est créée pour le 2ème comptage si elle n'existe pas
- Le 1er comptage (image de stock) n'a pas d'affectation

**Raisonnement :**
- L'image de stock est un comptage automatique qui ne nécessite pas d'intervention humaine
- Seul le 2ème comptage nécessite une affectation de session et de ressources

### Cas 2 : 1er comptage différent de "image de stock"

**Comportement :**
- Les emplacements sont **dupliqués** pour les deux comptages
- Des affectations (Assignments) sont créées pour chaque comptage si elles n'existent pas
- Chaque emplacement apparaît deux fois dans les JobDetails (une fois par comptage)

**Raisonnement :**
- Les deux comptages nécessitent une intervention humaine
- Chaque comptage peut avoir des résultats différents
- Les emplacements doivent être traités indépendamment pour chaque comptage

## Paramètres d'URL

| Paramètre | Type | Description | Requis |
|-----------|------|-------------|--------|
| `job_id` | Integer | ID du job | Oui |

## Authentification

Cette API nécessite une authentification. Incluez le token d'authentification dans l'en-tête de la requête :

```
Authorization: Token <your_token>
```

## Corps de la requête

### Format JSON

```json
{
    "emplacement_ids": [1, 2, 3, 4, 5]
}
```

### Paramètres du corps

| Paramètre | Type | Description | Requis | Validation |
|-----------|------|-------------|--------|------------|
| `emplacement_ids` | Array[Integer] | Liste des IDs des emplacements à ajouter au job | Oui | Non vide, tous les emplacements doivent exister et ne pas être déjà affectés à un autre job |

## Réponse

### Succès (200 OK)

```json
{
    "success": true,
    "message": "3 emplacements ajoutés au job JOB-123-4567-ABCD",
    "data": {
        "success": true,
        "message": "3 emplacements ajoutés au job JOB-123-4567-ABCD",
        "job_id": 1,
        "job_reference": "JOB-123-4567-ABCD",
        "emplacements_added": 3,
        "counting1_mode": "image de stock",
        "counting2_mode": "par article",
        "assignments_count": 1
    }
}
```

### Erreur - Validation des données (400 Bad Request)

#### Erreur de validation du serializer

```json
{
    "success": false,
    "message": "Erreur de validation",
    "errors": {
        "emplacement_ids": [
            "Cette liste ne peut pas être vide."
        ]
    }
}
```

#### Erreur métier

```json
{
    "success": false,
    "message": "Job avec l'ID 999 non trouvé"
}
```

```json
{
    "success": false,
    "message": "Emplacement avec l'ID 999 non trouvé"
}
```

```json
{
    "success": false,
    "message": "L'emplacement LOC001 est déjà affecté au job JOB002"
}
```

```json
{
    "success": false,
    "message": "Il faut au moins deux comptages pour l'inventaire INV001. Comptages trouvés : 1"
}
```

## Structure des Données Créées

### Cas 1 (Image de stock)

```json
{
  "job_details_added": [
    {
      "id": 1,
      "location_id": 1,
      "counting_id": 2,  // 2ème comptage uniquement
      "status": "EN ATTENTE"
    }
  ],
  "assignments": [
    {
      "id": 1,
      "counting_id": 2,  // 2ème comptage uniquement
      "status": "EN ATTENTE"
    }
  ]
}
```

### Cas 2 (Comptage normal)

```json
{
  "job_details_added": [
    {
      "id": 1,
      "location_id": 1,
      "counting_id": 1,  // 1er comptage
      "status": "EN ATTENTE"
    },
    {
      "id": 2,
      "location_id": 1,
      "counting_id": 2,  // 2ème comptage (dupliqué)
      "status": "EN ATTENTE"
    }
  ],
  "assignments": [
    {
      "id": 1,
      "counting_id": 1,  // 1er comptage
      "status": "EN ATTENTE"
    },
    {
      "id": 2,
      "counting_id": 2,  // 2ème comptage
      "status": "EN ATTENTE"
    }
  ]
}
```

## Exemples d'Utilisation

### Exemple 1 : Configuration "Image de stock"

**Configuration de l'inventaire :**
- 1er comptage : "image de stock"
- 2ème comptage : "par article"

**Requête :**
```bash
curl -X POST \
  http://localhost:8000/api/jobs/1/add-emplacements/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{
    "emplacement_ids": [1, 2, 3]
  }'
```

**Résultat :**
- 3 JobDetails ajoutés (un par emplacement, tous pour le 2ème comptage)
- 1 Assignment (pour le 2ème comptage uniquement)

### Exemple 2 : Configuration normale

**Configuration de l'inventaire :**
- 1er comptage : "en vrac"
- 2ème comptage : "par article"

**Requête :**
```bash
curl -X POST \
  http://localhost:8000/api/jobs/2/add-emplacements/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{
    "emplacement_ids": [1, 2, 3]
  }'
```

**Résultat :**
- 6 JobDetails ajoutés (3 emplacements × 2 comptages)
- 2 Assignments (un pour chaque comptage)

## Validation et Contrôles

### Contrôles Effectués

1. **Existence des entités :**
   - Job existe
   - Tous les emplacements existent

2. **Configuration des comptages :**
   - Au moins 2 comptages requis
   - Comptages d'ordre 1 et 2 requis

3. **Doublons :**
   - Vérification qu'aucun emplacement n'est déjà affecté à un autre job pour cet inventaire
   - Vérification qu'aucun emplacement n'est déjà dans le job pour le même comptage

4. **Affectations existantes :**
   - Vérification et création des affectations si nécessaire

### Messages d'Erreur

| Erreur | Description |
|--------|-------------|
| `Job avec l'ID {id} non trouvé` | Le job n'existe pas |
| `Emplacement non trouvé` | Un emplacement de la liste n'existe pas |
| `L'emplacement {ref} est déjà affecté au job {ref}` | L'emplacement est déjà utilisé par un autre job |
| `Il faut au moins deux comptages pour l'inventaire {ref}` | Configuration insuffisante |
| `Comptages d'ordre 1 et 2 requis` | Comptages manquants |

## Workflow Complet

### 1. Création du job (si nécessaire)
```
POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/
→ Job créé avec JobDetails et Assignments selon la configuration
```

### 2. Ajout d'emplacements au job
```
POST /api/jobs/{job_id}/add-emplacements/
→ Emplacements ajoutés avec JobDetails et Assignments selon la configuration
```

### 3. Affectation de sessions (optionnel)
```
POST /api/inventory/{inventory_id}/assign-jobs/
→ Sessions affectées aux assignments existants
```

### 4. Validation des jobs
```
POST /api/inventory/jobs/validate/
→ Jobs validés pour passer au statut "VALIDE"
```

### 5. Mise en prêt
```
POST /api/inventory/jobs/ready/
→ Jobs mis en PRET selon les règles métier
```

## Avantages de cette Approche

1. **Flexibilité :** S'adapte automatiquement à la configuration de l'inventaire
2. **Cohérence :** Respecte les règles métier selon le type de comptage
3. **Traçabilité :** Chaque comptage est traité indépendamment
4. **Performance :** Optimise les ressources selon les besoins réels
5. **Maintenabilité :** Logique centralisée dans le use case
6. **Réutilisabilité :** Même logique que la création de jobs

## Notes Techniques

- **Transaction atomique :** Toutes les opérations sont dans une transaction
- **Logging :** Les actions importantes sont loggées
- **Validation stricte :** Tous les cas d'erreur sont gérés
- **Performance :** Utilisation d'ORM optimisé pour les requêtes
- **Extensibilité :** Facile d'ajouter de nouveaux modes de comptage
- **Gestion des doublons :** Vérification et évitement des emplacements déjà présents
- **Gestion des affectations :** Création automatique des affectations si nécessaire

## Différences avec l'API de Création

### API de Création de Jobs
- Crée un nouveau job
- Crée tous les JobDetails et Assignments
- Gère la logique complète de création

### API d'Ajout d'Emplacements
- Ajoute des emplacements à un job existant
- Vérifie les emplacements déjà présents
- Crée seulement les JobDetails et Assignments manquants
- Réutilise la même logique métier

## Cas d'Usage Courants

### Ajout d'emplacements à un job existant
1. Job créé avec quelques emplacements
2. Ajout d'emplacements supplémentaires selon les besoins
3. Affectation de sessions aux nouveaux assignments
4. Validation et mise en prêt

### Modification de la couverture d'un job
1. Job existant avec emplacements
2. Ajout d'emplacements pour étendre la couverture
3. Mise à jour des affectations si nécessaire
4. Reprise du workflow de validation
