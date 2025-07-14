# API des Jobs en Attente

## Description

Cette API permet de récupérer la liste des jobs en attente pour un entrepôt spécifique avec filtrage avancé, recherche, tri et pagination. L'API utilise django-filter pour une gestion robuste des filtres.

## Endpoint

```
GET /api/warehouse/{warehouse_id}/pending-jobs/
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
| `reference` | String | Recherche par référence de job (contient) | `?reference=JOB001` |
| `reference__exact` | String | Recherche par référence de job (exact) | `?reference__exact=JOB001` |
| `reference__icontains` | String | Recherche par référence de job (insensible à la casse) | `?reference__icontains=job` |

### Filtres d'inventaire

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `inventory_id` | Integer | Filtrer par ID d'inventaire | `?inventory_id=1` |
| `inventory_reference` | String | Recherche par référence d'inventaire | `?inventory_reference=INV001` |
| `inventory_reference__exact` | String | Recherche exacte par référence d'inventaire | `?inventory_reference__exact=INV001` |
| `inventory_label` | String | Recherche par label d'inventaire | `?inventory_label=Inventaire` |

### Filtres d'entrepôt

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `warehouse_id` | Integer | Filtrer par ID d'entrepôt | `?warehouse_id=2` |
| `warehouse_reference` | String | Recherche par référence d'entrepôt | `?warehouse_reference=WH001` |
| `warehouse_name` | String | Recherche par nom d'entrepôt | `?warehouse_name=Central` |

### Filtres de date

| Paramètre | Type | Description | Format | Exemple |
|-----------|------|-------------|--------|---------|
| `created_at_gte` | DateTime | Date de création >= | YYYY-MM-DD HH:MM:SS | `?created_at_gte=2024-01-01 00:00:00` |
| `created_at_lte` | DateTime | Date de création <= | YYYY-MM-DD HH:MM:SS | `?created_at_lte=2024-12-31 23:59:59` |
| `created_at_date` | Date | Date de création exacte | YYYY-MM-DD | `?created_at_date=2024-01-15` |
| `created_at__exact` | DateTime | Date et heure exactes | YYYY-MM-DD HH:MM:SS | `?created_at__exact=2024-01-15 10:30:00` |

### Filtres de comptage

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `emplacements_count_min` | Integer | Nombre minimum d'emplacements | `?emplacements_count_min=5` |
| `emplacements_count_max` | Integer | Nombre maximum d'emplacements | `?emplacements_count_max=20` |
| `assignments_count_min` | Integer | Nombre minimum d'assignations | `?assignments_count_min=2` |
| `assignments_count_max` | Integer | Nombre maximum d'assignations | `?assignments_count_max=5` |

### Recherche globale

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `search` | String | Recherche dans référence, inventaire et entrepôt | `?search=JOB001` |

### Tri

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `ordering` | String | Tri par champ (préfixer par `-` pour ordre décroissant) | `?ordering=created_at` ou `?ordering=-reference` |

**Champs de tri disponibles :**
- `created_at` / `-created_at` (date de création)
- `reference` / `-reference` (référence du job)
- `inventory__reference` / `-inventory__reference` (référence de l'inventaire)
- `warehouse__warehouse_name` / `-warehouse__warehouse_name` (nom de l'entrepôt)

### Pagination

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `page` | Integer | Numéro de page | `?page=1` |
| `page_size` | Integer | Taille de page (max 100) | `?page_size=20` |

## Réponse

### Succès (200 OK)

```json
{
    "count": 25,
    "next": "http://localhost:8000/api/warehouse/1/pending-jobs/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "reference": "JOB001",
            "status": "EN ATTENTE",
            "created_at": "2024-01-15T10:30:00Z",
            "inventory_id": 1,
            "inventory_reference": "INV001",
            "inventory_label": "Inventaire Q1 2024",
            "warehouse_id": 1,
            "warehouse_reference": "WH001",
            "warehouse_name": "Entrepôt Central",
            "emplacements_count": 15,
            "assignments_count": 2
        },
        {
            "id": 2,
            "reference": "JOB002",
            "status": "EN ATTENTE",
            "created_at": "2024-01-15T09:15:00Z",
            "inventory_id": 1,
            "inventory_reference": "INV001",
            "inventory_label": "Inventaire Q1 2024",
            "warehouse_id": 1,
            "warehouse_reference": "WH001",
            "warehouse_name": "Entrepôt Central",
            "emplacements_count": 8,
            "assignments_count": 2
        }
    ],
    "message": "Liste des jobs en attente récupérée avec succès"
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
  "http://localhost:8000/api/warehouse/1/pending-jobs/?page=1&page_size=10" \
  -H "Authorization: Token your_token_here"
```

### Exemple 2 : Filtrage par référence d'inventaire

```bash
curl -X GET \
  "http://localhost:8000/api/warehouse/1/pending-jobs/?inventory_reference=INV001" \
  -H "Authorization: Token your_token_here"
```

### Exemple 3 : Filtrage par date de création

```bash
curl -X GET \
  "http://localhost:8000/api/warehouse/1/pending-jobs/?created_at_gte=2024-01-01 00:00:00&created_at_lte=2024-01-31 23:59:59" \
  -H "Authorization: Token your_token_here"
```

### Exemple 4 : Recherche globale

```bash
curl -X GET \
  "http://localhost:8000/api/warehouse/1/pending-jobs/?search=JOB001" \
  -H "Authorization: Token your_token_here"
```

### Exemple 5 : Tri par date de création (plus récent en premier)

```bash
curl -X GET \
  "http://localhost:8000/api/warehouse/1/pending-jobs/?ordering=-created_at" \
  -H "Authorization: Token your_token_here"
```

### Exemple 6 : Filtrage par nombre d'emplacements

```bash
curl -X GET \
  "http://localhost:8000/api/warehouse/1/pending-jobs/?emplacements_count_min=10&emplacements_count_max=50" \
  -H "Authorization: Token your_token_here"
```

### Exemple 7 : Combinaison de filtres

```bash
curl -X GET \
  "http://localhost:8000/api/warehouse/1/pending-jobs/?inventory_id=1&created_at_gte=2024-01-01 00:00:00&ordering=-created_at&page_size=20" \
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

1. **Filtrage automatique** : Seuls les jobs avec le statut "EN ATTENTE" sont retournés.

2. **Relations préchargées** : Les relations avec l'inventaire et l'entrepôt sont préchargées pour optimiser les performances.

3. **Comptage en temps réel** : Les compteurs d'emplacements et d'assignations sont calculés en temps réel.

4. **Recherche insensible à la casse** : La recherche globale est insensible à la casse.

5. **Pagination par défaut** : 10 éléments par page, maximum 100.

6. **Tri par défaut** : Par date de création décroissante (plus récent en premier).

## Endpoints liés

- `POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/` - Créer des jobs
- `GET /api/warehouse/{warehouse_id}/jobs/` - Tous les jobs d'un entrepôt
- `POST /api/jobs/validate/` - Valider des jobs
- `POST /api/jobs/delete/` - Supprimer des jobs 