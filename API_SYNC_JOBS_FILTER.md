# Filtre des Jobs dans l'API de Synchronisation Mobile

## 📋 Vue d'ensemble

L'API de synchronisation mobile (`/api/mobile/sync/data/`) a été modifiée pour ne retourner **que les jobs avec les statuts TRANSFERT ou ENTAME**.

## 🎯 Objectif

Optimiser la synchronisation mobile en ne récupérant que les jobs actifs qui nécessitent une action de la part des utilisateurs mobiles.

## 🔧 Modification technique

### Fichier modifié
`apps/mobile/repositories/sync_repository.py`

### Méthode modifiée
```python
def get_jobs_by_inventories(self, inventories):
    """Récupère les jobs pour les inventaires donnés avec statut TRANSFERT ou ENTAME"""
    return Job.objects.filter(
        inventory__in=inventories,
        status__in=['TRANSFERT', 'ENTAME']
    )
```

### Avant
```python
def get_jobs_by_inventories(self, inventories):
    """Récupère les jobs pour les inventaires donnés"""
    return Job.objects.filter(inventory__in=inventories)
```

## 📊 Statuts des Jobs

| Statut | Description | Retourné par l'API ? |
|--------|-------------|---------------------|
| EN ATTENTE | Job en attente d'affectation | ❌ Non |
| AFFECTE | Job affecté à une équipe | ❌ Non |
| PRET | Job prêt à démarrer | ❌ Non |
| **TRANSFERT** | Job en cours de transfert | ✅ **Oui** |
| **ENTAME** | Job commencé par l'équipe | ✅ **Oui** |
| VALIDE | Job validé | ❌ Non |
| TERMINE | Job terminé | ❌ Non |
| SAISIE MANUELLE | Job en saisie manuelle | ❌ Non |

## 🔄 Cycle de vie d'un Job

```
EN ATTENTE → AFFECTE → PRET → [TRANSFERT] → [ENTAME] → VALIDE → TERMINE
                                    ↑            ↑
                              Retourné par    Retourné par
                                 l'API          l'API
```

## 📱 Impact sur l'application mobile

### Avantages
1. ✅ **Performance améliorée** - Moins de données transférées
2. ✅ **Pertinence** - Uniquement les jobs nécessitant une action
3. ✅ **Batterie** - Moins de données = moins de consommation
4. ✅ **Clarté** - L'utilisateur mobile ne voit que ce qui le concerne

### Jobs visibles sur mobile
- Jobs en cours de **transfert** vers un emplacement
- Jobs **entamés** par l'équipe mobile

### Jobs non visibles sur mobile
- Jobs en attente d'affectation
- Jobs déjà terminés ou validés
- Jobs en préparation

## 🧪 Test de l'API

### Endpoint
```
GET /api/mobile/sync/data/user/{user_id}/
```

### Headers
```http
Authorization: Token {your_token}
Content-Type: application/json
```

### Exemple de réponse
```json
{
  "success": true,
  "sync_id": "sync_8_1728123456",
  "timestamp": "2025-10-08T10:30:00Z",
  "data": {
    "inventories": [...],
    "jobs": [
      {
        "job_web_id": 123,
        "reference": "JOB-xxx",
        "status": "TRANSFERT",
        "warehouse": {...}
      },
      {
        "job_web_id": 124,
        "reference": "JOB-yyy",
        "status": "ENTAME",
        "warehouse": {...}
      }
    ],
    "assignments": [...],
    "countings": [...]
  }
}
```

## 🚀 Script de test

Un script de test est disponible pour valider le filtre:

```bash
python test_sync_api_filtered_jobs.py
```

### Ce que teste le script:
1. ✅ Récupération d'un utilisateur mobile avec compte
2. ✅ Comptage des jobs dans la base par statut
3. ✅ Appel à l'API de synchronisation
4. ✅ Validation que seuls les jobs TRANSFERT/ENTAME sont retournés
5. ✅ Affichage du résumé complet

## 📝 Utilisation

### Côté serveur (Django)
Aucune modification nécessaire dans les vues. Le filtre est appliqué automatiquement dans le repository.

### Côté mobile (Application)
L'application mobile recevra automatiquement uniquement les jobs pertinents lors de la synchronisation.

```dart
// Exemple Flutter/Dart
Future<void> syncData() async {
  final response = await api.get('/api/mobile/sync/data/user/$userId/');
  
  if (response.success) {
    // Les jobs retournés sont uniquement TRANSFERT ou ENTAME
    final jobs = response.data.jobs;
    
    for (var job in jobs) {
      // Traiter uniquement les jobs actifs
      print('Job actif: ${job.reference} - ${job.status}');
    }
  }
}
```

## ⚠️ Points d'attention

### 1. Migrations de statut
Si un job passe de **ENTAME** à **VALIDE** pendant que l'utilisateur mobile est hors ligne:
- Le job sera toujours dans les données locales de l'utilisateur
- À la prochaine synchronisation, il disparaîtra de la liste
- **Recommandation**: Implémenter une logique de réconciliation dans l'app mobile

### 2. Jobs multiples
Un utilisateur mobile peut avoir plusieurs jobs simultanément:
- Plusieurs jobs en **TRANSFERT** vers différents emplacements
- Plusieurs jobs **ENTAMÉS** en parallèle
- **Recommandation**: Interface mobile avec liste priorisée

### 3. Données historiques
Les jobs terminés ne sont plus synchronisés:
- **Avantage**: Base de données mobile légère
- **Inconvénient**: Historique non disponible
- **Solution**: API séparée pour l'historique si nécessaire

## 🔍 Vérification

### Requête SQL équivalente
```sql
SELECT * FROM inventory_job
WHERE inventory_id IN (
    SELECT id FROM inventory_inventory 
    WHERE status = 'EN REALISATION'
)
AND status IN ('TRANSFERT', 'ENTAME')
ORDER BY created_at DESC;
```

### Comptage rapide
```python
from apps.inventory.models import Job

# Total des jobs
total_jobs = Job.objects.count()

# Jobs synchronisés
synced_jobs = Job.objects.filter(status__in=['TRANSFERT', 'ENTAME']).count()

print(f"Jobs total: {total_jobs}")
print(f"Jobs synchronisés: {synced_jobs}")
print(f"Ratio: {synced_jobs/total_jobs*100:.1f}%")
```

## 📚 Références

- **Service**: `apps/mobile/services/sync_service.py`
- **Repository**: `apps/mobile/repositories/sync_repository.py`
- **Vue**: `apps/mobile/views/sync/sync_data_view.py`
- **Modèle Job**: `apps/inventory/models.py` (ligne 143-173)

## 🆕 Historique des modifications

| Date | Version | Modification |
|------|---------|-------------|
| 2025-10-08 | 1.0 | Ajout du filtre TRANSFERT/ENTAME |

---

**Note**: Cette modification améliore la performance et la pertinence de la synchronisation mobile sans affecter les autres fonctionnalités du système.

