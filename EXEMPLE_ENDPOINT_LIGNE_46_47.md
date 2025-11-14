# Exemple d'endpoint basé sur la ligne 46-47 (UnassignedLocationsView)

## 📍 Endpoint actuel

```python
# apps/masterdata/urls.py (ligne 46-47)
path('warehouses/<int:account_id>/warehouse/<int:warehouse_id>/inventory/<int:inventory_id>/locations/unassigned/', 
     UnassignedLocationsView.as_view(), 
     name='account-warehouse-unassigned-locations'),
```

---

## 🔍 Exemples d'utilisation avec filtres, tri et recherche

### 1. **Liste simple (pagination par défaut)**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/
```

### 2. **Recherche globale**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?search=zone-a
```
Recherche "zone-a" dans tous les champs configurés :
- `reference`
- `location_reference`
- `description`
- `sous_zone__reference`
- `sous_zone__sous_zone_name`
- `sous_zone__zone__reference`
- `sous_zone__zone__zone_name`
- `sous_zone__zone__warehouse__reference`
- `sous_zone__zone__warehouse__warehouse_name`

### 3. **Tri simple**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?ordering=location_reference
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?ordering=-created_at
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?ordering=sous_zone__sous_zone_name
```

### 4. **Tri multiple**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?ordering=sous_zone__zone__zone_name,location_reference
```
Tri d'abord par nom de zone, puis par référence d'emplacement.

### 5. **Tri DataTable**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?order[0][column]=1&order[0][dir]=asc
```

### 6. **Filtre par référence d'emplacement**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?location_reference=LOC-001
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?location_reference__icontains=LOC
```

### 7. **Filtre par sous-zone**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?sous_zone_id=10
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?sous_zone_name=Zone%20A
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?sous_zone_reference=SZ-001
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?sous_zone_status=ACTIVE
```

### 8. **Filtre par zone**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?zone_id=5
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?zone_name=Zone%20Principale
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?zone_reference=Z-001
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?zone_status=ACTIVE
```

### 9. **Filtre par entrepôt**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?warehouse_id=5
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?warehouse_name=Entrepôt%20Central
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?warehouse_reference=WH-001
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?warehouse_type=PRINCIPAL
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?warehouse_status=ACTIVE
```

### 10. **Filtre par type d'emplacement**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?location_type_id=3
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?location_type_name=Palette
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?location_type_reference=LT-001
```

### 11. **Filtre par date de création**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?created_at_gte=2024-01-01
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?created_at_lte=2024-12-31
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?created_at_date=2024-06-15
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?created_at_gte=2024-01-01&created_at_lte=2024-12-31
```

### 12. **Filtre par date de modification**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?updated_at_gte=2024-01-01
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?updated_at_lte=2024-12-31
```

### 13. **Filtre par description**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?description=Stockage%20principal
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?description__icontains=stockage
```

### 14. **Filtre par statut actif**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?is_active=true
```

### 15. **Pagination**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?page=2
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?page=2&page_size=50
```

### 16. **Combinaison complète**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?search=zone-a&sous_zone_id=10&zone_status=ACTIVE&ordering=-created_at&page=1&page_size=20&created_at_gte=2024-01-01
```

---

## 🔧 Exemples de requêtes cURL

### Recherche globale + Filtre + Tri
```bash
curl -X GET "http://localhost:8000/api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?search=zone-a&sous_zone_id=10&ordering=-created_at&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filtre par zone et sous-zone
```bash
curl -X GET "http://localhost:8000/api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?zone_name=Zone%20Principale&sous_zone_status=ACTIVE" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filtre par date et tri
```bash
curl -X GET "http://localhost:8000/api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?created_at_gte=2024-01-01&created_at_lte=2024-12-31&ordering=location_reference" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Tri DataTable avec recherche
```bash
curl -X GET "http://localhost:8000/api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?search[value]=LOC&order[0][column]=1&order[0][dir]=asc&start=0&length=25" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 Format de réponse

