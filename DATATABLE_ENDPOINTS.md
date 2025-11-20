## Documentation DataTable / Endpoints API

Ce document recense les principaux `DataTable` de l'application d'inventaire, leurs endpoints API et les champs affichés.

---

## 1. Gestion des inventaires

- **Vue**: `InventoryManagement.vue`  
- **Composable**: `useInventoryManagement`  
- **Service**: `InventoryService`  
- **Endpoint**: `GET /web/api/inventory/`  
- **Chemin API**: `API.endpoints.inventory.base`

**Champs principaux (colonnes)**

- `label` – Libellé de l'inventaire
- `date` – Date de l'inventaire
- `status` – Statut (`EN PREPARATION`, `EN REALISATION`, `TERMINE`, `CLOTURE`)
- `en_preparation_status_date` – Date de passage en préparation
- `en_realisation_status_date` – Date de passage en réalisation
- `termine_status_date` – Date de passage terminé
- `cloture_status_date` – Date de passage clôturé
- `account_name` – Nom du compte

---

## 2. Résultats d'inventaire

- **Vue**: `InventoryResults.vue`  
- **Composable**: `useInventoryResults`  
- **Store**: `resultsStore` (`useResultsStore`)  
- **Service**: service interne du store (utilise `API.endpoints.inventoryResults.base`)  
- **Endpoint générique**: `GET /web/api/inventory-results/…`  
- **Chemin API**: `API.endpoints.inventoryResults.base`

**Champs principaux (colonnes)**

- `id` – Identifiant du résultat
- `article` – Référence article
- `emplacement` – Emplacement
- `resultats` – Résultat final validé

**Champs dynamiques de comptage**

- Tous les champs qui matchent `contage_\d+` (détectés automatiquement), par exemple :
  - `contage_1`
  - `contage_2`
  - `contage_3`

**Champs dynamiques d'écart**

- Tous les champs qui matchent `ecart_\d+_\d+`, par exemple :
  - `ecart_1_2`
  - `ecart_2_3`

---

## 3. Suivi des jobs (Job Tracking)

- **Vue**: `JobTracking.vue`  
- **Composable**: `useJobTracking`  
- **Store**: `jobStore` (`useJobStore`)  
- **Service**: `JobService`  
- **Endpoint**:  
  `GET /web/api/jobs/valid/warehouse/{warehouseId}/inventory/{inventoryId}/`  
- **Méthode service**: `JobService.getAllValidated`

**Champs principaux (colonnes)**

- `emplacement` – Emplacement concerné
- `statut` – Statut du job / assignment (pour ce comptage)
- `dateTransfert` – Date de transfert
- `dateLancement` – Date de lancement
- `dateFin` – Date de fin

---

## 4. Planning des magasins (Planning Management)

- **Vue**: `PlanningManagement.vue`  
- **Composable**: `usePlanningManagement`  
- **Store**: `inventoryStore` (`useInventoryStore`)  
- **Service**: `InventoryService`  
- **Endpoint**:  
  `GET /web/api/inventory/{inventoryId}/warehouse-stats/`  
- **Méthode service**: `InventoryService.getPlanningManagement`

**Champs principaux (colonnes)**

- `store_name` – Nom du magasin / entrepôt
- `teams_count` – Nombre d'équipes
- `jobs_count` – Nombre de jobs
- `reference` – Référence du magasin / entrepôt

---

## 5. Planning des jobs & emplacements

- **Vue**: `Planning.vue`  
- **Composable**: `usePlanning`  
- **Stores**: `jobStore`, `locationStore`, `inventoryStore`, `warehouseStore`  

### 5.1 DataTable « Jobs créés »

- **Service**: `JobService`  
- **Endpoint**:  
  `GET /web/api/inventory/{inventoryId}/warehouse/{warehouseId}/jobs/`  
- **Méthode service**: `JobService.getAll`

**Champs principaux (colonnes)** (`jobsColumns`) :

- `id` – Identifiant du job
- `reference` – Référence du job
- `status` – Statut (`EN ATTENTE`, `VALIDE`, `AFFECTE`, `PRET`, `TRANSFERET`, `TERMINE`, `ENTAME`)
- `locations` – Emplacements (données imbriquées)
  - nested columns :
    - `location_reference`
    - `zone_name`
    - `sous_zone_name`
