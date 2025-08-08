# API de Création de Jobs avec Gestion des Comptages Multiples

## Description

Cette API a été modifiée pour gérer la création de jobs avec une logique avancée basée sur le mode de comptage du 1er comptage de l'inventaire. La logique détermine automatiquement si les emplacements doivent être dupliqués pour les deux comptages ou créés uniquement pour le 2ème comptage.

## Endpoint

```
POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/
```

## Logique Métier

### Cas 1 : 1er comptage = "image de stock"

**Comportement :**
- Les emplacements sont créés **uniquement** pour le 2ème comptage
- Une seule affectation (Assignment) est créée pour le 2ème comptage
- Le 1er comptage (image de stock) n'a pas d'affectation

**Raisonnement :**
- L'image de stock est un comptage automatique qui ne nécessite pas d'intervention humaine
- Seul le 2ème comptage nécessite une affectation de session et de ressources

### Cas 2 : 1er comptage différent de "image de stock"

**Comportement :**
- Les emplacements sont **dupliqués** pour les deux comptages
- Deux affectations (Assignments) sont créées (une pour chaque comptage)
- Chaque emplacement apparaît deux fois dans les JobDetails (une fois par comptage)

**Raisonnement :**
- Les deux comptages nécessitent une intervention humaine
- Chaque comptage peut avoir des résultats différents
- Les emplacements doivent être traités indépendamment pour chaque comptage

## Structure des Données Créées

### Cas 1 (Image de stock)

```json
{
  "job": {
    "id": 1,
    "reference": "JOB-123-4567-ABCD",
    "status": "EN ATTENTE"
  },
  "job_details": [
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
  "job": {
    "id": 1,
    "reference": "JOB-123-4567-ABCD",
    "status": "EN ATTENTE"
  },
  "job_details": [
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
  http://localhost:8000/api/inventory/planning/1/warehouse/1/jobs/create/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{
    "emplacements": [1, 2, 3, 4, 5]
  }'
```

**Résultat :**
- 1 job créé
- 5 JobDetails (un par emplacement, tous pour le 2ème comptage)
- 1 Assignment (pour le 2ème comptage uniquement)

### Exemple 2 : Configuration normale

**Configuration de l'inventaire :**
- 1er comptage : "en vrac"
- 2ème comptage : "par article"

**Requête :**
```bash
curl -X POST \
  http://localhost:8000/api/inventory/planning/2/warehouse/1/jobs/create/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{
    "emplacements": [1, 2, 3, 4, 5]
  }'
```

**Résultat :**
- 1 job créé
- 10 JobDetails (5 emplacements × 2 comptages)
- 2 Assignments (un pour chaque comptage)

## Réponse de l'API

### Succès (201 Created)

```json
{
  "success": true,
  "message": "Job JOB-123-4567-ABCD créé avec succès",
  "data": {
    "success": true,
    "message": "Job JOB-123-4567-ABCD créé avec succès",
    "job_id": 1,
    "job_reference": "JOB-123-4567-ABCD",
    "emplacements_count": 5,
    "counting1_mode": "image de stock",
    "counting2_mode": "par article",
    "assignments_created": 1
  }
}
```

### Erreur - Configuration invalide (400 Bad Request)

```json
{
  "success": false,
  "message": "Il faut au moins deux comptages pour l'inventaire INV-001. Comptages trouvés : 1"
}
```

## Validation et Contrôles

### Contrôles Effectués

1. **Existence des entités :**
   - Inventaire existe
   - Warehouse existe
   - Tous les emplacements existent

2. **Appartenance des emplacements :**
   - Vérification que les emplacements appartiennent au warehouse spécifié

3. **Configuration des comptages :**
   - Au moins 2 comptages requis
   - Comptages d'ordre 1 et 2 requis

4. **Doublons :**
   - Vérification qu'aucun emplacement n'est déjà affecté à un autre job pour cet inventaire

### Messages d'Erreur

| Erreur | Description |
|--------|-------------|
| `Inventaire avec l'ID {id} non trouvé` | L'inventaire n'existe pas |
| `Warehouse avec l'ID {id} non trouvé` | Le warehouse n'existe pas |
| `Emplacement non trouvé` | Un emplacement de la liste n'existe pas |
| `L'emplacement {ref} n'appartient pas au warehouse {name}` | L'emplacement n'appartient pas au warehouse |
| `L'emplacement {ref} est déjà affecté au job {ref}` | L'emplacement est déjà utilisé |
| `Il faut au moins deux comptages pour l'inventaire {ref}` | Configuration insuffisante |
| `Comptages d'ordre 1 et 2 requis` | Comptages manquants |

## Workflow Complet

### 1. Création des jobs
```
POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/
→ Jobs créés avec JobDetails et Assignments selon la configuration
```

### 2. Affectation de sessions
```
POST /api/inventory/{inventory_id}/assign-jobs/
→ Sessions affectées aux assignments existants
```

### 3. Validation des jobs
```
POST /api/inventory/jobs/validate/
→ Jobs validés pour passer au statut "VALIDE"
```

### 4. Mise en prêt
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

## Notes Techniques

- **Transaction atomique :** Toutes les opérations sont dans une transaction
- **Logging :** Les actions importantes sont loggées
- **Validation stricte :** Tous les cas d'erreur sont gérés
- **Performance :** Utilisation d'ORM optimisé pour les requêtes
- **Extensibilité :** Facile d'ajouter de nouveaux modes de comptage
