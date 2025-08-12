# API de Suppression d'Emplacements d'un Job avec Gestion des Comptages Multiples

## Description

Cette API permet de supprimer des emplacements d'un job existant avec une logique avancée basée sur le mode de comptage du 1er comptage de l'inventaire. La logique détermine automatiquement si les emplacements doivent être supprimés pour les deux comptages ou uniquement pour le 2ème comptage.

## Endpoint

```
DELETE /api/jobs/{job_id}/remove-emplacements/
```

## Logique Métier

### Cas 1 : 1er comptage = "image de stock"

**Comportement :**
- Les emplacements sont supprimés **uniquement** pour le 2ème comptage
- Si plus aucun JobDetail pour le 2ème comptage, l'affectation (Assignment) est supprimée
- Le 1er comptage (image de stock) n'est pas affecté

**Raisonnement :**
- L'image de stock est un comptage automatique qui ne nécessite pas d'intervention humaine
- Seul le 2ème comptage nécessite une affectation de session et de ressources
- La suppression ne concerne que les emplacements du 2ème comptage

### Cas 2 : 1er comptage différent de "image de stock"

**Comportement :**
- Les emplacements sont **supprimés** pour les deux comptages
- Si plus aucun JobDetail pour un comptage, l'affectation correspondante est supprimée
- Chaque emplacement est supprimé des deux comptages

**Raisonnement :**
- Les deux comptages nécessitent une intervention humaine
- Chaque comptage peut avoir des résultats différents
- Les emplacements doivent être supprimés des deux comptages pour maintenir la cohérence

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
| `emplacement_ids` | Array[Integer] | Liste des IDs des emplacements à supprimer du job | Oui | Non vide, tous les emplacements doivent exister |

## Réponse

### Succès (200 OK)

```json
{
    "success": true,
    "message": "3 emplacements supprimés du job JOB-123-4567-ABCD",
    "data": {
        "success": true,
        "message": "3 emplacements supprimés du job JOB-123-4567-ABCD",
        "job_id": 1,
        "job_reference": "JOB-123-4567-ABCD",
        "emplacements_deleted": 3,
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
    "message": "Il faut au moins deux comptages pour l'inventaire INV001. Comptages trouvés : 1"
}
```

## Structure des Données Supprimées

### Cas 1 (Image de stock)

```json
{
  "job_details_deleted": [
    {
      "id": 1,
      "location_id": 1,
      "counting_id": 2,  // 2ème comptage uniquement
      "status": "EN ATTENTE"
    }
  ],
  "assignments_affected": [
    {
      "id": 1,
      "counting_id": 2,  // 2ème comptage uniquement (supprimé si plus de JobDetails)
      "status": "EN ATTENTE"
    }
  ]
}
```

### Cas 2 (Comptage normal)

```json
{
  "job_details_deleted": [
    {
      "id": 1,
      "location_id": 1,
      "counting_id": 1,  // 1er comptage
      "status": "EN ATTENTE"
    },
    {
      "id": 2,
      "location_id": 1,
      "counting_id": 2,  // 2ème comptage
      "status": "EN ATTENTE"
    }
  ],
  "assignments_affected": [
    {
      "id": 1,
      "counting_id": 1,  // 1er comptage (supprimé si plus de JobDetails)
      "status": "EN ATTENTE"
    },
    {
      "id": 2,
      "counting_id": 2,  // 2ème comptage (supprimé si plus de JobDetails)
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
curl -X DELETE \
  http://localhost:8000/api/jobs/1/remove-emplacements/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{
    "emplacement_ids": [1, 2, 3]
  }'
```

**Résultat :**
- 3 JobDetails supprimés (un par emplacement, tous pour le 2ème comptage)
- 1 Assignment supprimé (si plus de JobDetails pour le 2ème comptage)

### Exemple 2 : Configuration normale

**Configuration de l'inventaire :**
- 1er comptage : "en vrac"
- 2ème comptage : "par article"

**Requête :**
```bash
curl -X DELETE \
  http://localhost:8000/api/jobs/2/remove-emplacements/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{
    "emplacement_ids": [1, 2, 3]
  }'
```

**Résultat :**
- 6 JobDetails supprimés (3 emplacements × 2 comptages)
- 2 Assignments supprimés (si plus de JobDetails pour chaque comptage)

## Validation et Contrôles

### Contrôles Effectués

1. **Validation des paramètres d'entrée :**
   - job_id doit être un entier positif
   - emplacement_ids doit être une liste non vide
   - Tous les IDs d'emplacements doivent être des entiers positifs

2. **Existence des entités :**
   - Job existe
   - Tous les emplacements existent
   - Le job contient des emplacements à supprimer

3. **Configuration des comptages :**
   - Au moins 2 comptages requis
   - Comptages d'ordre 1 et 2 requis

4. **Gestion des affectations :**
   - Vérification et suppression des affectations si plus de JobDetails pour un comptage

### Messages d'Erreur

#### Erreurs de Validation (400 Bad Request)

| Erreur | Description | Type |
|--------|-------------|------|
| `ID de job invalide` | job_id est 0, négatif ou None | validation_error |
| `Liste d'emplacements vide` | emplacement_ids est vide ou None | validation_error |
| `emplacement_ids doit être une liste` | Type incorrect pour emplacement_ids | validation_error |
| `IDs d'emplacements invalides: [liste]` | IDs non entiers ou négatifs | validation_error |

#### Erreurs Métier (400 Bad Request)

