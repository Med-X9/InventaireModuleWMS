# API de Clôture de Job avec Assignment

## Description

Cette API permet de clôturer un job avec son assignment en vérifiant que tous les emplacements (JobDetails) sont terminés. L'API vérifie automatiquement que tous les emplacements ont le statut 'TERMINE' avant de clôturer le job et l'assignment.

## Endpoint

```
POST /api/mobile/job/{job_id}/close/{assignment_id}/
```

## Authentification

Cette API nécessite une authentification. Incluez le token d'authentification dans l'en-tête de la requête :

```
Authorization: Bearer <your_jwt_token>
```

Note : L'API ne vérifie pas que l'utilisateur authentifié est affecté à l'assignment. Toute personne authentifiée peut clôturer un job à condition que tous les emplacements soient terminés.

## Paramètres d'URL

| Paramètre | Type | Description | Requis |
|-----------|------|-------------|--------|
| `job_id` | Integer | ID du job à clôturer | Oui |
| `assignment_id` | Integer | ID de l'assignment associé au job | Oui |

## Corps de la requête

Cette API ne nécessite pas de corps de requête.

## Vérifications effectuées

L'API effectue les vérifications suivantes avant de clôturer le job :

1. **Vérification de l'existence du job** : Vérifie que le job existe dans la base de données
2. **Vérification de l'existence de l'assignment** : Vérifie que l'assignment existe dans la base de données
3. **Vérification de la liaison** : Vérifie que l'assignment appartient bien au job
4. **Vérification des emplacements** : Vérifie que tous les JobDetails du job ont le statut 'TERMINE'

## Réponse

### Succès (200 OK)

Si toutes les vérifications sont réussies, le job et l'assignment sont clôturés :

```json
{
    "success": true,
    "message": "Job JOB-123 et assignment ASS-456 clôturés avec succès",
    "job": {
        "id": 123,
        "reference": "JOB-123",
        "status": "TERMINE",
        "termine_date": "2024-01-15T10:30:00Z",
        "total_emplacements": 5
    },
    "assignment": {
        "id": 456,
        "reference": "ASS-456",
        "status": "TERMINE"
    }
}
```

### Erreur - Job non trouvé (404 Not Found)

```json
{
    "success": false,
    "error": "Job avec l'ID 123 non trouvé"
}
```

### Erreur - Assignment non trouvé (404 Not Found)

```json
{
    "success": false,
    "error": "Assignment avec l'ID 456 non trouvé"
}
```

### Erreur - Emplacements non terminés (400 Bad Request)

```json
{
    "success": false,
    "error": "Le job ne peut pas être clôturé car certains emplacements ne sont pas terminés. Emplacement JBD-789 (ID: 789) a le statut: EN ATTENTE"
}
```

### Erreur - Assignment n'appartient pas au job (400 Bad Request)

```json
{
    "success": false,
    "error": "L'assignment 456 n'appartient pas au job 123"
}
```

### Erreur - Erreur serveur (500 Internal Server Error)

```json
{
    "success": false,
    "error": "Erreur interne: <message d'erreur>"
}
```

## Processus de clôture

1. **Vérification des emplacements** : L'API vérifie que tous les JobDetails ont le statut 'TERMINE'
2. **Clôture de l'assignment** : Le statut de l'assignment est mis à jour à 'TERMINE'
3. **Clôture du job** : Le statut du job est mis à jour à 'TERMINE' et la date de terminaison est enregistrée

## Exemples d'utilisation

### Exemple avec cURL

```bash
curl -X POST \
  'http://localhost:8000/api/mobile/job/123/close/456/' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json'
```

### Exemple avec Python (requests)

```python
import requests

url = "http://localhost:8000/api/mobile/job/123/close/456/"
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"Job clôturé: {data['job']['reference']}")
else:
    print(f"Erreur: {response.json()}")
```

### Exemple avec JavaScript (fetch)

```javascript
const response = await fetch('http://localhost:8000/api/mobile/job/123/close/456/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  }
});

const data = await response.json();

if (response.ok) {
  console.log('Job clôturé:', data.job.reference);
} else {
  console.error('Erreur:', data.error);
}
```

## Notes importantes

1. **Authentification requise** : Cette API nécessite une authentification JWT valide
2. **Pas de vérification d'utilisateur** : L'API ne vérifie pas que l'utilisateur authentifié est affecté à l'assignment
3. **Vérification des emplacements** : Tous les emplacements doivent être terminés avant de pouvoir clôturer le job
4. **Transaction atomique** : La clôture du job et de l'assignment est effectuée dans une transaction atomique pour garantir la cohérence des données
5. **Une seule clôture** : Une fois qu'un job est clôturé, il ne peut plus être modifié
6. **Emplacements à vérifier** : Tous les JobDetails associés au job sont vérifiés, qu'ils aient ou non un counting associé

## Statuts des JobDetails

Le système vérifie que tous les JobDetails ont le statut 'TERMINE'. Les statuts possibles sont :

- `EN ATTENTE` : L'emplacement n'a pas encore été traité
- `TERMINE` : L'emplacement a été complété

## Logique métier

L'API de clôture garantit que :

1. L'assignment appartient bien au job spécifié
2. Tous les emplacements sont terminés avant la clôture
3. Le job et l'assignment sont mis à jour de manière atomique

Cette approche garantit l'intégrité des données et prévient les erreurs de clôture prématurée.
