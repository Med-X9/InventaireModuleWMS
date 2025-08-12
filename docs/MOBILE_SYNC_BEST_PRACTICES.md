# APIs Mobile - Bonnes Pratiques

## Table des matières
1. [Architecture recommandée](#architecture-recommandée)
2. [APIs unifiées vs séparées](#apis-unifiées-vs-séparées)
3. [Tables de synchronisation](#tables-de-synchronisation)
4. [Endpoints créés](#endpoints-créés)
5. [Avantages de cette approche](#avantages-de-cette-approche)

---

## Architecture recommandée

### ✅ **Approche unifiée intelligente**

Nous avons créé une architecture qui combine le meilleur des deux mondes :

1. **APIs unifiées** pour la synchronisation principale
2. **Logging et monitoring** pour le suivi
3. **Gestion des erreurs** robuste
4. **Transactions atomiques** pour la cohérence

---

## APIs unifiées vs séparées

### ❌ **Approche monolithique (à éviter)**
```python
# Une seule API qui fait tout - MAUVAISE PRATIQUE
@api_view(['POST'])
def do_everything(request):
    # Authentification
    # Récupération des données
    # Upload des données
    # Gestion des erreurs
    # Logging
    # etc...
```

### ✅ **Approche unifiée intelligente (recommandée)**
```python
# APIs séparées mais optimisées - BONNE PRATIQUE
@api_view(['GET'])
def sync_data(request):  # Une seule requête pour tout télécharger
    # Récupère toutes les données nécessaires
    # Optimisé pour les performances
    # Gestion d'erreurs centralisée

@api_view(['POST'])
def upload_data(request):  # Une seule requête pour tout uploader
    # Traite tous les types d'uploads
    # Transactions atomiques
    # Logging détaillé
```

---

## Tables de synchronisation

### Tables créées dans `apps/mobile/models.py`

#### 1. **MobileSyncSession**
```python
class MobileSyncSession(TimeStampedModel):
    sync_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(UserApp, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=100, blank=True, null=True)
    last_sync_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```
**Usage :** Gère les sessions de synchronisation par utilisateur

#### 2. **MobileSyncLog**
```python
class MobileSyncLog(TimeStampedModel):
    LOG_TYPES = (
        ('DOWNLOAD', 'Téléchargement'),
        ('UPLOAD', 'Upload'),
        ('ERROR', 'Erreur'),
        ('CONFLICT', 'Conflit'),
    )
    sync_session = models.ForeignKey(MobileSyncSession, on_delete=models.CASCADE)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    operation = models.CharField(max_length=100)
    details = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=True)
```
**Usage :** Logging détaillé de toutes les opérations de synchronisation

#### 3. **MobileCountingUpload**
```python
class MobileCountingUpload(TimeStampedModel):
    sync_id = models.CharField(max_length=50)
    detail_id = models.CharField(max_length=50, unique=True)
    quantite_comptee = models.IntegerField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    numero_lot = models.CharField(max_length=100, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    dlc = models.DateField(blank=True, null=True)
    compte_par = models.ForeignKey('inventory.Personne', on_delete=models.CASCADE)
    date_comptage = models.DateTimeField()
    counting_detail = models.ForeignKey(CountingDetail, on_delete=models.CASCADE, blank=True, null=True)
    is_processed = models.BooleanField(default=False)
```
**Usage :** Stockage temporaire des uploads de comptages

#### 4. **MobileSerialNumberUpload**
```python
class MobileSerialNumberUpload(TimeStampedModel):
    sync_id = models.CharField(max_length=50)
    numero_serie = models.CharField(max_length=100)
    counting_detail = models.ForeignKey(CountingDetail, on_delete=models.CASCADE)
    timestamp_sync = models.DateTimeField()
    is_processed = models.BooleanField(default=False)
```
**Usage :** Stockage temporaire des numéros de série

#### 5. **MobileAssignmentStatusUpload**
```python
class MobileAssignmentStatusUpload(TimeStampedModel):
    sync_id = models.CharField(max_length=50)
    assignment = models.ForeignKey(Assigment, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    entame_date = models.DateTimeField(blank=True, null=True)
    date_start = models.DateTimeField(blank=True, null=True)
    is_processed = models.BooleanField(default=False)
```
**Usage :** Stockage temporaire des statuts d'assignation

---

## Endpoints créés

### Authentification
- `POST /api/mobile/auth/login/` - Connexion
- `POST /api/mobile/auth/logout/` - Déconnexion  
- `POST /api/mobile/auth/refresh/` - Refresh token

### Synchronisation unifiée
- `GET /api/mobile/sync/data/` - Téléchargement de toutes les données
- `POST /api/mobile/sync/upload/` - Upload de toutes les données

---

## Avantages de cette approche

### ✅ **Performance**
- **Une seule requête** pour télécharger toutes les données
- **Réduction du trafic réseau** entre mobile et serveur
- **Optimisation des requêtes** base de données

### ✅ **Maintenabilité**
- **Code centralisé** et facile à maintenir
- **Logging détaillé** pour le debugging
- **Gestion d'erreurs** robuste

### ✅ **Sécurité**
- **Authentification** obligatoire
- **Transactions atomiques** pour la cohérence
- **Validation** des données

### ✅ **Monitoring**
- **Logs détaillés** de toutes les opérations
- **Suivi des sessions** de synchronisation
- **Détection d'erreurs** en temps réel

### ✅ **Évolutivité**
- **Facile d'ajouter** de nouvelles fonctionnalités
- **Modularité** du code
- **Tests unitaires** simplifiés

---

## Exemple d'utilisation

### Téléchargement des données
```bash
GET /api/mobile/sync/data/?inventory_id=123
Authorization: Bearer <token>

Response:
{
  "success": true,
  "sync_id": "sync_123_1642345678",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "inventories": [...],
    "jobs": [...],
    "assignments": [...],
    "countings": [...],
    "products": [...],
    "locations": [...],
    "stocks": [...]
  }
}
```

### Upload des données
```bash
POST /api/mobile/sync/upload/
Authorization: Bearer <token>

{
  "sync_id": "sync_123_1642345678",
  "countings": [...],
  "assignments": [...]
}

Response:
{
  "success": true,
  "sync_id": "sync_123_1642345678",
  "uploaded_count": 15,
  "errors": [],
  "conflicts": []
}
```

---

## Conclusion

Cette approche unifiée intelligente offre :

1. **Performance optimale** avec une seule requête
2. **Code maintenable** et bien structuré
3. **Monitoring complet** des opérations
4. **Gestion d'erreurs** robuste
5. **Évolutivité** pour les futures fonctionnalités

C'est la **meilleure pratique** pour les APIs de synchronisation mobile. 