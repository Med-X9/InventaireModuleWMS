# API de Mise en Prêt des Jobs Affectés

## Description

Cette API permet de mettre plusieurs jobs affectés au statut "PRET" en une seule requête. Seuls les jobs ayant le statut "AFFECTE" et des comptages correctement affectés avec des sessions peuvent être mis au statut "PRET".

**Note importante** : La validation des comptages dépend de la configuration de l'inventaire :
- Si le 1er comptage est "image de stock" : seul le 2ème comptage doit être affecté avec une session
- Sinon : tous les comptages d'ordre 1 et 2 doivent être affectés avec des sessions

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
    "ready_jobs_count": 3,
    "ready_jobs": [
        {
            "job_id": 1,
            "job_reference": "JOB001"
        },
        {
            "job_id": 2,
            "job_reference": "JOB002"
        },
        {
            "job_id": 3,
            "job_reference": "JOB003"
        }
    ],
    "updated_assignments": [
        {
            "assignment_id": 1,
            "counting_reference": "CNT001",
            "counting_order": 2
        }
    ],
    "ready_date": "2024-01-15T10:00:00Z",
    "message": "3 jobs et 1 assignments marqués comme PRET"
}
```

### Erreur - Validation (400 Bad Request)

```json
{
    "success": false,
    "message": "Seuls les jobs avec le statut AFFECTE et leurs comptages correctement affectés avec des sessions peuvent être mis au statut PRET. Jobs invalides : Job JOB001 (statut: EN ATTENTE), Job JOB002 (aucun comptage avec session affectée)"
}
```

## Règles de validation

### 1. Statut du job
- Le job doit avoir le statut "AFFECTE"
- Les jobs en "EN ATTENTE", "VALIDE", "PRET", etc. ne peuvent pas être mis en PRET

### 2. Affectations de comptages

#### Cas spécial : 1er comptage = "image de stock"
- **Seul le 2ème comptage doit être affecté avec une session**
- Le 1er comptage (image de stock) n'a pas besoin d'être affecté
- Le 2ème comptage doit avoir une session assignée

#### Cas normal : 1er comptage ≠ "image de stock"
- **Tous les comptages d'ordre 1 et 2 doivent être affectés avec des sessions**
- Chaque comptage doit avoir une session assignée

### 3. Sessions requises
- Au moins un comptage doit avoir une session affectée
- Les assignments sans session ne sont pas considérés comme "affectés"

## Exemples de configurations valides

### Configuration avec image de stock
```
1er comptage : "image de stock" (pas d'affectation de session)
2ème comptage : "en vrac" (affecté avec session)
→ VALIDE ✅
```

### Configuration normale
```
1er comptage : "en vrac" (affecté avec session)
2ème comptage : "par article" (affecté avec session)
→ VALIDE ✅
```

## Exemples de configurations invalides

### Job sans affectation
```
Aucun comptage affecté avec session
→ INVALIDE ❌
```

### Configuration normale incomplète
```
1er comptage : "en vrac" (affecté avec session)
2ème comptage : "par article" (pas d'affectation de session)
→ INVALIDE ❌
```

### Configuration image de stock incomplète
```
1er comptage : "image de stock" (pas d'affectation de session)
2ème comptage : "en vrac" (pas d'affectation de session)
→ INVALIDE ❌
```

## Workflow complet

### 1. Création de jobs
```
POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/
→ Jobs créés avec assignments selon la configuration
```

### 2. Affectation de sessions
```
POST /api/inventory/{inventory_id}/assign-jobs/
→ Sessions affectées aux assignments existants
```

### 3. Validation des jobs
```
POST /api/inventory/jobs/validate/
→ Jobs validés pour passer au statut "VALIDE"
```

### 4. Mise en prêt
```
POST /api/inventory/jobs/ready/
→ Jobs mis en PRET selon les règles métier
```

## Cas d'usage courants

### Inventaire avec image de stock
1. Créer l'inventaire avec 1er comptage = "image de stock"
2. Créer les jobs → 1 assignment par job (2ème comptage)
3. Affecter une session au 2ème comptage
4. Mettre les jobs en PRET

### Inventaire normal
1. Créer l'inventaire avec comptages normaux
2. Créer les jobs → 2 assignments par job
3. Affecter des sessions aux deux comptages
4. Mettre les jobs en PRET

## Messages d'erreur courants

### "Job non trouvé"
- Vérifiez que les IDs des jobs existent
- Vérifiez que les jobs appartiennent à l'inventaire

### "Statut invalide"
- Seuls les jobs avec le statut "AFFECTE" peuvent être mis en PRET
- Validez d'abord les jobs avec l'API de validation

### "Aucun comptage avec session affectée"
- Affectez d'abord des sessions aux comptages
- Utilisez l'API d'affectation de sessions

### "Comptages non affectés avec session"
- Dans le cas normal, tous les comptages d'ordre 1 et 2 doivent avoir des sessions
- Dans le cas image de stock, seul le 2ème comptage doit avoir une session

## Intégration avec les autres APIs

### API de création de jobs
- Les jobs sont créés avec des assignments selon la configuration
- Dans le cas image de stock, seul le 2ème comptage reçoit une affectation

### API d'affectation de sessions
- Seuls les assignments existants peuvent recevoir des sessions
- Les sessions sont requises pour mettre les jobs en PRET

### API de validation
- Les jobs doivent être validés avant d'être mis en PRET
- La validation change le statut de "EN ATTENTE" à "VALIDE"

## Performance et limitations

### Limitations
- Pas de limite sur le nombre de jobs traités
- Tous les jobs doivent appartenir au même inventaire
- Traitement en transaction atomique

### Performance
- Validation optimisée avec requêtes groupées
- Mise à jour en lot des assignments
- Logs détaillés pour le debugging

## Monitoring et logs

### Logs générés
- Validation des jobs et assignments
- Marquage des jobs et assignments en PRET
- Erreurs de validation détaillées

### Métriques à surveiller
- Nombre de jobs mis en PRET
- Nombre d'assignments mis en PRET
- Erreurs de validation par type

## Dépannage

### Vérifications préalables
1. Les jobs existent et ont le statut "AFFECTE"
2. Les comptages sont correctement configurés
3. Les sessions sont affectées selon les règles
4. Les assignments existent pour les comptages requis

### Validation manuelle
```sql
-- Vérifier les jobs et leurs assignments
SELECT j.reference, j.status, a.counting_id, a.session_id
FROM inventory_job j
LEFT JOIN inventory_assigment a ON j.id = a.job_id
WHERE j.id IN (1, 2, 3);
```

### Test avec curl
```bash
curl -X POST \
  http://localhost:8000/api/inventory/jobs/ready/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "job_ids": [1, 2, 3]
}'
``` 