| Erreur | Description | Type |
|--------|-------------|------|
| `Job avec l'ID {id} non trouvé` | Le job n'existe pas | business_error |
| `Emplacements non trouvés: [liste]` | Un ou plusieurs emplacements n'existent pas | business_error |
| `Aucun emplacement à supprimer trouvé dans le job {ref}` | Les emplacements ne sont pas dans le job | business_error |
| `Il faut au moins deux comptages pour l'inventaire {ref}` | Configuration insuffisante | business_error |
| `Comptage d'ordre 1 manquant` | 1er comptage manquant | business_error |
| `Comptage d'ordre 2 manquant` | 2ème comptage manquant | business_error |
| `Aucun emplacement supprimé du job {ref}` | Aucune suppression effectuée | business_error |

#### Erreurs Internes (500 Internal Server Error)

| Erreur | Description | Type |
|--------|-------------|------|
| `Erreur interne du serveur` | Erreur inattendue du système | internal_error |

## Workflow Complet

### 1. Création du job (si nécessaire)
```
POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/
→ Job créé avec JobDetails et Assignments selon la configuration
```

### 2. Ajout d'emplacements au job (optionnel)
```
POST /api/jobs/{job_id}/add-emplacements/
→ Emplacements ajoutés avec JobDetails et Assignments selon la configuration
```

### 3. Suppression d'emplacements du job
```
DELETE /api/jobs/{job_id}/remove-emplacements/
→ Emplacements supprimés avec gestion des JobDetails et Assignments selon la configuration
```

### 4. Affectation de sessions (optionnel)
```
POST /api/inventory/{inventory_id}/assign-jobs/
→ Sessions affectées aux assignments existants
```

### 5. Validation des jobs
```
POST /api/inventory/jobs/validate/
→ Jobs validés pour passer au statut "VALIDE"
```

### 6. Mise en prêt
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
6. **Réutilisabilité :** Même logique que les autres opérations sur les jobs

## Gestion des Exceptions

### Types d'Exceptions

1. **JobCreationError :** Exceptions métier personnalisées
   - Levées pour les erreurs de logique métier
   - Retournent un message d'erreur clair
   - Gérées dans le use case et la vue

2. **ValidationError :** Exceptions de validation Django
   - Levées pour les erreurs de validation des modèles
   - Converties en JobCreationError dans le use case

3. **Exception générique :** Erreurs inattendues
   - Capturées et loggées pour le debugging
   - Retournent un message générique à l'utilisateur

### Gestion dans le Use Case

```python
try:
    # Logique métier
    with transaction.atomic():
        # Opérations de suppression
        pass
except JobCreationError:
    # Re-raise sans modification
    raise
except ValidationError as e:
    # Convertir en JobCreationError
    raise JobCreationError(f"Erreur de validation: {str(e)}")
except Exception as e:
    # Logger et convertir en JobCreationError
    logger.error(f"Erreur inattendue: {str(e)}")
    raise JobCreationError(f"Erreur inattendue: {str(e)}")
```

### Gestion dans la Vue

```python
try:
    # Validation des paramètres
    # Appel du use case
    result = use_case.execute(job_id, emplacement_ids)
    return Response({'success': True, 'data': result})
except JobCreationError as e:
    return Response({
        'success': False,
        'message': str(e),
        'error_type': 'business_error'
    }, status=400)
except ValidationError as e:
    return Response({
        'success': False,
        'message': f'Erreur de validation: {str(e)}',
        'error_type': 'validation_error'
    }, status=400)
except Exception as e:
    logger.error(f"Erreur inattendue: {str(e)}")
    return Response({
        'success': False,
        'message': 'Erreur interne du serveur',
        'error_type': 'internal_error'
    }, status=500)
```

## Notes Techniques

- **Transaction atomique :** Toutes les opérations sont dans une transaction
- **Logging :** Les actions importantes sont loggées
- **Validation stricte :** Tous les cas d'erreur sont gérés
- **Performance :** Utilisation d'ORM optimisé pour les requêtes
- **Extensibilité :** Facile d'ajouter de nouveaux modes de comptage
- **Gestion des affectations :** Suppression automatique des affectations si plus de JobDetails
- **Gestion des comptages :** Suppression selon la logique métier
- **Gestion d'exceptions robuste :** Validation complète des paramètres et gestion des erreurs

## Différences avec les autres APIs

### API de Création de Jobs
- Crée un nouveau job
- Crée tous les JobDetails et Assignments
- Gère la logique complète de création

### API d'Ajout d'Emplacements
- Ajoute des emplacements à un job existant
- Vérifie les emplacements déjà présents
- Crée seulement les JobDetails et Assignments manquants

### API de Suppression d'Emplacements
- Supprime des emplacements d'un job existant
- Supprime les JobDetails selon la logique des comptages
- Supprime les Assignments si plus de JobDetails pour un comptage

## Cas d'Usage Courants

### Suppression d'emplacements d'un job existant
1. Job créé avec plusieurs emplacements
2. Suppression d'emplacements selon les besoins
3. Mise à jour automatique des affectations
4. Reprise du workflow de validation

### Modification de la couverture d'un job
1. Job existant avec emplacements
2. Suppression d'emplacements pour réduire la couverture
3. Mise à jour des affectations si nécessaire
4. Reprise du workflow de validation

### Nettoyage d'un job
1. Job avec emplacements non désirés
2. Suppression en lot des emplacements
3. Suppression automatique des affectations orphelines
4. Job prêt pour de nouvelles affectations
