# API de Statistiques des Warehouses d'un Inventaire

## Description

Cette API permet de récupérer les statistiques des warehouses associés à un inventaire spécifique, incluant le nombre de jobs et d'équipes (sessions mobiles) pour chaque warehouse.

## Endpoint

```
GET /api/inventory/{inventory_id}/warehouse-stats/
```

## Paramètres

| Paramètre | Type | Description | Requis |
|-----------|------|-------------|--------|
| `inventory_id` | Integer | ID de l'inventaire | Oui |

## Authentification

Cette API nécessite une authentification. Incluez le token d'authentification dans l'en-tête de la requête :

```
Authorization: Token <your_token>
```

## Réponse

### Succès (200 OK)

```json
{
    "status": "success",
    "message": "Statistiques des warehouses récupérées avec succès",
    "inventory_id": 1,
    "warehouses_count": 2,
    "data": [
        {
            "warehouse_id": 1,
            "warehouse_reference": "WH001",
            "warehouse_name": "Entrepôt Central",
            "jobs_count": 5,
            "teams_count": 3
        },
        {
            "warehouse_id": 2,
            "warehouse_reference": "WH002",
            "warehouse_name": "Entrepôt Réception",
            "jobs_count": 3,
            "teams_count": 2
        }
    ]
}
```

### Erreur - Inventaire non trouvé (404 Not Found)

```json
{
    "status": "error",
    "message": "Inventaire non trouvé",
    "error": "L'inventaire avec l'ID 999 n'existe pas."
}
```

### Erreur - Erreur de validation (400 Bad Request)

```json
{
    "status": "error",
    "message": "Erreur de validation",
    "error": "Erreur lors de la récupération des statistiques: ..."
}
```

### Erreur - Erreur serveur (500 Internal Server Error)

```json
{
    "status": "error",
    "message": "Erreur lors de la récupération des statistiques des warehouses",
    "error": "Erreur interne du serveur"
}
```

## Description des champs

### Réponse principale

| Champ | Type | Description |
|-------|------|-------------|
| `status` | String | Statut de la réponse ("success" ou "error") |
| `message` | String | Message descriptif |
| `inventory_id` | Integer | ID de l'inventaire demandé |
| `warehouses_count` | Integer | Nombre total de warehouses associés à l'inventaire |
| `data` | Array | Liste des statistiques par warehouse |

### Données par warehouse

| Champ | Type | Description |
|-------|------|-------------|
| `warehouse_id` | Integer | ID du warehouse |
| `warehouse_reference` | String | Référence du warehouse |
| `warehouse_name` | String | Nom du warehouse |
| `jobs_count` | Integer | Nombre de jobs associés à ce warehouse et cet inventaire |
| `teams_count` | Integer | Nombre d'équipes (sessions mobiles uniques) affectées à ce warehouse |

## Logique métier

### Calcul des statistiques

1. **Jobs count** : Nombre de jobs associés au warehouse et à l'inventaire spécifiés
2. **Teams count** : Nombre d'utilisateurs mobiles uniques ayant des affectations pour ce warehouse

### Filtres appliqués

- Seuls les utilisateurs de type "Mobile" sont comptés comme équipes
- Les affectations sans session ne sont pas comptées dans le nombre d'équipes

## Exemples d'utilisation

### Exemple avec cURL

```bash
curl -X GET \
  "http://localhost:8000/api/inventory/1/warehouse-stats/" \
  -H "Authorization: Token your_token_here" \
  -H "Content-Type: application/json"
```

### Exemple avec Python requests

```python
import requests

url = "http://localhost:8000/api/inventory/1/warehouse-stats/"
headers = {
    "Authorization": "Token your_token_here",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"Nombre de warehouses: {data['warehouses_count']}")
    
    for warehouse in data['data']:
        print(f"Warehouse {warehouse['warehouse_name']}:")
        print(f"  - Jobs: {warehouse['jobs_count']}")
        print(f"  - Équipes: {warehouse['teams_count']}")
else:
    print(f"Erreur: {response.status_code}")
    print(response.json())
```

### Exemple avec JavaScript fetch

```javascript
const url = 'http://localhost:8000/api/inventory/1/warehouse-stats/';
const headers = {
    'Authorization': 'Token your_token_here',
    'Content-Type': 'application/json'
};

fetch(url, { headers })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(`Nombre de warehouses: ${data.warehouses_count}`);
            
            data.data.forEach(warehouse => {
                console.log(`Warehouse ${warehouse.warehouse_name}:`);
                console.log(`  - Jobs: ${warehouse.jobs_count}`);
                console.log(`  - Équipes: ${warehouse.teams_count}`);
            });
        } else {
            console.error('Erreur:', data.message);
        }
    })
    .catch(error => console.error('Erreur réseau:', error));
```

## Cas d'usage

Cette API est particulièrement utile pour :

1. **Tableaux de bord** : Afficher un aperçu des ressources par warehouse
2. **Planification** : Évaluer la charge de travail par entrepôt
3. **Reporting** : Générer des rapports de performance par warehouse
4. **Monitoring** : Suivre l'activité des équipes par entrepôt

## Notes importantes

- L'API ne retourne que les warehouses associés à l'inventaire via le modèle `Setting`
- Les warehouses sans jobs retourneront des compteurs à 0
- Les utilisateurs de type "Web" ne sont pas comptés comme équipes
- L'API est optimisée pour les performances avec des requêtes SQL efficaces 