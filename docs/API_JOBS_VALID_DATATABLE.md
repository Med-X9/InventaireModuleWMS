# 📊 API DataTable - Jobs

## 🎯 1. Jobs Valid / Detail Complets

**Endpoint :**
```
GET /api/jobs/valid/warehouse/{warehouse_id}/inventory/{inventory_id}/
```

**Paramètres DataTable :**
```
?draw=1&start=0&length=20
```

**Paramètres optionnels :**
```
?search=terme                              # Recherche globale
?ordering=-created_at                      # Tri par champ
?order[0][column]=2&order[0][dir]=asc      # Tri multi-colonnes
?status=valide                              # Filtrer par statut
?emplacement_contains=BAT                   # Filtrer par emplacement
?session=admin                              # Filtrer par session
```

**Réponse JSON :**
```json
{
  "draw": 1,
  "recordsTotal": 150,
  "recordsFiltered": 45,
  "data": [
    {
      "id": 123,
      "reference": "JOB-2024-001",
      "status": "VALIDE",
      "emplacements": [
        {
          "id": 1,
          "reference": "LOC-ABC-001",
          "sous_zone": {"id": 5, "name": "Sous-zone A"},
          "zone": {"id": 2, "name": "Zone 1"}
        }
      ],
      "assignments": [
        {
          "counting_order": 1,
          "status": "AFFECTE",
          "session": {"id": 10, "username": "admin"},
          "date_start": "2024-03-15T10:00:00Z"
        }
      ],
      "ressources": [
        {
          "id": 1,
          "reference": "PDA-01",
          "quantity": 2
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## 🎯 2. Jobs Pending (En Attente)

**Endpoint :**
```
GET /api/jobs/pending/
```

**Paramètres DataTable :**
```
?draw=1&start=0&length=20
```

**Paramètres optionnels :**
```
?search=JOB-001
?ordering=-created_at
?reference_contains=2024
```

**Réponse JSON :**
```json
{
  "draw": 1,
  "recordsTotal": 50,
  "recordsFiltered": 10,
  "data": [
    {
      "id": 456,
      "reference": "JOB-2024-002",
      "status": "EN ATTENTE",
      "emplacements": [...],
      "assignments": [...],
      "ressources": [...]
    }
  ],
  "pagination": {...}
}
```

---

## 🎯 3. Jobs avec Locations

**Endpoint :**
```
GET /api/jobs/list/
```

**Paramètres DataTable :**
```
?draw=1&start=0&length=20
```

**Paramètres optionnels :**
```
?search=terme
?ordering=reference
?status=valide
?location_reference=LOC-001
?created_at_gte=2024-01-01
```

**Réponse JSON :**
```json
{
  "draw": 1,
  "recordsTotal": 200,
  "recordsFiltered": 75,
  "data": [
    {
      "id": 789,
      "reference": "JOB-2024-003",
      "status": "AFFECTE",
      "created_at": "2024-03-15T10:00:00Z",
      "locations": [
        {
          "id": 1,
          "location_id": 10,
          "reference": "JD-001",
          "location_reference": "LOC-ABC-001",
          "sous_zone": {...},
          "zone": {...},
          "status": "EN ATTENTE"
        }
      ]
    }
  ],
  "pagination": {...}
}
```

---

## 🎯 4. Jobs par Warehouse et Inventory

**Endpoint :**
```
GET /api/inventory/{inventory_id}/warehouse/{warehouse_id}/jobs/
```

**Paramètres DataTable :**
```
?draw=1&start=0&length=20
```

**Paramètres optionnels :**
```
?search=terme
?ordering=-created_at
?status=pret
```

**Réponse JSON :**
```json
{
  "draw": 1,
  "recordsTotal": 120,
  "recordsFiltered": 30,
  "data": [
    {
      "id": 1011,
      "reference": "JOB-2024-004",
      "status": "PRET",
      "created_at": "2024-03-14T08:00:00Z",
      "locations": [...]
    }
  ],
  "pagination": {...}
}
```

---

## 🎯 5. Jobs Pending pour Warehouse (Références)

**Endpoint :**
```
GET /api/inventory/{warehouse_id}/pending-jobs/
```

**Paramètres DataTable :**
```
?draw=1&start=0&length=20
```

**Paramètres optionnels :**
```
?search=inventaire
?ordering=-created_at
?inventory_reference=INV-2024-001
?inventory_label=Inventaire
?warehouse_name=Entrepôt
?created_at_gte=2024-01-01
?emplacements_count_min=5
```

**Réponse JSON :**
```json
{
  "draw": 1,
  "recordsTotal": 80,
  "recordsFiltered": 25,
  "data": [
    {
      "id": 1213,
      "reference": "JOB-2024-005",
      "status": "EN ATTENTE",
      "created_at": "2024-03-16T09:00:00Z",
      "inventory_id": 25,
      "inventory_reference": "INV-2024-001",
      "inventory_label": "Inventaire Mars 2024",
      "warehouse_id": 697,
      "warehouse_reference": "WH-001",
      "warehouse_name": "Entrepôt Principal",
      "emplacements_count": 10,
      "assignments_count": 2
    }
  ],
  "pagination": {...}
}
```

---

## 📋 Paramètres DataTable universels

| Paramètre | Type | Description |
|-----------|------|-------------|
| `draw` | int | Numéro de synchronisation (obligatoire) |
| `start` | int | Index de début (0 = page 1) |
| `length` | int | Nombre d'éléments par page (1-100) |
| `search` | string | Recherche globale |
| `ordering` | string | Tri simple (-champ pour desc) |
| `order[0][column]` | int | Index colonne pour tri DataTable |
| `order[0][dir]` | string | Direction (asc/desc) |

---

## 🎨 Exemples d'URL complètes

```bash
# Exemple 1 : Jobs Valid - Page 1
GET http://192.168.11.131:9000/web/api/jobs/valid/warehouse/697/inventory/25/?draw=1&start=0&length=20

# Exemple 2 : Jobs Valid - Avec recherche
GET http://192.168.11.131:9000/web/api/jobs/valid/warehouse/697/inventory/25/?draw=1&start=0&length=20&search=JOB-001

# Exemple 3 : Jobs Valid - Avec tri
GET http://192.168.11.131:9000/web/api/jobs/valid/warehouse/697/inventory/25/?draw=1&start=0&length=20&ordering=-created_at

# Exemple 4 : Jobs Valid - Avec filtres
GET http://192.168.11.131:9000/web/api/jobs/valid/warehouse/697/inventory/25/?draw=1&start=0&length=20&status=valide&emplacement_contains=BAT

# Exemple 5 : Jobs Valid - Pagination page 2
GET http://192.168.11.131:9000/web/api/jobs/valid/warehouse/697/inventory/25/?draw=2&start=20&length=20

# Exemple 6 : Jobs Pending
GET http://192.168.11.131:9000/web/api/jobs/pending/?draw=1&start=0&length=20

# Exemple 7 : Jobs List (avec locations)
GET http://192.168.11.131:9000/web/api/jobs/list/?draw=1&start=0&length=20

# Exemple 8 : Jobs par Warehouse
GET http://192.168.11.131:9000/web/api/inventory/25/warehouse/697/jobs/?draw=1&start=0&length=20
```

