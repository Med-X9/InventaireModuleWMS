# API de Mise en Prêt des Jobs Affectés

## Description

Cette API permet de mettre plusieurs jobs affectés au statut "PRET" en une seule requête. Seuls les jobs ayant le statut "AFFECTE" peuvent être mis au statut "PRET".

## Endpoint

```
POST /api/inventory/jobs/ready/
```

## Paramètres de requête

### Body (JSON)

```json
{
    "job_ids": [1, 2, 3, 4, 5]
}
```

- `job_ids` (array, obligatoire) : Liste des IDs des jobs à mettre au statut "PRET"
  - Minimum : 1 job
  - Maximum : Aucune limite pratique

## Réponse

### Succès (200 OK)

```json
{
    "success": true,
    "message": "Jobs mis au statut PRET avec succès",
    "data": {
        "ready_jobs_count": 3,
        "ready_jobs": [
            {
                "job_id": 1,
                "job_reference": "JOB12345678"
            },
            {
                "job_id": 2,
                "job_reference": "JOB87654321"
            },
            {
                "job_id": 3,
                "job_reference": "JOB11111111"
            }
        ],
        "ready_date": "2024-01-15T10:30:00Z"
    }
}
```

### Erreur (400 Bad Request)

#### Jobs non trouvés
```json
{
    "success": false,
    "message": "Jobs non trouvés avec les IDs : 999, 888. Jobs trouvés : JOB12345678, JOB87654321"
}
```

#### Statuts invalides
```json
{
    "success": false,
    "message": "Seuls les jobs affectés peuvent être mis au statut PRET. Jobs invalides : Job JOB12345678 (statut: EN ATTENTE), Job JOB87654321 (statut: VALIDE)"
}
```

#### Données invalides
```json
{
    "success": false,
    "message": "Erreur de validation",
    "errors": {
        "job_ids": ["Ce champ est requis."]
    }
}
```

## Règles métier

1. **Statut requis** : Seuls les jobs avec le statut "AFFECTE" peuvent être mis au statut "PRET"
2. **Validation en lot** : Si un seul job dans la liste n'a pas le bon statut, toute l'opération est annulée
3. **Transaction atomique** : Tous les jobs sont mis à jour dans une transaction. Si une erreur survient, aucun job n'est modifié
4. **Date de mise en prêt** : La date `pret_date` est automatiquement définie lors de la mise à jour
5. **Validation multiple** : L'API accepte plusieurs jobs en une seule requête pour optimiser les performances

## Statuts des jobs

- `EN ATTENTE` : Job créé mais pas encore validé
- `VALIDE` : Job validé mais pas encore affecté
- `AFFECTE` : Job affecté à une personne/session (peut être mis au statut PRET)
- `PRET` : Job prêt à être exécuté
- `TRANSFERT` : Job en cours de transfert
- `ENTAME` : Job commencé
- `TERMINE` : Job terminé

## Exemples d'utilisation

### cURL

```bash
curl -X POST \
  http://localhost:8000/api/inventory/jobs/ready/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "job_ids": [1, 2, 3, 4, 5]
}'
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/inventory/jobs/ready/"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}
data = {
    "job_ids": [1, 2, 3, 4, 5]
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### JavaScript (fetch)

```javascript
const url = 'http://localhost:8000/api/inventory/jobs/ready/';
const data = {
    job_ids: [1, 2, 3, 4, 5]
};

fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_TOKEN'
    },
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => console.log(data));
```

## Cas d'usage typiques

### Mise en prêt de tous les jobs affectés d'un warehouse

```python
# Récupérer tous les jobs affectés d'un warehouse
jobs_affectes = Job.objects.filter(
    warehouse_id=warehouse_id,
    status='AFFECTE'
).values_list('id', flat=True)

# Les mettre au statut PRET
response = requests.post(
    'http://localhost:8000/api/inventory/jobs/ready/',
    json={'job_ids': list(jobs_affectes)},
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

### Mise en prêt sélective

```python
# Mettre en prêt seulement certains jobs spécifiques
jobs_a_activer = [10, 15, 23, 45, 67]

response = requests.post(
    'http://localhost:8000/api/inventory/jobs/ready/',
    json={'job_ids': jobs_a_activer},
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

## Tests

Des tests unitaires sont disponibles dans `apps/inventory.tests.test_job_ready_api` pour valider le bon fonctionnement de l'API.

Pour exécuter les tests :

```bash
python manage.py test apps.inventory.tests.test_job_ready_api
``` 