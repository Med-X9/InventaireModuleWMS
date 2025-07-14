# API d'Affectation des Ressources aux Jobs

Cette API permet de gérer l'affectation des ressources (scanners, terminaux, imprimantes, etc.) aux jobs d'inventaire.

## Architecture

L'API suit une architecture en couches séparées :

- **Interface** : Définit les contrats pour les services et repositories
- **Repository** : Gère l'accès aux données
- **Service** : Contient la logique métier
- **Vue** : Gère les requêtes HTTP et les réponses
- **Serializer** : Valide et sérialise les données

## Endpoints

### 1. Affecter les mêmes ressources à plusieurs jobs

**POST** `/api/inventory/jobs/assign-resources/`

Affecte les mêmes ressources à plusieurs jobs en une seule requête.

#### Corps de la requête
```json
{
  "job_ids": [123, 124, 125],
  "resource_assignments": [
    {
      "resource_id": 1,
      "quantity": 2
    },
    {
      "resource_id": 3,
      "quantity": 1
    }
  ]
}
```

#### Réponse de succès (200)
```json
{
  "success": true,
  "message": "Traitement terminé pour 3 jobs",
  "total_jobs_processed": 3,
  "total_assignments_created": 6,
  "total_assignments_updated": 0,
  "job_results": [
    {
      "success": true,
      "message": "2 affectations créées, 0 affectations mises à jour",
      "assignments_created": 2,
      "assignments_updated": 0,
      "total_assignments": 2,
      "job_id": 123,
      "job_reference": "JOBABC123"
    },
    {
      "success": true,
      "message": "2 affectations créées, 0 affectations mises à jour",
      "assignments_created": 2,
      "assignments_updated": 0,
      "total_assignments": 2,
      "job_id": 124,
      "job_reference": "JOBABC124"
    },
    {
      "success": true,
      "message": "2 affectations créées, 0 affectations mises à jour",
      "assignments_created": 2,
      "assignments_updated": 0,
      "total_assignments": 2,
      "job_id": 125,
      "job_reference": "JOBABC125"
    }
  ]
}
```

#### Codes d'erreur
- **400** : Données invalides
- **422** : Violation de règle métier (job en statut EN ATTENTE)

### 2. Récupérer les ressources d'un job

**GET** `/api/inventory/job/{job_id}/resources/`

Récupère toutes les ressources affectées à un job.

#### Paramètres de chemin
- `job_id` (integer, requis) : ID du job

#### Réponse de succès (200)
```json
[
  {
    "id": 1,
    "reference": "JDRABC123",
    "resource_id": 1,
    "resource_name": "Scanner",
    "resource_code": "SCAN001",
    "quantity": 2,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  {
    "id": 2,
    "reference": "JDRDEF456",
    "resource_id": 3,
    "resource_name": "Terminal",
    "resource_code": "TERM001",
    "quantity": 1,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
]
```

#### Codes d'erreur
- **404** : Job non trouvé

### 3. Supprimer des ressources d'un job

**DELETE** `/api/inventory/job/{job_id}/remove-resources/`

Supprime une ou plusieurs ressources d'un job.

#### Paramètres de chemin
- `job_id` (integer, requis) : ID du job

#### Corps de la requête
```json
{
  "resource_ids": [1, 3, 5]
}
```

#### Réponse de succès (200)
```json
{
  "success": true,
  "message": "2 affectations de ressources supprimées",
  "deleted_count": 2,
  "job_id": 123,
  "job_reference": "JOBABC123"
}
```

#### Codes d'erreur
- **400** : Données invalides
- **404** : Job non trouvé
- **422** : Violation de règle métier (job en statut EN ATTENTE)

## Règles métier

### Validation des données

1. **Jobs obligatoires** : La liste des IDs de jobs doit être fournie
2. **Ressources obligatoires** : La liste des ressources à affecter doit être fournie
3. **Quantité positive** : La quantité doit être un entier positif (défaut: 1)
4. **Ressource existante** : La ressource doit exister en base de données
5. **Job existant** : Le job doit exister en base de données

### Règles d'affectation

1. **Statut du job** : Les ressources ne peuvent être affectées qu'aux jobs qui ne sont pas en statut "EN ATTENTE"
2. **Mise à jour automatique** : Si une ressource est déjà affectée au job, sa quantité est mise à jour
3. **Création automatique** : Si la ressource n'est pas encore affectée, une nouvelle affectation est créée
4. **Ressources communes** : Tous les jobs reçoivent exactement les mêmes ressources avec les mêmes quantités
5. **Traitement en lot** : Chaque job est traité individuellement, les erreurs d'un job n'affectent pas les autres

### Règles de suppression

1. **Statut du job** : Les ressources ne peuvent être supprimées que des jobs qui ne sont pas en statut "EN ATTENTE"
2. **Suppression partielle** : Si certaines ressources ne sont pas affectées au job, elles sont ignorées
3. **Comptage des suppressions** : Le nombre réel de suppressions est retourné

