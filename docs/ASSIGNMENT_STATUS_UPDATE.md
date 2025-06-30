# Mise à jour automatique du statut des affectations

## Vue d'ensemble

L'API `assign-jobs-to-counting` a été modifiée pour mettre automatiquement à jour le statut des affectations dans la table `Assigment` quand les deux comptages (1 et 2) ont des sessions assignées.

## Règles métier

### Statut des affectations

- **EN ATTENTE** : Statut initial d'une affectation
- **AFFECTE** : Statut automatiquement assigné quand les deux comptages ont des sessions
- **PRET** : Statut assigné manuellement via l'API `jobs/ready/`
- **TRANSFERT** : Statut pour les affectations en cours de transfert
- **ENTAME** : Statut pour les affectations commencées
- **TERMINE** : Statut pour les affectations terminées

### Logique de mise à jour automatique

Le statut d'une affectation passe automatiquement à `'AFFECTE'` quand :

1. **Les deux comptages (1 et 2) existent** pour l'inventaire
2. **Les deux comptages ont des sessions assignées** (pas de sessions null)
3. **Le job a des affectations** pour les deux comptages

### Exemple de workflow

```
1. Affectation au comptage 1 avec session
   └── Statut des affectations : EN ATTENTE

2. Affectation au comptage 2 avec session
   └── Statut des affectations : AFFECTE (automatique)
   
3. Utilisation de l'API jobs/ready/
   └── Statut des affectations : PRET
```

## API Modifiée

### POST /api/inventory/{inventory_id}/assign-jobs/

Cette API met maintenant automatiquement à jour le statut des affectations.

#### Paramètres

```json
{
    "job_ids": [1, 2, 3],
    "counting_order": 1,
    "session_id": 5,
    "date_start": "2024-01-15T10:00:00Z"
}
```

#### Réponse

```json
{
    "success": true,
    "message": "1 affectations créées, 0 affectations mises à jour",
    "assignments_created": 1,
    "assignments_updated": 0,
    "total_assignments": 1,
    "counting_order": 1,
    "inventory_id": 1,
    "timestamp": "2024-01-15T10:00:00Z"
}
```

#### Comportement

1. **Premier comptage avec session** : Les affectations restent en statut `'EN ATTENTE'`
2. **Deuxième comptage avec session** : Toutes les affectations du job passent automatiquement à `'AFFECTE'`
3. **Mise à jour de la date** : `affecte_date` est automatiquement mise à jour

## Méthodes du service

### `should_update_job_status_to_affecte(job_id, inventory_id)`

Vérifie si le statut des affectations doit être mis à jour à `'AFFECTE'`.

**Retourne** : `True` si les deux comptages ont des sessions

### `update_assignments_status_to_affecte(job_id, inventory_id)`

Met à jour le statut de toutes les affectations d'un job à `'AFFECTE'` et met à jour `affecte_date`.

## Tests

### Tests unitaires

Les tests vérifient :

1. **Mise à jour automatique** : Le statut passe à `'AFFECTE'` quand les deux comptages ont des sessions
2. **Pas de mise à jour** : Le statut reste `'EN ATTENTE'` quand un seul comptage a une session
3. **Intégration API** : L'API met automatiquement à jour les statuts

### Exécution des tests

```bash
python manage.py test apps.inventory.tests.test_assignment_status_update
```

## Exemple d'utilisation

### Script Python

```python
import requests

# Affectation au premier comptage
response1 = requests.post(
    f"/api/inventory/{inventory_id}/assign-jobs/",
    json={
        "job_ids": [1, 2, 3],
        "counting_order": 1,
        "session_id": 5
    }
)

# Affectation au deuxième comptage (déclenche la mise à jour automatique)
response2 = requests.post(
    f"/api/inventory/{inventory_id}/assign-jobs/",
    json={
        "job_ids": [1, 2, 3],
        "counting_order": 2,
        "session_id": 6
    }
)

# Les affectations sont maintenant en statut 'AFFECTE'
```

### Vérification

```python
# Récupérer les affectations d'une session
assignments = requests.get(f"/api/inventory/session/{session_id}/assignments/")

# Les affectations auront le statut 'AFFECTE' si les deux comptages ont des sessions
```

## Migration de base de données

### Nouveaux champs dans Assigment

- `status` : Statut de l'affectation (EN ATTENTE, AFFECTE, PRET, etc.)
- `affecte_date` : Date de mise à jour du statut à AFFECTE
- `pret_date` : Date de mise à jour du statut à PRET
- `entame_date` : Date de mise à jour du statut à ENTAME
- `transfert_date` : Date de mise à jour du statut à TRANSFERT

### Valeur par défaut

Les affectations existantes auront le statut `'EN ATTENTE'` par défaut.

## Intégration avec l'API jobs/ready/

L'API `jobs/ready/` peut maintenant mettre à jour le statut des affectations de `'AFFECTE'` à `'PRET'` :

```python
# Marquer les jobs comme prêts
response = requests.post(
    "/api/inventory/jobs/ready/",
    json={
        "job_ids": [1, 2, 3]
    }
)

# Les affectations passent de 'AFFECTE' à 'PRET'
```

## Avantages

1. **Automatisation** : Pas besoin de mettre à jour manuellement les statuts
2. **Cohérence** : Les statuts reflètent automatiquement l'état des affectations
3. **Traçabilité** : Dates automatiques pour chaque changement de statut
4. **Intégration** : Fonctionne avec les APIs existantes

## Limitations

1. **Deux comptages requis** : La logique ne fonctionne qu'avec deux comptages
2. **Sessions obligatoires** : Les deux comptages doivent avoir des sessions
3. **Statut global** : Toutes les affectations d'un job changent de statut ensemble

## Évolutions futures

- Support pour plus de deux comptages
- Logique de statut plus granulaire par affectation
- Historique des changements de statut
- Notifications automatiques lors des changements de statut 