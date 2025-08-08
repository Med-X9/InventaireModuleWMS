# Modèle NSerie - Gestion des Numéros de Série

## Vue d'ensemble

Le modèle `NSerie` permet de gérer les numéros de série des produits dans le système WMS. Il est lié au modèle `Product` et permet de suivre chaque unité individuelle d'un produit avec des informations détaillées.

## Structure du Modèle

### Champs principaux

- **`reference`** : Référence unique générée automatiquement (format: NS-{id}-{timestamp}-{hash})
- **`n_serie`** : Numéro de série unique (100 caractères max)
- **`product`** : Relation vers le modèle Product (obligatoire)
- **`status`** : Statut du numéro de série (ACTIVE, INACTIVE, USED, EXPIRED, BLOCKED)
- **`description`** : Description optionnelle
- **`date_fabrication`** : Date de fabrication
- **`date_expiration`** : Date d'expiration
- **`warranty_end_date`** : Date de fin de garantie
- **`location`** : Emplacement où se trouve le numéro de série
- **`stock_quantity`** : Quantité en stock (défaut: 1)
- **`is_tracked`** : Si le suivi est activé (défaut: True)
- **`notes`** : Notes additionnelles

### Propriétés calculées

- **`is_expired`** : Vérifie si le numéro de série est expiré
- **`is_warranty_valid`** : Vérifie si la garantie est encore valide

## Validation

### Règles de validation

1. **Produit supporte les numéros de série** : Le produit doit avoir `n_serie=True`
2. **Unicité** : Le numéro de série doit être unique pour un produit donné
3. **Dates cohérentes** : La date d'expiration ne peut pas être postérieure à la date de fin de garantie

### Exemple de validation

```python
from apps.masterdata.models import NSerie, Product

# Créer un produit avec support des numéros de série
product = Product.objects.create(
    reference='PRD-001',
    Internal_Product_Code='PROD001',
    Short_Description='Produit avec Numéros de Série',
    n_serie=True,  # Important !
    # ... autres champs
)

# Créer un numéro de série
nserie = NSerie.objects.create(
    n_serie='NS-001-2024-001',
    product=product,
    status='ACTIVE'
)
```

## APIs disponibles

### 1. Liste des numéros de série

**Endpoint**: `GET /api/v1/masterdata/nseries/`

**Paramètres de filtrage**:
- `n_serie` : Recherche par numéro de série
- `product_id` : Filtrer par produit
- `status` : Filtrer par statut
- `location_id` : Filtrer par emplacement
- `expired` : Filtrer les expirés
- `expiring_soon` : Filtrer ceux qui expirent bientôt

**Exemple**:
```bash
curl -X GET "http://localhost:8000/api/v1/masterdata/nseries/?status=ACTIVE&expired=false"
```

### 2. Détails d'un numéro de série

**Endpoint**: `GET /api/v1/masterdata/nseries/{id}/`

**Exemple**:
```bash
curl -X GET "http://localhost:8000/api/v1/masterdata/nseries/1/"
```

### 3. Créer un numéro de série

**Endpoint**: `POST /api/v1/masterdata/nseries/create/`

**Données requises**:
```json
{
    "n_serie": "NS-001-2024-001",
    "product": 1,
    "status": "ACTIVE",
    "description": "Numéro de série de test",
    "date_fabrication": "2024-01-01",
    "date_expiration": "2025-01-01",
    "warranty_end_date": "2026-01-01",
    "location": 1,
    "stock_quantity": 1,
    "is_tracked": true,
    "notes": "Notes de test"
}
```

### 4. Mettre à jour un numéro de série

**Endpoint**: `PUT /api/v1/masterdata/nseries/{id}/update/`

### 5. Supprimer un numéro de série

**Endpoint**: `DELETE /api/v1/masterdata/nseries/{id}/delete/`

### 6. Numéros de série par produit

**Endpoint**: `GET /api/v1/masterdata/products/{product_id}/nseries/`

### 7. Numéros de série par emplacement

**Endpoint**: `GET /api/v1/masterdata/locations/{location_id}/nseries/`

### 8. Numéros de série expirés

**Endpoint**: `GET /api/v1/masterdata/nseries/expired/`

### 9. Numéros de série qui expirent bientôt

**Endpoint**: `GET /api/v1/masterdata/nseries/expiring/?days=30`

### 10. Statistiques

**Endpoint**: `GET /api/v1/masterdata/nseries/statistics/`

### 11. Déplacer un numéro de série

