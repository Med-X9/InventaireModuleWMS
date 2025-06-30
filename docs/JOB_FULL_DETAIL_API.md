# API Jobs Full Detail - Documentation

## Vue d'ensemble

L'API `JobFullDetailListView` permet de récupérer une liste complète des jobs avec tous leurs détails associés : emplacements, sous-zones, zones, assignements, sessions, ressources et statuts. Cette API inclut la pagination et des filtres multi-champs pour une recherche avancée.

## Endpoint

```
GET /api/inventory/jobs/full-list/
```

## Paramètres de requête

### Pagination
- `page` (int, optionnel) : Numéro de page (défaut: 1)
- `page_size` (int, optionnel) : Nombre d'éléments par page (défaut: 10, max: 100)

### Filtres sur le Job
- `reference` (string, optionnel) : Filtre par référence du job (recherche insensible à la casse)
- `status` (string, optionnel) : Filtre par statut du job (ex: "VALIDE", "EN ATTENTE", "TERMINE")

### Filtres sur les Emplacements
- `emplacement_reference` (string, optionnel) : Filtre par référence de l'emplacement
- `sous_zone` (string, optionnel) : Filtre par nom de la sous-zone
- `zone` (string, optionnel) : Filtre par nom de la zone

### Filtres sur les Assignements
- `assignment_status` (string, optionnel) : Filtre par statut de l'assignement (ex: "AFFECTE", "PRET", "EN ATTENTE")
- `counting_order` (int, optionnel) : Filtre par ordre du comptage (1, 2, 3)

### Filtres sur les Sessions
- `session_username` (string, optionnel) : Filtre par nom d'utilisateur de la session

### Filtres sur les Ressources
- `ressource_reference` (string, optionnel) : Filtre par référence de la ressource

### Tri
- `ordering` (string, optionnel) : Tri par champ (ex: "created_at", "-created_at", "status", "-reference")

### Recherche globale
- `search` (string, optionnel) : Recherche globale dans la référence du job

## Exemples d'utilisation

### Récupération basique avec pagination
```http
GET /api/inventory/jobs/full-list/?page=1&page_size=20
```

### Filtrage par statut de job et d'assignement
```http
GET /api/inventory/jobs/full-list/?status=VALIDE&assignment_status=PRET&page=1&page_size=20
```

### Filtrage par zone et sous-zone
```http
GET /api/inventory/jobs/full-list/?zone=Johnson-Lopez&sous_zone=SousZone%20A&page=1&page_size=20
```

### Filtrage par session et ordre de comptage
```http
GET /api/inventory/jobs/full-list/?session_username=pda1&counting_order=1&page=1&page_size=20
```

### Recherche globale
```http
GET /api/inventory/jobs/full-list/?search=JOB-001&page=1&page_size=20
```

### Tri par date de création décroissante
```http
GET /api/inventory/jobs/full-list/?ordering=-created_at&page=1&page_size=20
```

## Structure de la réponse

### Réponse de succès (200 OK)

```json
{
  "count": 150,
  "next": "http://127.0.0.1:8000/api/inventory/jobs/full-list/?page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": 1,
      "reference": "JOB-001",
      "status": "VALIDE",
      "emplacements": [
        {
          "id": 10,
          "reference": "EMPL-001",
          "sous_zone": {
            "id": 5,
            "sous_zone_name": "SousZone A",
            "zone_name": "Zone 1"
          },
          "zone": {
            "id": 2,
            "zone_name": "Zone 1",
            "warehouse_name": "Entrepôt Principal"
          }
        },
        {
          "id": 11,
          "reference": "EMPL-002",
          "sous_zone": {
            "id": 6,
            "sous_zone_name": "SousZone B",
            "zone_name": "Zone 1"
          },
          "zone": {
            "id": 2,
            "zone_name": "Zone 1",
            "warehouse_name": "Entrepôt Principal"
          }
        }
      ],
      "assignments": [
        {
          "counting_order": 1,
          "status": "AFFECTE",
          "session": {
            "id": 7,
            "username": "pda1"
          }
        },
        {
          "counting_order": 2,
          "status": "PRET",
          "session": {
            "id": 8,
            "username": "pda2"
          }
        }
      ],
      "ressources": [
        {
          "id": 3,
          "reference": "RES-001",
          "quantity": 2
        },
        {
          "id": 4,
          "reference": "RES-002",
          "quantity": 1
        }
      ]
    }
  ]
}
```

### Champs de la réponse

#### Job
- `id` (int) : Identifiant unique du job
- `reference` (string) : Référence du job
- `status` (string) : Statut du job (EN ATTENTE, VALIDE, TERMINE)

#### Emplacements
- `id` (int) : Identifiant de l'emplacement
- `reference` (string) : Référence de l'emplacement
- `sous_zone` (object) : Informations sur la sous-zone
  - `id` (int) : Identifiant de la sous-zone
  - `sous_zone_name` (string) : Nom de la sous-zone
  - `zone_name` (string) : Nom de la zone parente
- `zone` (object) : Informations sur la zone
  - `id` (int) : Identifiant de la zone
  - `zone_name` (string) : Nom de la zone
  - `warehouse_name` (string) : Nom de l'entrepôt

#### Assignements
- `counting_order` (int) : Ordre du comptage (1, 2, 3)
- `status` (string) : Statut de l'assignement (EN ATTENTE, AFFECTE, PRET, TRANSFERT, ENTAME, TERMINE)
- `session` (object, nullable) : Informations sur la session
  - `id` (int) : Identifiant de la session
  - `username` (string) : Nom d'utilisateur de la session

#### Ressources
- `id` (int) : Identifiant de la ressource
- `reference` (string) : Référence de la ressource
- `quantity` (int, nullable) : Quantité de la ressource

## Codes d'erreur

### 400 Bad Request
```json
{
  "detail": "Invalid page number"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Notes importantes

1. **Filtres combinés** : Les filtres peuvent être combinés pour affiner la recherche
2. **Pagination** : L'API utilise la pagination par défaut avec 10 éléments par page
3. **Recherche insensible à la casse** : Tous les filtres textuels sont insensibles à la casse
4. **Relations** : L'API retourne les jobs qui correspondent à au moins un des critères de filtre sur les relations
5. **Performance** : L'API utilise `select_related` pour optimiser les requêtes de base de données

## Cas d'usage typiques

1. **Affichage d'un tableau de jobs** avec pagination
2. **Recherche de jobs par zone/sous-zone** pour la planification
3. **Filtrage par statut d'assignement** pour le suivi des comptages
4. **Recherche par session** pour identifier les PDA utilisées
5. **Filtrage par ressources** pour la gestion des équipements

## Exemple Postman

### Configuration
- **Méthode** : GET
- **URL** : `http://127.0.0.1:8000/api/inventory/jobs/full-list/`
- **Headers** : 
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (si authentification requise)

### Paramètres d'exemple
```
page: 1
page_size: 20
status: VALIDE
assignment_status: PRET
zone: Johnson-Lopez
ordering: -created_at
``` 