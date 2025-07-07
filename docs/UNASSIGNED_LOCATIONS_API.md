# API des Emplacements Non Affectés

## Description

Cette API permet de récupérer la liste des emplacements qui ne sont pas affectés à des jobs d'inventaire, avec filtrage avancé, recherche, tri et pagination. L'API utilise django-filter pour une gestion robuste des filtres.

## Endpoint

```
GET /api/locations/unassigned/{warehouse_id}/
```

## Paramètres d'URL

| Paramètre | Type | Description | Requis |
|-----------|------|-------------|--------|
| `warehouse_id` | Integer | ID de l'entrepôt | Oui |

## Authentification

Cette API nécessite une authentification. Incluez le token d'authentification dans l'en-tête de la requête :

```
Authorization: Token <your_token>
```

## Paramètres de requête

### Filtres de base

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `reference` | String | Recherche par référence d'emplacement (contient) | `?reference=LOC001` |
| `reference__exact` | String | Recherche par référence d'emplacement (exact) | `?reference__exact=LOC001` |
| `location_reference` | String | Recherche par référence d'emplacement (contient) | `?location_reference=LOC001` |
| `description` | String | Recherche par description | `?description=Zone A` |

### Filtres de sous-zone

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `sous_zone_id` | Integer | Filtrer par ID de sous-zone | `?sous_zone_id=1` |
| `sous_zone_reference` | String | Recherche par référence de sous-zone | `?sous_zone_reference=SZ001` |
| `sous_zone_name` | String | Recherche par nom de sous-zone | `?sous_zone_name=Zone A` |
| `sous_zone_status` | String | Filtrer par statut de sous-zone | `?sous_zone_status=ACTIVE` |

### Filtres de zone

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `zone_id` | Integer | Filtrer par ID de zone | `?zone_id=1` |
| `zone_reference` | String | Recherche par référence de zone | `?zone_reference=Z001` |
| `zone_name` | String | Recherche par nom de zone | `?zone_name=Zone Principale` |
| `zone_status` | String | Filtrer par statut de zone | `?zone_status=ACTIVE` |

### Filtres d'entrepôt

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `warehouse_id` | Integer | Filtrer par ID d'entrepôt | `?warehouse_id=1` |
| `warehouse_reference` | String | Recherche par référence d'entrepôt | `?warehouse_reference=WH001` |
| `warehouse_name` | String | Recherche par nom d'entrepôt | `?warehouse_name=Central` |
| `warehouse_type` | String | Filtrer par type d'entrepôt | `?warehouse_type=PRINCIPAL` |
| `warehouse_status` | String | Filtrer par statut d'entrepôt | `?warehouse_status=ACTIVE` |

### Filtres de date

| Paramètre | Type | Description | Format | Exemple |
|-----------|------|-------------|--------|---------|
| `created_at_gte` | DateTime | Date de création >= | YYYY-MM-DD HH:MM:SS | `?created_at_gte=2024-01-01 00:00:00` |
| `created_at_lte` | DateTime | Date de création <= | YYYY-MM-DD HH:MM:SS | `?created_at_lte=2024-12-31 23:59:59` |
| `created_at_date` | Date | Date de création exacte | YYYY-MM-DD | `?created_at_date=2024-01-15` |
| `updated_at_gte` | DateTime | Date de modification >= | YYYY-MM-DD HH:MM:SS | `?updated_at_gte=2024-01-01 00:00:00` |
| `updated_at_lte` | DateTime | Date de modification <= | YYYY-MM-DD HH:MM:SS | `?updated_at_lte=2024-12-31 23:59:59` |

### Filtres de type d'emplacement

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `location_type_id` | Integer | Filtrer par ID de type d'emplacement | `?location_type_id=1` |
| `location_type_code` | String | Recherche par code de type d'emplacement | `?location_type_code=PAL` |
| `location_type_name` | String | Recherche par nom de type d'emplacement | `?location_type_name=Palette` |

### Recherche globale

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `search` | String | Recherche dans référence, description, sous-zone, zone et entrepôt | `?search=LOC001` |

### Tri

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `ordering` | String | Tri par champ (préfixer par `-` pour ordre décroissant) | `?ordering=location_reference` ou `?ordering=-created_at` |

