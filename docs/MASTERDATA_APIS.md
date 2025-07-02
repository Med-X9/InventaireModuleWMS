# Documentation des APIs masterdata

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET     | /masterdata/api/accounts/ | Liste des comptes |
| GET     | /masterdata/api/warehouses/ | Liste des entrepôts |
| GET     | /masterdata/api/warehouse/<warehouse_id>/locations/ | Toutes les locations d'un entrepôt |
| GET     | /masterdata/api/warehouse/<warehouse_id>/job-locations/ | Locations groupées par job pour un entrepôt |
| GET     | /masterdata/api/zones/ | Liste des zones |
| GET     | /masterdata/api/zones/<pk>/ | Détail d'une zone |
| GET     | /masterdata/api/zones/<zone_id>/sous-zones/ | Liste des sous-zones d'une zone |
| GET     | /masterdata/api/sous-zones/ | Liste des sous-zones |
| GET     | /masterdata/api/sous-zones/<pk>/ | Détail d'une sous-zone |
| GET     | /masterdata/api/sous-zones/<sous_zone_id>/locations/ | Locations d'une sous-zone |
| GET     | /masterdata/api/locations/unassigned/ | Emplacements non affectés |
| GET     | /masterdata/api/warehouse/<warehouse_id>/locations/unassigned/ | Emplacements non affectés d'un entrepôt |
| GET     | /masterdata/api/locations/<pk>/ | Détail d'un emplacement |

## GET /masterdata/api/accounts/
- **Description** : Liste des comptes
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
[
  {
    "id": 1,
    "reference": "ACC-001",
    "account_name": "Compte Principal",
    "account_statuts": "ACTIVE",
    "description": "Compte principal de test"
  }
]
```
- **Statuts possibles** : 200

---

## GET /masterdata/api/warehouses/
- **Description** : Liste des entrepôts
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
[
  {
    "id": 1,
    "reference": "WH-001",
    "warehouse_name": "Entrepôt Test",
    "warehouse_type": "CENTRAL",
    "status": "ACTIVE"
  }
]
```
- **Statuts possibles** : 200

---

## GET /masterdata/api/locations/<pk>/
- **Description** : Détail d'un emplacement
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
{
  "id": 1,
  "sous_zone_name": "SousZone Test",
  "location_reference": "L-001",
  "is_active": true,
  "created_at": "2024-07-01T12:00:00Z",
  "updated_at": "2024-07-01T12:00:00Z"
}
```
- **Réponse erreur (404)** :
```json
{
  "error": "Location 9999 non trouvée."
}
```
- **Statuts possibles** : 200, 404

---

## GET /masterdata/api/zones/
- **Description** : Liste des zones
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
[
  {
    "id": 1,
    "zone_code": "Z-001",
    "zone_name": "Zone Test"
  }
]
```
- **Statuts possibles** : 200

---

## GET /masterdata/api/zones/<pk>/
- **Description** : Détail d'une zone
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
{
  "id": 1,
  "zone_code": "Z-001",
  "zone_name": "Zone Test"
}
```
- **Réponse erreur (404)** :
```json
{
  "error": "Zone non trouvée."
}
```
- **Statuts possibles** : 200, 404

---

## GET /masterdata/api/locations/unassigned/
- **Description** : Emplacements non affectés
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
{
  "success": true,
  "message": "Emplacements non affectés récupérés avec succès",
  "data": [
    {
      "id": 2,
      "reference": "LOC-002",
      "location_reference": "L-002",
      "description": "Emplacement libre",
      "sous_zone": {"id": 1, "reference": "SZ-001"},
      "zone": {"id": 1, "reference": "Z-001"},
      "warehouse": {"id": 1, "reference": "WH-001"}
    }
  ],
  "count": 1
}
```
- **Statuts possibles** : 200

---

**Remarque :**
- Pour chaque endpoint, adapter les exemples selon la structure réelle des serializers.
- Pour les endpoints POST/PUT, ajouter un exemple de payload si besoin.
- Pour plus de détails, consulter la documentation Swagger intégrée (`/swagger/`). 