## Exemples d'utilisation

### Affecter les mêmes ressources à plusieurs jobs

```bash
curl -X POST \
  http://localhost:8000/api/inventory/jobs/assign-resources/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "job_ids": [123, 124, 125],
    "resource_assignments": [
      {
        "resource_id": 1,
        "quantity": 2
      },
      {
        "resource_id": 3,
        "quantity": 1
      }
    ]
  }'
```

### Récupérer les ressources d'un job

```bash
curl -X GET \
  http://localhost:8000/api/inventory/job/123/resources/ \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Supprimer des ressources d'un job

```bash
curl -X DELETE \
  http://localhost:8000/api/inventory/job/123/remove-resources/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "resource_ids": [1, 3]
  }'
```

## Gestion des erreurs

### Erreurs de validation (400)

```json
{
  "error": "job_ids: La liste des IDs de jobs est obligatoire"
}
```

### Erreurs de règle métier (422)

```json
{
  "error": "Les ressources ne peuvent pas être affectées aux jobs en statut 'EN ATTENTE'. Job JOB123 doit d'abord être validé."
}
```

### Erreurs de ressource non trouvée (404)

```json
{
  "error": "Job avec l'ID 123 non trouvé"
}
```

### Gestion des erreurs en lot

Lors de l'affectation en lot, si un job échoue, l'erreur est incluse dans le résultat de ce job spécifique, mais les autres jobs continuent d'être traités :

```json
{
  "success": true,
  "message": "Traitement terminé pour 3 jobs",
  "total_jobs_processed": 3,
  "total_assignments_created": 4,
  "total_assignments_updated": 0,
  "job_results": [
    {
      "success": true,
      "message": "2 affectations créées, 0 affectations mises à jour",
      "assignments_created": 2,
      "assignments_updated": 0,
      "total_assignments": 2,
      "job_id": 123,
      "job_reference": "JOBABC123"
    },
    {
      "success": true,
      "message": "2 affectations créées, 0 affectations mises à jour",
      "assignments_created": 2,
      "assignments_updated": 0,
      "total_assignments": 2,
      "job_id": 124,
      "job_reference": "JOBABC124"
    },
    {
      "success": false,
      "message": "Les ressources ne peuvent pas être affectées aux jobs en statut 'EN ATTENTE'",
      "assignments_created": 0,
      "assignments_updated": 0,
      "total_assignments": 0,
      "job_id": 125,
      "job_reference": "Job 125"
    }
  ]
}
```

## Modèles de données

### JobDetailRessource

```python
class JobDetailRessource(TimeStampedModel, ReferenceMixin):
    reference = models.CharField(unique=True, max_length=20, null=False)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    ressource = models.ForeignKey('masterdata.Ressource', on_delete=models.CASCADE)
    quantity = models.IntegerField(null=True, blank=True)
    history = HistoricalRecords()
```

### Ressource

```python
class Ressource(CodeGeneratorMixin, TimeStampedModel):
    reference = models.CharField(unique=True, max_length=20)
    libelle = models.CharField(max_length=100)
    description = models.TextField(max_length=100, null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES)
    history = HistoricalRecords()
```

## Tests

L'API inclut une suite complète de tests couvrant :

- Affectation réussie de ressources communes à plusieurs jobs
- Validation des données
- Gestion des erreurs
- Règles métier
- Authentification
- Cas limites
- Traitement des erreurs partielles en lot
- Vérification que tous les jobs reçoivent les mêmes ressources

Pour exécuter les tests :

```bash
python manage.py test apps.inventory.tests.test_resource_assignment_api
```

## Sécurité

- **Authentification requise** : Tous les endpoints nécessitent une authentification
- **Permissions** : Vérification des permissions utilisateur
- **Validation des données** : Validation stricte des entrées
- **Transactions** : Opérations atomiques pour garantir la cohérence des données 

## Comportement transactionnel

L'API utilise des transactions atomiques pour garantir la cohérence des données :

- **Toutes les affectations réussissent** : Si tous les jobs et ressources sont valides, toutes les affectations sont créées/mises à jour.
- **Aucune affectation en cas d'erreur** : Si un seul job ou ressource pose problème, aucune affectation n'est effectuée (rollback complet).
- **Validation préalable** : Tous les jobs et ressources sont validés avant de commencer les affectations.

### Exemples d'erreurs qui bloquent l'affectation

1. **Job inexistant** : Si un job_id n'existe pas, l'erreur 404 est retournée et aucune affectation n'est effectuée.
2. **Job en statut EN ATTENTE** : Si un job est en statut "EN ATTENTE", l'erreur 422 est retournée et aucune affectation n'est effectuée.
3. **Ressource inexistante** : Si une ressource n'existe pas, l'erreur 404 est retournée et aucune affectation n'est effectuée.

### Exemple de réponse d'erreur

```json
{
  "error": "Job avec l'ID 125 non trouvé"
}
```

**Code de statut** : 404 NOT FOUND 