**Endpoint**: `POST /api/v1/masterdata/nseries/{nserie_id}/move/`

**Données**:
```json
{
    "location_id": 2
}
```

### 12. Mettre à jour le statut

**Endpoint**: `POST /api/v1/masterdata/nseries/{nserie_id}/status/`

**Données**:
```json
{
    "status": "USED"
}
```

## Utilisation avec Python

### Service NSerieService

```python
from apps.masterdata.services.nserie_service import NSerieService

# Initialiser le service
nserie_service = NSerieService()

# Créer un numéro de série
data = {
    'n_serie': 'NS-001-2024-001',
    'product': product,
    'status': 'ACTIVE',
    'description': 'Numéro de série de test'
}
nserie = nserie_service.create_nserie(data)

# Récupérer les numéros de série d'un produit
nseries = nserie_service.get_nseries_by_product(product.id)

# Récupérer les numéros de série expirés
expired_nseries = nserie_service.get_expired_nseries()

# Déplacer un numéro de série
updated_nserie = nserie_service.move_nserie_to_location(nserie.id, new_location.id)

# Mettre à jour le statut
updated_nserie = nserie_service.update_nserie_status(nserie.id, 'USED')

# Obtenir les statistiques
statistics = nserie_service.get_nserie_statistics()
```

### Repository NSerieRepository

```python
from apps.masterdata.repositories.nserie_repository import NSerieRepository

# Initialiser le repository
repository = NSerieRepository()

# Recherche avec filtres
filters = {
    'product_id': 1,
    'status': 'ACTIVE',
    'expired': False
}
nseries = repository.get_nseries_with_filters(filters)

# Recherche par terme
search_results = repository.search_nseries('NS-001')
```

## Cas d'usage courants

### 1. Suivi des équipements

```python
# Créer un numéro de série pour un équipement
equipment_nserie = NSerie.objects.create(
    n_serie='EQ-2024-001',
    product=equipment_product,
    status='ACTIVE',
    description='Équipement de production',
    date_fabrication=date(2024, 1, 1),
    warranty_end_date=date(2027, 1, 1),
    location=production_location
)
```

### 2. Gestion des garanties

```python
# Vérifier les garanties expirées
warranty_expired = NSerie.objects.filter(
    warranty_end_date__lt=timezone.now().date(),
    status__in=['ACTIVE', 'USED']
)

for nserie in warranty_expired:
    print(f"Garantie expirée: {nserie.n_serie} - {nserie.product.Short_Description}")
```

### 3. Suivi des emplacements

```python
# Trouver tous les numéros de série dans un emplacement
location_nseries = NSerie.objects.filter(location=location)

for nserie in location_nseries:
    print(f"Emplacement {location.location_reference}: {nserie.n_serie}")
```

### 4. Gestion des expirations

```python
# Trouver les numéros de série qui expirent dans les 30 jours
expiring_soon = NSerie.objects.filter(
    date_expiration__gte=timezone.now().date(),
    date_expiration__lte=timezone.now().date() + timedelta(days=30),
    status__in=['ACTIVE', 'USED']
)
```

## Migration

Pour ajouter le modèle NSerie à votre base de données :

```bash
python manage.py makemigrations masterdata
python manage.py migrate
```

## Notes importantes

1. **Performance** : Les index sont créés automatiquement sur les champs fréquemment utilisés
2. **Soft Delete** : La suppression est logique (soft delete) pour préserver l'historique
3. **Historique** : Toutes les modifications sont tracées avec django-simple-history
4. **Validation** : Les validations sont effectuées au niveau du modèle et du service
5. **Unicité** : Le numéro de série doit être unique par produit, pas globalement

## Exemples de réponses API

### Liste des numéros de série

```json
{
    "count": 10,
    "next": "http://localhost:8000/api/v1/masterdata/nseries/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "reference": "NS-1-1234567890-ABCD",
            "n_serie": "NS-001-2024-001",
            "product_reference": "PRD-001",
            "product_name": "Produit Test",
            "status": "ACTIVE",
            "location_reference": "A-01-01",
            "stock_quantity": 1,
            "is_expired": false,
            "is_warranty_valid": true,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### Statistiques

```json
{
    "success": true,
    "data": {
        "total_nseries": 100,
        "active_nseries": 80,
        "expired_nseries": 5,
        "used_nseries": 10,
        "blocked_nseries": 5,
        "products_with_nseries": 25,
        "nseries_with_location": 90,
        "nseries_without_location": 10,
        "expiring_soon": 3
    }
}
``` 