**Champs de tri disponibles :**
- `reference` / `-reference` (référence d'emplacement)
- `location_reference` / `-location_reference` (référence d'emplacement)
- `created_at` / `-created_at` (date de création)
- `updated_at` / `-updated_at` (date de modification)
- `sous_zone__sous_zone_name` / `-sous_zone__sous_zone_name` (nom de sous-zone)
- `sous_zone__zone__zone_name` / `-sous_zone__zone__zone_name` (nom de zone)
- `sous_zone__zone__warehouse__warehouse_name` / `-sous_zone__zone__warehouse__warehouse_name` (nom d'entrepôt)

### Pagination

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `page` | Integer | Numéro de page | `?page=1` |
| `page_size` | Integer | Taille de page (max 100) | `?page_size=20` |

## Réponse

### Succès (200 OK)

```json
{
    "count": 150,
    "next": "http://localhost:8000/api/locations/unassigned/1/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "reference": "LOC001",
            "location_reference": "LOC001",
            "description": "Emplacement principal zone A",
            "sous_zone": {
                "id": 1,
                "reference": "SZ001",
                "sous_zone_name": "Sous-zone A",
                "sous_zone_status": "ACTIVE",
                "description": "Sous-zone principale"
            },
            "zone": {
                "id": 1,
                "reference": "Z001",
                "zone_name": "Zone Principale",
                "zone_status": "ACTIVE",
                "description": "Zone principale de l'entrepôt"
            },
            "warehouse": {
                "id": 1,
                "reference": "WH001",
                "warehouse_name": "Entrepôt Central",
                "warehouse_type": "PRINCIPAL",
                "status": "ACTIVE"
            }
        },
        {
            "id": 2,
            "reference": "LOC002",
            "location_reference": "LOC002",
            "description": "Emplacement secondaire zone B",
            "sous_zone": {
                "id": 2,
                "reference": "SZ002",
                "sous_zone_name": "Sous-zone B",
                "sous_zone_status": "ACTIVE",
                "description": "Sous-zone secondaire"
            },
            "zone": {
                "id": 1,
                "reference": "Z001",
                "zone_name": "Zone Principale",
                "zone_status": "ACTIVE",
                "description": "Zone principale de l'entrepôt"
            },
            "warehouse": {
                "id": 1,
                "reference": "WH001",
                "warehouse_name": "Entrepôt Central",
                "warehouse_type": "PRINCIPAL",
                "status": "ACTIVE"
            }
        }
    ],
    "message": "Liste des emplacements non affectés récupérée avec succès"
}
```

### Erreur - Entrepôt non trouvé (404 Not Found)

```json
{
    "detail": "Not found."
}
```

### Erreur - Erreur serveur (500 Internal Server Error)

```json
{
    "success": false,
    "message": "Erreur interne : Une erreur inattendue est survenue"
}
```

## Exemples d'utilisation

### Exemple 1 : Récupération simple avec pagination

```bash
curl -X GET \
  "http://localhost:8000/api/locations/unassigned/1/?page=1&page_size=10" \
  -H "Authorization: Token your_token_here"
```

### Exemple 2 : Filtrage par référence d'emplacement

```bash
curl -X GET \
  "http://localhost:8000/api/locations/unassigned/1/?location_reference=LOC001" \
  -H "Authorization: Token your_token_here"
```

### Exemple 3 : Filtrage par sous-zone

```bash
curl -X GET \
  "http://localhost:8000/api/locations/unassigned/1/?sous_zone_name=Zone A" \
  -H "Authorization: Token your_token_here"
```

### Exemple 4 : Filtrage par date de création

```bash
curl -X GET \
  "http://localhost:8000/api/locations/unassigned/1/?created_at_gte=2024-01-01 00:00:00&created_at_lte=2024-01-31 23:59:59" \
  -H "Authorization: Token your_token_here"
```

### Exemple 5 : Recherche globale

```bash
curl -X GET \
  "http://localhost:8000/api/locations/unassigned/1/?search=LOC001" \
  -H "Authorization: Token your_token_here"
```

### Exemple 6 : Tri par nom de zone

```bash
curl -X GET \
  "http://localhost:8000/api/locations/unassigned/1/?ordering=sous_zone__zone__zone_name" \
  -H "Authorization: Token your_token_here"
```

### Exemple 7 : Combinaison de filtres

```bash
curl -X GET \
  "http://localhost:8000/api/locations/unassigned/1/?sous_zone_id=1&created_at_gte=2024-01-01 00:00:00&ordering=location_reference&page_size=20" \
  -H "Authorization: Token your_token_here"
```

### Exemple 8 : Filtrage par type d'emplacement

```bash
curl -X GET \
  "http://localhost:8000/api/locations/unassigned/1/?location_type_name=Palette" \
  -H "Authorization: Token your_token_here"
```

## Codes d'erreur HTTP

| Code | Description |
|------|-------------|
| 200 | Succès avec données |
| 400 | Erreur de validation des paramètres |
| 401 | Non authentifié |
| 403 | Non autorisé |
| 404 | Entrepôt non trouvé |
| 500 | Erreur interne du serveur |

## Notes importantes

1. **Filtrage automatique** : Seuls les emplacements actifs et non affectés à des jobs sont retournés.

2. **Relations préchargées** : Les relations avec la sous-zone, zone, entrepôt et type d'emplacement sont préchargées pour optimiser les performances.

3. **Exclusion des jobs** : Les emplacements déjà affectés à des jobs d'inventaire sont automatiquement exclus.

4. **Recherche insensible à la casse** : La recherche globale est insensible à la casse.

5. **Pagination par défaut** : 10 éléments par page, maximum 100.

6. **Tri par défaut** : Par référence d'emplacement croissante.

7. **Filtrage par entrepôt** : Si un `warehouse_id` est spécifié dans l'URL, seuls les emplacements de cet entrepôt sont retournés.

## Endpoints liés

- `POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/` - Créer des jobs avec des emplacements
- `GET /api/warehouse/{warehouse_id}/pending-jobs/` - Jobs en attente d'un entrepôt
- `GET /api/warehouse/{warehouse_id}/jobs/` - Tous les jobs d'un entrepôt
- `GET /api/locations/{location_id}/` - Détail d'un emplacement 