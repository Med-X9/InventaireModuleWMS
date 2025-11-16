# Exemples d'endpoints DataTable avec filtres, tri et recherche globale

## 📋 Paramètres DataTable standards

### Paramètres de base
- `draw` : Numéro de draw (pour synchronisation avec le frontend)
- `start` : Index de début (offset pour pagination)
- `length` : Nombre d'éléments par page
- `search[value]` : Valeur de recherche globale
- `search[regex]` : Utiliser regex pour la recherche (true/false)

### Paramètres de tri
- `order[0][column]` : Index de la colonne à trier
- `order[0][dir]` : Direction du tri (asc/desc)
- `order[1][column]` : Index de la deuxième colonne (tri multiple)
- `order[1][dir]` : Direction du deuxième tri

### Paramètres de colonnes
- `columns[0][data]` : Nom du champ de la colonne 0
- `columns[0][name]` : Nom de la colonne 0
- `columns[0][searchable]` : Colonne recherchable (true/false)
- `columns[0][orderable]` : Colonne triable (true/false)
- `columns[0][search][value]` : Valeur de recherche pour la colonne 0
- `columns[0][search][regex]` : Utiliser regex pour la colonne 0 (true/false)

---

## 📝 Exemples d'endpoints

### 1. **Requête DataTable minimale**
```
GET /api/masterdata/products/?draw=1&start=0&length=20
```

### 2. **Recherche globale**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&search[value]=laptop&search[regex]=false
```

### 3. **Tri simple (ascendant)**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&order[0][column]=2&order[0][dir]=asc
```

### 4. **Tri simple (descendant)**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&order[0][column]=2&order[0][dir]=desc
```

### 5. **Tri multiple**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc
```

### 6. **Pagination (page 2)**
```
GET /api/masterdata/products/?draw=1&start=20&length=20
```

### 7. **Pagination (page 3)**
```
GET /api/masterdata/products/?draw=1&start=50&length=20
```

### 8. **Recherche par colonne spécifique**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&columns[2][search][value]=Dell&columns[2][search][regex]=false
```

### 9. **Recherche globale + Tri**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&search[value]=laptop&order[0][column]=2&order[0][dir]=asc
```

### 10. **Recherche globale + Tri + Pagination**
```
GET /api/masterdata/products/?draw=1&start=20&length=20&search[value]=laptop&order[0][column]=2&order[0][dir]=desc
```

### 11. **Configuration complète des colonnes**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&columns[0][data]=id&columns[0][name]=id&columns[0][searchable]=true&columns[0][orderable]=true&columns[0][search][value]=&columns[0][search][regex]=false&columns[1][data]=reference&columns[1][name]=reference&columns[1][searchable]=true&columns[1][orderable]=true&columns[1][search][value]=&columns[1][search][regex]=false&columns[2][data]=Short_Description&columns[2][name]=Short_Description&columns[2][searchable]=true&columns[2][orderable]=true&columns[2][search][value]=&columns[2][search][regex]=false
```

### 12. **Recherche globale + Recherche par colonne**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&search[value]=laptop&columns[2][search][value]=Dell&columns[2][search][regex]=false
```

### 13. **Tri multiple + Recherche**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&search[value]=laptop&order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc
```

### 14. **Filtres personnalisés + DataTable**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&Product_Status=ACTIVE&search[value]=laptop&order[0][column]=2&order[0][dir]=asc
```

### 15. **Filtres multiples + DataTable**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&Product_Status=ACTIVE&product_family_id=5&n_serie=true&search[value]=laptop&order[0][column]=2&order[0][dir]=desc
```

### 16. **Filtres de date + DataTable**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&created_at_gte=2024-01-01&created_at_lte=2024-12-31&search[value]=laptop&order[0][column]=4&order[0][dir]=asc
```

### 17. **Recherche avec regex**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&search[value]=^PROD-&search[regex]=true
```

### 18. **Recherche par colonne avec regex**
```
GET /api/masterdata/products/?draw=1&start=0&length=20&columns[1][search][value]=^PROD-&columns[1][search][regex]=true
```

### 19. **Combinaison complète (tous les paramètres)**
```
GET /api/masterdata/products/?draw=1&start=20&length=50&search[value]=laptop&search[regex]=false&order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc&columns[0][data]=id&columns[0][name]=id&columns[0][searchable]=true&columns[0][orderable]=true&columns[0][search][value]=&columns[0][search][regex]=false&columns[1][data]=reference&columns[1][name]=reference&columns[1][searchable]=true&columns[1][orderable]=true&columns[1][search][value]=&columns[1][search][regex]=false&columns[2][data]=Short_Description&columns[2][name]=Short_Description&columns[2][searchable]=true&columns[2][orderable]=true&columns[2][search][value]=Dell&columns[2][search][regex]=false&Product_Status=ACTIVE&product_family_id=5&created_at_gte=2024-01-01
```

### 20. **Pagination avec taille de page personnalisée**
```
GET /api/masterdata/products/?draw=1&start=0&length=100
```

---

## 🔍 Exemples pour endpoint spécifique (ligne 46-47)

### Endpoint : `/api/masterdata/warehouses/<account_id>/warehouse/<warehouse_id>/inventory/<inventory_id>/locations/unassigned/`

### 1. **Requête DataTable minimale**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=0&length=20
```

### 2. **Recherche globale**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=0&length=20&search[value]=zone-a&search[regex]=false
```

### 3. **Tri par référence d'emplacement**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=0&length=20&order[0][column]=1&order[0][dir]=asc
```

