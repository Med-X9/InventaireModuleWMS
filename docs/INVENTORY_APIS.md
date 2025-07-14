# Documentation des APIs inventory (web/api)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET     | /web/api/inventory/ | Liste des inventaires |
| POST    | /web/api/inventory/create/ | Créer un inventaire |
| GET     | /web/api/inventory/<pk>/edit/ | Détail d'un inventaire (édition) |
| POST    | /web/api/inventory/<pk>/update/ | Mettre à jour un inventaire |
| POST    | /web/api/inventory/<pk>/delete/ | Supprimer un inventaire |
| POST    | /web/api/inventory/<pk>/launch/ | Lancer un inventaire |
| POST    | /web/api/inventory/<pk>/cancel/ | Annuler un inventaire |
| GET     | /web/api/inventory/<pk>/detail/ | Détail d'équipe d'inventaire |
| GET     | /web/api/inventory/<int:inventory_id>/warehouse-stats/ | Statistiques des entrepôts d'un inventaire |
| GET     | /web/api/inventory/planning/<int:inventory_id>/warehouses/ | Entrepôts d'un inventaire |
| POST    | /web/api/inventory/planning/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/create/ | Créer des jobs pour un entrepôt |
| GET     | /web/api/warehouse/<int:warehouse_id>/pending-jobs/ | Jobs en attente d'un entrepôt |
| GET     | /web/api/warehouse/<int:warehouse_id>/jobs/ | Tous les jobs d'un entrepôt |
| POST    | /web/api/jobs/validate/ | Valider des jobs |
| POST    | /web/api/jobs/delete/ | Supprimer définitivement un job |
| POST    | /web/api/job/<int:job_id>/remove-emplacements/ | Supprimer des emplacements d'un job |
| POST    | /web/api/job/<int:job_id>/add-emplacements/ | Ajouter des emplacements à un job |
| GET     | /web/api/jobs/list/ | Lister tous les jobs avec détails |
| POST    | /web/api/inventory/<int:inventory_id>/assign-jobs/ | Affecter des jobs à un inventaire |
| GET     | /web/api/assignment-rules/ | Règles d'affectation |
| GET     | /web/api/session/<int:session_id>/assignments/ | Assignations par session |
| POST    | /web/api/jobs/assign-resources/ | Affecter des ressources à des jobs |
| GET     | /web/api/job/<int:job_id>/resources/ | Récupérer les ressources d'un job |
| POST    | /web/api/job/<int:job_id>/remove-resources/ | Retirer des ressources d'un job |
| POST    | /web/api/jobs/ready/ | Marquer un job comme prêt |
| GET     | /web/api/jobs/full-list/ | Liste complète des jobs |
| GET     | /web/api/jobs/pending/ | Lister les jobs en attente |
| POST    | /web/api/jobs/reset-assignments/ | Remettre les assignations de jobs en attente |

## GET /web/api/inventory/
- **Description** : Liste des inventaires
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
[
  {
    "id": 1,
    "name": "Inventaire Juillet",
    "date": "2024-07-01",
    "warehouses": [1, 2]
  }
]
```
- **Statuts possibles** : 200

## POST /web/api/inventory/create/
- **Description** : Créer un inventaire
- **Méthode** : POST
- **Payload attendu** :
```json
{
  "name": "Inventaire Juillet",
  "date": "2024-07-01",
  "warehouses": [1, 2]
}
```
- **Réponse succès (201)** :
```json
{
  "id": 5,
  "name": "Inventaire Juillet",
  "date": "2024-07-01",
  "warehouses": [1, 2]
}
```
- **Réponse erreur (400)** :
```json
{
  "error": "Le champ 'name' est obligatoire."
}
```
- **Statuts possibles** : 201, 400

## GET /web/api/inventory/<pk>/edit/
- **Description** : Détail d'un inventaire (édition)
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
{
  "id": 1,
  "name": "Inventaire Juillet",
  "date": "2024-07-01",
  "warehouses": [1, 2]
}
```
- **Réponse erreur (404)** :
```json
{
  "error": "Inventaire non trouvé."
}
```
- **Statuts possibles** : 200, 404

## POST /web/api/inventory/<pk>/update/
- **Description** : Mettre à jour un inventaire
- **Méthode** : POST
- **Payload attendu** :
```json
{
  "name": "Inventaire Août",
  "date": "2024-08-01"
}
```
- **Réponse succès (200)** :
```json
{
  "id": 1,
  "name": "Inventaire Août",
  "date": "2024-08-01",
  "warehouses": [1, 2]
}
```
- **Réponse erreur (400)** :
```json
{
  "error": "Format de date invalide."
}
```
- **Statuts possibles** : 200, 400

## GET /web/api/inventory/<int:inventory_id>/warehouse-stats/
- **Description** : Statistiques des entrepôts d'un inventaire
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
{
  "inventory_id": 1,
  "warehouses": [
    {"id": 1, "name": "Entrepôt A", "stats": {"nb_jobs": 10, "nb_locations": 50}},
    {"id": 2, "name": "Entrepôt B", "stats": {"nb_jobs": 5, "nb_locations": 20}}
  ]
}
```
- **Statuts possibles** : 200

## POST /web/api/jobs/validate/
- **Description** : Valider des jobs
- **Méthode** : POST
- **Payload attendu** :
```json
{
  "job_ids": [1, 2, 3]
}
```
- **Réponse succès (200)** :
```json
{
  "success": true,
  "validated_jobs": [1, 2, 3]
}
```
- **Réponse erreur (400)** :
```json
{
  "error": "Aucun job à valider."
}
```
- **Statuts possibles** : 200, 400

**Remarque :**
- Adapter les exemples selon la structure réelle des serializers et des vues.
- Pour chaque endpoint POST/PUT, ajouter un exemple de payload.
- Pour plus de détails, consulter la documentation Swagger intégrée (`/swagger/`). 