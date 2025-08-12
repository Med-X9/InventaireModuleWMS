# API d'Avancement des Emplacements par Job et par Counting

## Vue d'ensemble

Cette API permet d'afficher l'avancement des emplacements par job et par counting, même si le modèle `JobDetail` ne contient pas directement l'information de counting. La progression est calculée en utilisant les données de `CountingDetail` qui contiennent les informations de comptage par emplacement et par counting.

## Structure des données

### Modèles impliqués

- **Job**: Représente un travail d'inventaire
- **JobDetail**: Contient les emplacements associés à un job
- **Counting**: Représente un comptage dans un inventaire
- **CountingDetail**: Contient les détails de comptage par emplacement et par counting
- **Assigment**: Lie un job à un counting

### Logique de calcul

L'avancement est calculé en :
1. Récupérant tous les emplacements d'un job via `JobDetail`
2. Pour chaque counting de l'inventaire, vérifiant s'il existe des `CountingDetail` pour chaque emplacement
3. Calculant le pourcentage de progression basé sur les emplacements terminés

## APIs disponibles

### 1. Avancement d'un Job par Counting

**Endpoint**: `GET /api/v1/jobs/{job_id}/progress-by-counting/`

**Description**: Affiche l'avancement détaillé d'un job spécifique par counting.

**Paramètres**:
- `job_id` (int): ID du job

**Réponse**:
```json
{
  "success": true,
  "data": {
    "job_id": 1,
    "job_reference": "JOB-123",
    "inventory_reference": "INV-456",
    "warehouse_name": "Entrepôt Principal",
    "progress_by_counting": [
      {
        "job_id": 1,
        "job_reference": "JOB-123",
        "job_status": "EN ATTENTE",
        "counting_order": 1,
        "counting_reference": "CNT-001",
        "counting_count_mode": "Comptage manuel",
        "total_emplacements": 10,
        "completed_emplacements": 3,
        "progress_percentage": 30.0,
        "emplacements_details": [
          {
            "location_id": 1,
            "location_reference": "A-01-01",
            "sous_zone_name": "Zone A",
            "zone_name": "Zone 1",
            "status": "TERMINE",
            "counting_details": [
              {
                "id": 1,
                "reference": "CD-001",
                "quantity_inventoried": 5,
                "product_reference": "PROD-001",
                "dlc": "2024-12-31",
                "n_lot": "LOT123",
                "last_synced_at": "2024-01-15T10:30:00Z"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 2. Avancement Global d'un Inventaire par Counting

**Endpoint**: `GET /api/v1/inventory/{inventory_id}/progress-by-counting/`

**Description**: Affiche l'avancement global de tous les jobs d'un inventaire par counting.

**Paramètres**:
- `inventory_id` (int): ID de l'inventaire

**Réponse**:
```json
{
  "success": true,
  "data": {
    "inventory_id": 1,
    "inventory_reference": "INV-456",
    "total_jobs": 5,
    "progress_by_counting": [
      {
        "counting_order": 1,
        "counting_reference": "CNT-001",
        "counting_count_mode": "Comptage manuel",
        "total_emplacements": 50,
        "completed_emplacements": 15,
        "progress_percentage": 30.0,
        "jobs_progress": [
          {
            "job_id": 1,
            "job_reference": "JOB-123",
            "job_status": "EN ATTENTE",
            "total_emplacements": 10,
            "completed_emplacements": 3,
            "progress_percentage": 30.0
          }
        ]
      }
    ]
  }
}
```

## Utilisation

### Exemple avec curl

```bash
# Avancement d'un job spécifique
curl -X GET "http://localhost:8000/api/v1/jobs/1/progress-by-counting/"

# Avancement global d'un inventaire
curl -X GET "http://localhost:8000/api/v1/inventory/1/progress-by-counting/"
```

### Exemple avec Python

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

# Avancement d'un job
job_id = 1
response = requests.get(f"{BASE_URL}/jobs/{job_id}/progress-by-counting/")
if response.status_code == 200:
    data = response.json()
    print(f"Job {data['data']['job_reference']}: {data['data']['progress_by_counting']}")

# Avancement global d'un inventaire
inventory_id = 1
response = requests.get(f"{BASE_URL}/inventory/{inventory_id}/progress-by-counting/")
if response.status_code == 200:
    data = response.json()
    print(f"Inventaire {data['data']['inventory_reference']}: {data['data']['progress_by_counting']}")
```

## Gestion des erreurs

### Erreurs communes

1. **Job non trouvé**:
```json
{
  "success": false,
  "message": "Job avec l'ID 999 non trouvé"
}
```

2. **Inventaire sans jobs**:
```json
{
  "success": false,
  "message": "Aucun job trouvé pour l'inventaire 999"
}
```

3. **Erreur interne**:
```json
{
  "success": false,
  "message": "Erreur interne : [détails de l'erreur]"
}
```

## Avantages de cette approche

1. **Séparation des responsabilités**: Le modèle `JobDetail` reste simple et ne contient que les informations d'emplacement
2. **Flexibilité**: L'avancement est calculé dynamiquement à partir des données de comptage
3. **Précision**: Utilise les vraies données de `CountingDetail` pour déterminer l'avancement
4. **Extensibilité**: Facile d'ajouter de nouveaux critères de progression

## Notes techniques

- Les pourcentages sont arrondis à 2 décimales
- Les emplacements sont considérés comme "TERMINE" s'il existe au moins un `CountingDetail` pour cet emplacement et ce counting
- Les données sont optimisées avec des `select_related` pour éviter les requêtes N+1
- La logique gère les cas où certains countings peuvent ne pas avoir d'affectations 