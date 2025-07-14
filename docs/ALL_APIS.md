# Documentation des APIs du projet

## 1. masterdata/api/

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

---

## 2. web/api/ (apps.inventory)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET     | /web/api/inventory/ | Liste des inventaires |
| POST    | /web/api/inventory/create/ | Créer un inventaire |
| GET     | /web/api/inventory/<pk>/edit/ | Détail d'un inventaire (édition) |
| POST    | /web/api/inventory/<pk>/update/ | Mettre à jour un inventaire |
| POST    | /web/api/inventory/<pk>/delete/ | Supprimer un inventaire |
| POST    | /web/api/inventory/<pk>/launch/ | Lancer un inventaire |
| POST    | /web/api/inventory/<pk>/cancel/ | Annuler un inventaire |
| GET     | /web/api/inventory/<pk>/detail/ | Détail d'équipe d'inventaire |
| GET     | /web/api/inventory/<int:inventory_id>/warehouse-stats/ | Statistiques des entrepôts d'un inventaire |
| GET     | /web/api/inventory/planning/<int:inventory_id>/warehouses/ | Entrepôts d'un inventaire |
| POST    | /web/api/inventory/planning/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/create/ | Créer des jobs pour un entrepôt |
| GET     | /web/api/warehouse/<int:warehouse_id>/pending-jobs/ | Jobs en attente d'un entrepôt |
| GET     | /web/api/warehouse/<int:warehouse_id>/jobs/ | Tous les jobs d'un entrepôt |
| POST    | /web/api/jobs/validate/ | Valider des jobs |
| POST    | /web/api/jobs/delete/ | Supprimer définitivement un job |
| POST    | /web/api/job/<int:job_id>/remove-emplacements/ | Supprimer des emplacements d'un job |
| POST    | /web/api/job/<int:job_id>/add-emplacements/ | Ajouter des emplacements à un job |
| GET     | /web/api/jobs/list/ | Lister tous les jobs avec détails |
| POST    | /web/api/inventory/<int:inventory_id>/assign-jobs/ | Affecter des jobs à un inventaire |
| GET     | /web/api/assignment-rules/ | Règles d'affectation |
| GET     | /web/api/session/<int:session_id>/assignments/ | Assignations par session |
| POST    | /web/api/jobs/assign-resources/ | Affecter des ressources à des jobs |
| GET     | /web/api/job/<int:job_id>/resources/ | Récupérer les ressources d'un job |
| POST    | /web/api/job/<int:job_id>/remove-resources/ | Retirer des ressources d'un job |
| POST    | /web/api/jobs/ready/ | Marquer un job comme prêt |
| GET     | /web/api/jobs/full-list/ | Liste complète des jobs |
| GET     | /web/api/jobs/pending/ | Lister les jobs en attente |
| POST    | /web/api/jobs/reset-assignments/ | Remettre les assignations de jobs en attente |

---

## 3. api/auth/ (apps.users)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST    | /api/auth/login/ | Authentification (JWT) |
| POST    | /api/auth/login/refresh/ | Rafraîchir le token JWT |
| POST    | /api/auth/logout/ | Déconnexion |
| GET     | /api/auth/mobile-users/ | Liste des utilisateurs mobiles |

---

## 4. mobile/api/ (apps.mobile)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| (À compléter selon les endpoints définis dans apps/mobile/urls.py) |

---

**Remarque :**
- Les méthodes (GET, POST, etc.) sont à vérifier selon l'implémentation réelle de chaque vue.
- Pour plus de détails sur les paramètres, le format des données ou les réponses, se référer au code source ou à la documentation Swagger intégrée (`/swagger/` ou `/redoc/`). 