- `created_at` – Date de création

### 5.2 DataTable « Emplacements disponibles »

- **Service**: `LocationService`  
- **Endpoint**:  
  `GET /masterdata/api/warehouses/{account_id}/warehouse/{warehouse_id}/inventory/{inventory_id}/locations/unassigned/`  
- **Méthode service**: `LocationService.getUnassigned`

**Champs principaux (colonnes)** (`locationsColumns`) :

- `id` – Identifiant de l'emplacement
- `reference` – Référence interne
- `location_reference` – Référence de l'emplacement
- `zone_name` – Zone
- `sous_zone_name` – Sous-zone

---

## 6. Affectation des jobs (Affecter)

- **Vue**: `Affecter.vue`  
- **Composable**: `useAffecter`  
- **Composable DataTable**: `useJobValidatedDataTable`  
- **Store**: `jobStore`  
- **Service**: `JobService`  
- **Endpoint**:  
  `GET /web/api/jobs/valid/warehouse/{warehouseId}/inventory/{inventoryId}/`  
- **Méthode service**: `JobService.getAllValidated`

**Champs principaux (colonnes)** (`columns` dans `useAffecter`) :

- `job` – Référence du job
- `status` – Statut (`AFFECTE`, `VALIDE`, `TRANSFERT`, `PRET`, `ENTAME`)
- `team1` – Équipe 1er comptage (username de session)
- `date1` – Date 1er comptage
- `team2` – Équipe 2e comptage
- `date2` – Date 2e comptage
- `resources` – Ressources affectées (concaténation)
- `locations` – Emplacements (nested, via `nestedData` sur `job`)

---

## 7. Gestion des jobs (vue générique)

- **Vue**: `JobManagement.vue` (module Inventaire + `views/Job/JobManagement.vue`)  
- **Composable**: `useJobManagement`  
- **Store**: `jobStore`  
- **Service**: `JobService`

### 7.1 DataTable « Jobs » (vue simple Inventaire)

- **Endpoint**:  
  `GET /web/api/inventory/{inventoryId}/warehouse/{warehouseId}/jobs/`  
- **Méthode service**: `JobService.getAll`

**Champs principaux (colonnes)** (`useJobManagement`) :

- `id` – Identifiant du job
- `reference` – Référence du job
- `status` – Statut
- `warehouse_name` – Nom de l'entrepôt
- `inventory_reference` – Référence de l'inventaire
- `en_attente_date` – Date de passage en attente
- `valide_date` – Date de validation
- `termine_date` – Date de terminaison

> Remarque : une autre vue `views/Job/JobManagement.vue` encapsule également un `DataTable` avec `useJobManagementPage` (logique similaire, sur les mêmes endpoints).

---

## 8. Locations (DataTable générique)

- **Composable**: `useLocationDataTable`  
- **Store**: `locationStore` (`useLocationStore`)  
- **Service**: `LocationService`  
- **Endpoint**: `GET /masterdata/api/locations/`  
- **Chemin API**: `API.endpoints.location.base`

**Champs principaux** (selon `Location`) :

- `id`
- `reference`
- `location_reference`
- `zone_name`
- `sous_zone_name`

Les colonnes exactes dépendent du `DataTable` qui utilise ce composable (planning, écrans de configuration, etc.).

---

## 9. Ressources (DataTable générique)

- **Composable**: `useResourceDataTable`  
- **Store**: `resourceStore` (`useResourceStore`)  
- **Service**: `ResourceService`  
- **Endpoint**: `GET masterdata/api/ressources`  
- **Chemin API**: `API.endpoints.resource.base`

**Champs principaux** (selon `Resource`) :

- `id`
- `reference`
- `ressource_nom`

Là aussi, les colonnes exactes sont définies dans les vues qui consomment ce composable.

---

## 10. Notes

- Tous les DataTable serveur utilisent soit:
  - `useBackendDataTable` (intégré à un store Pinia et à un service spécifique), soit  
  - `useGenericDataTable` avec `fetchAction` du store (`fetchInventories`, `fetchJobs`, `fetchLocations`, `fetchResources`, etc.).
- Les paramètres DataTable (pagination, tri, filtres, recherche globale) sont convertis au format standard `draw/start/length/columns[..]` avant d'être envoyés aux endpoints.