### 4. **Tri par date de création (descendant)**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=0&length=20&order[0][column]=4&order[0][dir]=desc
```

### 5. **Tri multiple (zone puis emplacement)**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=0&length=20&order[0][column]=2&order[0][dir]=asc&order[1][column]=1&order[1][dir]=asc
```

### 6. **Recherche + Tri + Pagination**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=20&length=20&search[value]=LOC&order[0][column]=1&order[0][dir]=asc
```

### 7. **Recherche par colonne (sous-zone)**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=0&length=20&columns[2][search][value]=Zone%20A&columns[2][search][regex]=false
```

### 8. **Filtres + DataTable**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=0&length=20&sous_zone_id=10&zone_status=ACTIVE&search[value]=LOC&order[0][column]=1&order[0][dir]=asc
```

### 9. **Filtres de date + DataTable**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=0&length=20&created_at_gte=2024-01-01&created_at_lte=2024-12-31&order[0][column]=4&order[0][dir]=desc
```

### 10. **Combinaison complète**
```
GET /api/masterdata/warehouses/1/warehouse/5/inventory/10/locations/unassigned/?draw=1&start=20&length=50&search[value]=zone-a&order[0][column]=2&order[0][dir]=asc&order[1][column]=1&order[1][dir]=asc&sous_zone_id=10&zone_status=ACTIVE&created_at_gte=2024-01-01&columns[2][search][value]=Zone%20A&columns[2][search][regex]=false
```

---

## 📊 Format de réponse DataTable

### Succès (200 OK)
```json
{
  "draw": 1,
  "recordsTotal": 150,
  "recordsFiltered": 45,
  "data": [
    {
      "id": 1,
      "reference": "PROD-001",
      "Short_Description": "Laptop Dell XPS 15",
      "Barcode": "1234567890123",
      "Product_Status": "ACTIVE",
      "created_at": "2024-01-15T10:30:00Z"
    },
    ...
  ]
}
```

---

## 🎯 Tableau récapitulatif des paramètres

| Paramètre | Type | Exemple | Description |
|-----------|------|---------|-------------|
| **draw** | Integer | `draw=1` | Numéro de draw (incrémenté à chaque requête) |
| **start** | Integer | `start=0` | Index de début (offset pour pagination) |
| **length** | Integer | `length=20` | Nombre d'éléments par page |
| **search[value]** | String | `search[value]=laptop` | Valeur de recherche globale |
| **search[regex]** | Boolean | `search[regex]=false` | Utiliser regex pour la recherche |
| **order[0][column]** | Integer | `order[0][column]=2` | Index de la colonne à trier |
| **order[0][dir]** | String | `order[0][dir]=asc` | Direction du tri (asc/desc) |
| **order[N][column]** | Integer | `order[1][column]=3` | Index de la N-ième colonne (tri multiple) |
| **order[N][dir]** | String | `order[1][dir]=desc` | Direction du N-ième tri |
| **columns[N][data]** | String | `columns[0][data]=id` | Nom du champ de la colonne N |
| **columns[N][name]** | String | `columns[0][name]=id` | Nom de la colonne N |
| **columns[N][searchable]** | Boolean | `columns[0][searchable]=true` | Colonne recherchable |
| **columns[N][orderable]** | Boolean | `columns[0][orderable]=true` | Colonne triable |
| **columns[N][search][value]** | String | `columns[2][search][value]=Dell` | Valeur de recherche pour la colonne N |
| **columns[N][search][regex]** | Boolean | `columns[2][search][regex]=false` | Utiliser regex pour la colonne N |

---

## ✅ Exemples pratiques

### Exemple 1 : Page 1 avec recherche
```
GET /api/masterdata/products/?draw=1&start=0&length=20&search[value]=laptop&order[0][column]=2&order[0][dir]=asc
```

### Exemple 2 : Page 2 avec filtres
```
GET /api/masterdata/products/?draw=2&start=20&length=20&Product_Status=ACTIVE&product_family_id=5&order[0][column]=4&order[0][dir]=desc
```

### Exemple 3 : Recherche par colonne spécifique
```
GET /api/masterdata/products/?draw=1&start=0&length=20&columns[1][search][value]=PROD-&columns[1][search][regex]=false&order[0][column]=1&order[0][dir]=asc
```

### Exemple 4 : Tri multiple avec recherche
```
GET /api/masterdata/products/?draw=1&start=0&length=20&search[value]=laptop&order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc
```

### Exemple 5 : Filtres combinés avec DataTable
```
GET /api/masterdata/products/?draw=1&start=0&length=50&Product_Status=ACTIVE&created_at_gte=2024-01-01&search[value]=laptop&order[0][column]=2&order[0][dir]=asc
```

---

## 🔗 Notes importantes

1. **draw** : Doit être incrémenté à chaque requête pour la synchronisation avec le frontend
2. **start** : Index de début (0 = première page, 20 = deuxième page si length=20)
3. **length** : Nombre d'éléments par page (généralement 10, 20, 50, 100)
4. **order[0][column]** : Index de la colonne (0 = première colonne, 1 = deuxième colonne, etc.)
5. **search[value]** : Recherche globale dans tous les champs configurés
6. **columns[N][search][value]** : Recherche spécifique à une colonne
7. Les filtres personnalisés peuvent être combinés avec les paramètres DataTable standards