### Succès (200 OK)
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "reference": "LOC-REF-001",
      "location_reference": "LOC-001",
      "description": "Emplacement principal zone A",
      "is_active": true,
      "sous_zone": {
        "id": 10,
        "reference": "SZ-001",
        "sous_zone_name": "Sous-zone A",
        "sous_zone_status": "ACTIVE"
      },
      "zone": {
        "id": 5,
        "reference": "Z-001",
        "zone_name": "Zone Principale",
        "zone_status": "ACTIVE"
      },
      "warehouse": {
        "id": 5,
        "reference": "WH-001",
        "warehouse_name": "Entrepôt Central",
        "warehouse_type": "PRINCIPAL",
        "status": "ACTIVE"
      },
      "location_type": {
        "id": 3,
        "reference": "LT-001",
        "name": "Palette"
      },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T14:45:00Z"
    },
    ...
  ]
}
```

---

## 📋 Liste complète des paramètres disponibles

### Recherche
- `search` : Recherche globale dans tous les champs configurés
- `search[value]` : Recherche DataTable

### Tri
- `ordering` : Tri par champ (ex: `ordering=location_reference`, `ordering=-created_at`)
- `order[0][column]` : Tri DataTable (index de colonne)
- `order[0][dir]` : Direction du tri DataTable (`asc` ou `desc`)

### Pagination
- `page` : Numéro de page
- `page_size` : Taille de page (1-100)

### Filtres de base
- `reference` : Référence d'emplacement (contient)
- `reference_exact` : Référence exacte
- `location_reference` : Référence d'emplacement (contient)
- `location_reference_exact` : Référence exacte
- `description` : Description (contient)
- `is_active` : Statut actif (true/false)

### Filtres de sous-zone
- `sous_zone_id` : ID de sous-zone
- `sous_zone_reference` : Référence de sous-zone (contient)
- `sous_zone_name` : Nom de sous-zone (contient)
- `sous_zone_status` : Statut de sous-zone (exact)

### Filtres de zone
- `zone_id` : ID de zone
- `zone_reference` : Référence de zone (contient)
- `zone_name` : Nom de zone (contient)
- `zone_status` : Statut de zone (exact)

### Filtres d'entrepôt
- `warehouse_id` : ID d'entrepôt
- `warehouse_reference` : Référence d'entrepôt (contient)
- `warehouse_name` : Nom d'entrepôt (contient)
- `warehouse_type` : Type d'entrepôt (exact)
- `warehouse_status` : Statut d'entrepôt (exact)

### Filtres de type d'emplacement
- `location_type_id` : ID de type d'emplacement
- `location_type_reference` : Référence de type (contient)
- `location_type_name` : Nom de type (contient)

### Filtres de date
- `created_at_gte` : Date de création >= (YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS)
- `created_at_lte` : Date de création <= (YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS)
- `created_at_date` : Date de création exacte (YYYY-MM-DD)
- `updated_at_gte` : Date de modification >= (YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS)
- `updated_at_lte` : Date de modification <= (YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS)

---

## ✅ Exemples pratiques

### 1. Trouver tous les emplacements non affectés dans une zone spécifique
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?zone_id=5&ordering=location_reference
```

### 2. Rechercher des emplacements par nom de sous-zone
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?search=zone-a&sous_zone_status=ACTIVE
```

### 3. Filtrer les emplacements créés récemment
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?created_at_gte=2024-01-01&ordering=-created_at
```

### 4. Lister les emplacements avec pagination
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?page=1&page_size=50&ordering=location_reference
```

### 5. Recherche avancée avec plusieurs filtres
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?zone_name=Zone%20Principale&sous_zone_status=ACTIVE&location_type_id=3&created_at_gte=2024-01-01&ordering=sous_zone__sous_zone_name,location_reference
```

