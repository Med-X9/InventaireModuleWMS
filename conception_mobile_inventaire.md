# Conception Application Mobile Inventaire

## Tables Principales

### Table Inventaire
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(50), unique, NOT NULL)
- label (VARCHAR(200), NOT NULL)
- date (DATETIME, NOT NULL)
- status (VARCHAR(50), NOT NULL, valeurs: 'EN PREPARATION', 'EN REALISATION', 'TERMINE', 'CLOTURE')
- inventory_type (VARCHAR(20), NOT NULL, valeurs: 'TOURNANT', 'GENERAL')
- warehouse_web_id (INTEGER, NOT NULL, ID du serveur web)
- en_preparation_status_date (DATETIME, NULL)
- en_realisation_status_date (DATETIME, NULL)
- termine_status_date (DATETIME, NULL)
- cloture_status_date (DATETIME, NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Job
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- status (VARCHAR(10), NOT NULL, valeurs: 'EN ATTENTE', 'AFFECTE', 'PRET', 'TRANSFERT', 'ENTAME', 'VALIDE', 'TERMINE')
- inventory_web_id (INTEGER, NOT NULL, ID du serveur web)
- warehouse_web_id (INTEGER, NOT NULL, ID du serveur web)
- en_attente_date (DATETIME, NULL)
- affecte_date (DATETIME, NULL)
- pret_date (DATETIME, NULL)
- transfert_date (DATETIME, NULL)
- entame_date (DATETIME, NULL)
- valide_date (DATETIME, NULL)
- termine_date (DATETIME, NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table JobDetail
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- location_web_id (INTEGER, NOT NULL, ID du serveur web)
- job_web_id (INTEGER, NOT NULL, ID du serveur web)
- status (VARCHAR(50), NOT NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Assignment
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- status (VARCHAR(10), NOT NULL, valeurs: 'EN ATTENTE', 'AFFECTE', 'PRET', 'TRANSFERT', 'ENTAME', 'TERMINE')
- job_web_id (INTEGER, NOT NULL, ID du serveur web)
- personne_web_id (INTEGER, NULL, ID du serveur web)
- personne_two_web_id (INTEGER, NULL, ID du serveur web)
- counting_web_id (INTEGER, NOT NULL, ID du serveur web)
- transfert_date (DATETIME, NULL)
- entame_date (DATETIME, NULL)
- affecte_date (DATETIME, NULL)
- pret_date (DATETIME, NULL)
- date_start (DATETIME, NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Produit
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- internal_product_code (VARCHAR(20), unique, NOT NULL)
- short_description (VARCHAR(100), NOT NULL)
- barcode (VARCHAR(30), unique, NULL)
- product_group (VARCHAR(10), NULL)
- stock_unit (VARCHAR(30), NOT NULL)
- product_status (VARCHAR(20), NOT NULL, valeurs: 'ACTIVE', 'INACTIVE', 'OBSOLETE')
- product_family_web_id (INTEGER, NOT NULL, ID du serveur web)
- is_variant (BOOLEAN, NOT NULL, default: FALSE)
- n_lot (BOOLEAN, NOT NULL, default: FALSE)
- n_serie (BOOLEAN, NOT NULL, default: FALSE)
- dlc (BOOLEAN, NOT NULL, default: FALSE)
- parent_product_web_id (INTEGER, NULL, ID du serveur web)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Stock
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- location_web_id (INTEGER, NOT NULL, ID du serveur web)
- product_web_id (INTEGER, NULL, ID du serveur web)
- quantity_available (INTEGER, NOT NULL, default: 0)
- quantity_reserved (INTEGER, NULL, default: 0)
- quantity_in_transit (INTEGER, NULL, default: 0)
- quantity_in_receiving (INTEGER, NULL, default: 0)
- unit_of_measure_web_id (INTEGER, NOT NULL, ID du serveur web)
- inventory_web_id (INTEGER, NOT NULL, ID du serveur web)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Emplacement
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- location_reference (VARCHAR(30), unique, NOT NULL)
- sous_zone_web_id (INTEGER, NOT NULL, ID du serveur web)
- location_type_web_id (INTEGER, NOT NULL, ID du serveur web)
- capacity (INTEGER, NULL)
- is_active (BOOLEAN, NOT NULL, default: TRUE)
- description (TEXT, NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Comptage
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- order (INTEGER, NOT NULL)
- count_mode (VARCHAR(100), NOT NULL)
- unit_scanned (BOOLEAN, NOT NULL, default: FALSE)
- entry_quantity (BOOLEAN, NOT NULL, default: FALSE)
- is_variant (BOOLEAN, NOT NULL, default: FALSE)
- n_lot (BOOLEAN, NOT NULL, default: FALSE)
- n_serie (BOOLEAN, NOT NULL, default: FALSE)
- dlc (BOOLEAN, NOT NULL, default: FALSE)
- show_product (BOOLEAN, NOT NULL, default: FALSE)
- stock_situation (BOOLEAN, NOT NULL, default: FALSE)
- quantity_show (BOOLEAN, NOT NULL, default: FALSE)
- inventory_web_id (INTEGER, NOT NULL, ID du serveur web)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Détail Comptage
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- quantity_inventoried (INTEGER, NOT NULL)
- product_web_id (INTEGER, NULL, ID du serveur web)
- dlc (DATE, NULL)
- n_lot (VARCHAR(100), NULL)
- location_web_id (INTEGER, NOT NULL, ID du serveur web)
- counting_web_id (INTEGER, NOT NULL, ID du serveur web)
- last_synced_at (DATETIME, NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Numéro Série
- id (INTEGER, clé primaire, auto-increment)
- web_id (INTEGER, unique, NOT NULL, ID du serveur web)
- reference (VARCHAR(20), unique, NOT NULL)
- n_serie (VARCHAR(100), NULL)
- counting_detail_web_id (INTEGER, NOT NULL, ID du serveur web)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

## Tables de Synchronisation (Obligatoires)

### Table Détail Comptage Mobile
- id (INTEGER, clé primaire, auto-increment)
- detail_id (VARCHAR(50), unique, NOT NULL)
- quantite_comptee (INTEGER, NOT NULL)
- product_web_id (INTEGER, NULL, ID du serveur web)
- location_web_id (INTEGER, NOT NULL, ID du serveur web)
- numero_lot (VARCHAR(100), NULL)
- numero_serie (VARCHAR(100), NULL)
- dlc (DATE, NULL)
- compte_par_web_id (INTEGER, NOT NULL, ID du serveur web - récupéré via API)
- date_comptage (DATETIME, NOT NULL)
- synchronise (BOOLEAN, NOT NULL, default: FALSE)
- donnees_supplementaires (TEXT, NULL, JSON)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Numéro Série Mobile
- id (INTEGER, clé primaire, auto-increment)
- numero_serie (VARCHAR(100), unique, NOT NULL)
- counting_detail_web_id (INTEGER, NOT NULL, ID du serveur web)
- synchronise (BOOLEAN, NOT NULL, default: FALSE)
- timestamp_sync (DATETIME, NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Journal Synchronisation
- id (INTEGER, clé primaire, auto-increment)
- sync_id (VARCHAR(50), unique, NOT NULL)
- type_sync (VARCHAR(20), NOT NULL, valeurs: 'Téléchargement', 'Upload', 'Résolution conflit')
- nb_enregistrements (INTEGER, NOT NULL, default: 0)
- status (VARCHAR(20), NOT NULL, valeurs: 'En attente', 'En cours', 'Terminée', 'Erreur')
- message_erreur (TEXT, NULL)
- date_debut (DATETIME, NOT NULL)
- date_fin (DATETIME, NULL)
- donnees_echangees (TEXT, NULL, JSON)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Conflit Données
- id (INTEGER, clé primaire, auto-increment)
- conflit_id (VARCHAR(50), unique, NOT NULL)
- type_entite (VARCHAR(20), NOT NULL, valeurs: 'Comptage', 'Produit', 'Emplacement')
- web_id_entite (INTEGER, NOT NULL, ID du serveur web)
- donnees_locales (TEXT, NOT NULL, JSON)
- donnees_serveur (TEXT, NOT NULL, JSON)
- status_resolution (VARCHAR(20), NOT NULL, valeurs: 'Non résolu', 'Résolu local', 'Résolu serveur', 'Fusion')
- date_detection (DATETIME, NOT NULL)
- date_resolution (DATETIME, NULL)
- commentaire_resolution (TEXT, NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table File Attente Synchronisation
- id (INTEGER, clé primaire, auto-increment)
- file_id (VARCHAR(50), unique, NOT NULL)
- type_operation (VARCHAR(20), NOT NULL, valeurs: 'Création', 'Modification', 'Suppression')
- type_entite (VARCHAR(20), NOT NULL)
- web_id_entite (INTEGER, NOT NULL, ID du serveur web)
- donnees (TEXT, NOT NULL, JSON)
- priorite (VARCHAR(10), NOT NULL, valeurs: 'Haute', 'Normale', 'Basse')
- tentatives_echouees (INTEGER, NOT NULL, default: 0)
- date_creation (DATETIME, NOT NULL)
- date_prochaine_tentative (DATETIME, NULL)
- status (VARCHAR(20), NOT NULL, valeurs: 'En attente', 'En cours', 'Terminée', 'Échec')
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Configuration Synchronisation
- id (INTEGER, clé primaire, auto-increment)
- config_id (VARCHAR(50), unique, NOT NULL)
- intervalle_sync (INTEGER, NOT NULL, default: 300, unité: secondes)
- max_jours_hors_ligne (INTEGER, NOT NULL, default: 7)
- taille_max_donnees (INTEGER, NOT NULL, default: 10485760, unité: bytes)
- tentatives_max (INTEGER, NOT NULL, default: 3)
- delai_entre_tentatives (INTEGER, NOT NULL, default: 60, unité: secondes)
- timeout_connexion (INTEGER, NOT NULL, default: 30, unité: secondes)
- compression_active (BOOLEAN, NOT NULL, default: TRUE)
- chiffrement_active (BOOLEAN, NOT NULL, default: TRUE)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Statut Connexion
- id (INTEGER, clé primaire, auto-increment)
- statut_id (VARCHAR(50), unique, NOT NULL)
- type_connexion (VARCHAR(20), NOT NULL, valeurs: 'WiFi', 'Mobile', 'Hors ligne')
- force_signal (INTEGER, NULL, unité: dBm)
- adresse_ip (VARCHAR(45), NULL)
- serveur_connecte (VARCHAR(255), NULL)
- derniere_verification (DATETIME, NOT NULL)
- status_connexion (VARCHAR(20), NOT NULL, valeurs: 'Connecté', 'Déconnecté', 'Erreur')
- message_erreur (TEXT, NULL)
- created_at (DATETIME, NOT NULL, auto)
- updated_at (DATETIME, NOT NULL, auto)

### Table Log Synchronisation
- id (INTEGER, clé primaire, auto-increment)
- log_id (VARCHAR(50), unique, NOT NULL)
- niveau (VARCHAR(10), NOT NULL, valeurs: 'Info', 'Warning', 'Error', 'Debug')
- message (TEXT, NOT NULL)
- type_operation (VARCHAR(50), NULL)
- web_id_entite (INTEGER, NULL, ID du serveur web)
- donnees_contexte (TEXT, NULL, JSON)
- timestamp (DATETIME, NOT NULL)
- user_web_id (INTEGER, NULL, ID du serveur web - récupéré via API)
- created_at (DATETIME, NOT NULL, auto)

## Index Recommandés

### Index Principaux
- web_id (toutes les tables principales)
- reference (toutes les tables principales)
- status (tables avec statut)
- created_at (toutes les tables)
- synchronise (tables de synchronisation)

### Index de Performance
- inventory_web_id (Job, Stock)
- job_web_id (JobDetail, Assignment)
- location_web_id (JobDetail, Stock, Détail Comptage)
- product_web_id (Stock, Détail Comptage)
- counting_web_id (Détail Comptage)

## Contraintes de Clés Étrangères

### Relations Principales (basées sur web_id)
- Job.inventory_web_id → Inventaire.web_id
- Job.warehouse_web_id → Warehouse.web_id
- JobDetail.job_web_id → Job.web_id
- JobDetail.location_web_id → Emplacement.web_id
- Assignment.job_web_id → Job.web_id
- Assignment.counting_web_id → Comptage.web_id
- Stock.location_web_id → Emplacement.web_id
- Stock.product_web_id → Produit.web_id
- Détail Comptage.location_web_id → Emplacement.web_id
- Détail Comptage.product_web_id → Produit.web_id
- Détail Comptage.counting_web_id → Comptage.web_id
- Numéro Série.counting_detail_web_id → Détail Comptage.web_id

### Relations de Synchronisation
- Détail Comptage Mobile.product_web_id → Produit.web_id
- Détail Comptage Mobile.location_web_id → Emplacement.web_id
- Numéro Série Mobile.counting_detail_web_id → Détail Comptage.web_id

## Avantages de l'Utilisation des web_id

1. **Cohérence** : Les IDs web garantissent une correspondance exacte entre mobile et serveur
2. **Évite les Conflits** : Pas de problème de références dupliquées ou modifiées
3. **Synchronisation Simplifiée** : Identification unique et stable des entités
4. **Performance** : Requêtes plus rapides avec des entiers au lieu de chaînes
5. **Maintenance** : Plus facile de gérer les relations entre entités
6. **Évolutivité** : Supporte les modifications de références côté serveur
7. **Authentification via API** : Pas de stockage local des utilisateurs et sessions, authentification centralisée
8. **Architecture Cohérente** : Même structure que le web avec les tables Assignment, JobDetail, Counting, et CountingDetail 