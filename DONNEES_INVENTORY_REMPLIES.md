# Documentation des Données Inventory Créées

## 📋 Vue d'ensemble

Ce document décrit toutes les données créées dans l'application **inventory** avec le script `populate_inventory_data.py`.

## 🚀 Utilisation du script

```bash
python populate_inventory_data.py
```

Le script va:
1. Supprimer toutes les anciennes données de l'app inventory
2. Créer des données complètes avec tous les cas possibles
3. Afficher un résumé détaillé

---

## 📊 Données créées

### 👥 Utilisateurs (3)

| Username | Type | Nom | Prénom | Compte associé |
|----------|------|-----|--------|----------------|
| mobile_user1 | Mobile | Durand | Marc | Compte actif de masterdata |
| mobile_user2 | Mobile | Lefebvre | Julie | Compte actif de masterdata |
| mobile_user3 | Mobile | Moreau | Thomas | Compte actif de masterdata |

**Mot de passe:** `password123`

**Note importante:** Chaque utilisateur est associé à un compte (Account) actif de masterdata pour permettre la synchronisation mobile.

### 👤 Personnes (6)
Utilisées pour les affectations:
- Dupont Jean
- Martin Marie
- Bernard Pierre
- Dubois Sophie
- Thomas Luc
- Robert Claire

### 📦 Inventaires (5)

| Label | Type | Statut | Description |
|-------|------|--------|-------------|
| Inventaire Général 2025 Q1 | GENERAL | EN PREPARATION | Inventaire en cours de préparation |
| Inventaire Tournant Zone A - Janvier | TOURNANT | EN REALISATION | En cours de réalisation |
| Inventaire Général 2024 Q4 | GENERAL | TERMINE | Terminé |
| Inventaire Tournant Zone B - Décembre | TOURNANT | CLOTURE | Clôturé |
| Inventaire Général Annuel 2025 | GENERAL | EN PREPARATION | En préparation |

**Cas couverts:**
- ✅ 2 inventaires EN PREPARATION
- ✅ 1 inventaire EN REALISATION
- ✅ 1 inventaire TERMINE
- ✅ 1 inventaire CLOTURE
- ✅ Type GENERAL et TOURNANT

---

### ⚙️ Settings (9)
Liens entre comptes, entrepôts et inventaires pour configurer les inventaires.

---

### 📅 Plannings (3)
Planifications avec dates de début et de fin pour les 3 premiers inventaires.

---

### 🔢 Comptages (20)

#### Configuration complète des comptages

**Modes de comptage valides dans le système:**
- `"image de stock"` - Premier comptage basé sur l'image de stock
- `"en vrac"` - Comptage en vrac (sans obligation de produit)
- `"par article"` - Comptage par article (produit obligatoire)

| # | Mode de comptage | Ordre | Options activées | Description |
|---|-----------------|-------|------------------|-------------|
| 1 | image de stock | 1 | show_product, stock_situation, quantity_show | Image de stock - 1er comptage |
| 2 | en vrac | 2 | entry_quantity | Comptage en vrac simple |
| 3 | par article | 3 | N° LOT, show_product, quantity_show | Par article avec lots |
| 4 | par article | 1 | N° SÉRIE, unit_scanned, show_product, stock_situation | Par article avec séries |
| 5 | par article | 2 | DLC, show_product, quantity_show | Par article avec DLC |
| 6 | par article | 3 | VARIANTE, show_product, stock_situation, quantity_show | Par article avec variantes |
| 7 | par article | 1 | N° LOT + DLC, show_product, stock_situation, quantity_show | Par article lot + DLC |
| 8 | par article | 2 | N° SÉRIE, unit_scanned, stock_situation | Par article série + scan |
| 9 | en vrac | 3 | entry_quantity | Comptage aveugle (sans affichage) |
| 10 | par article | 1 | TOUTES | Comptage complet (toutes options) |

**Cas couverts:**
- ✅ 3 modes de comptage: `image de stock`, `en vrac`, `par article`
- ✅ 4 comptages avec N° SÉRIE
- ✅ 3 comptages avec N° LOT
- ✅ 3 comptages avec DLC
- ✅ 2 comptages avec VARIANTES
- ✅ Différentes combinaisons d'options
- ✅ Options: `unit_scanned`, `entry_quantity`, `show_product`, `stock_situation`, `quantity_show`

---

### 💼 Jobs (8)

Tous les statuts possibles sont représentés:

| Statut | Description | Dates remplies |
|--------|-------------|----------------|
| EN ATTENTE | Job en attente | en_attente_date |
| AFFECTE | Job affecté | en_attente_date, affecte_date |
| PRET | Prêt à démarrer | + pret_date |
| TRANSFERT | En transfert | + transfert_date |
| ENTAME | Commencé | + entame_date |
| VALIDE | Validé | + valide_date |
| TERMINE | Terminé | + termine_date |
| SAISIE MANUELLE | Saisie manuelle | saisie_manuelle_date |

**Cas couverts:**
- ✅ Tous les statuts possibles (8)
- ✅ Toutes les dates de transition remplies
- ✅ Liens avec différents entrepôts et inventaires

---

### 📋 JobDetails (15)

Détails des jobs par emplacement:
- 15 JobDetails créés pour les 5 premiers jobs
- 3 détails par job
- Statuts: EN ATTENTE et TERMINE
- Liens avec emplacements et comptages

---

### 👥 Affectations (6)

| Job | Personnes | Statut | Session |
|-----|-----------|--------|---------|
| JOB-xxx | Dupont + Martin | EN ATTENTE | mobile_user1 |
| JOB-xxx | Martin | AFFECTE | - |
| JOB-xxx | Bernard + Dubois | PRET | - |
| JOB-xxx | Dubois | TRANSFERT | mobile_user2 |
| JOB-xxx | Thomas + Robert | ENTAME | - |
| JOB-xxx | Robert | TERMINE | - |

**Cas couverts:**
- ✅ Affectations avec 1 personne
- ✅ Affectations avec 2 personnes
- ✅ Affectations avec et sans session utilisateur
- ✅ Tous les statuts d'affectation

---

### 🔧 Ressources

#### Types de ressources
- Terminal Mobile

#### Ressources (4)
- PDA
- Nacelle
- Transpalette
- Gilet fluo

**Utilisation:**
- 4 JobDetailRessources (liens jobs ↔ ressources)
- 6 InventoryDetailRessources (liens inventaires ↔ ressources)

---

### 📊 CountingDetails (50)

50 détails de comptage créés avec:
- **Produits variés** (5 produits différents)
- **Emplacements variés** (10 emplacements)
- **Quantités diverses** (de 1 à 96)
- **N° de lot** pour les comptages qui le requièrent
- **DLC** pour les comptages qui le requièrent
- **last_synced_at** pour simuler la synchronisation

**Produits utilisés:**
- Peluche DDl & DDa Bébé 30cm
- MAGIC COLOURSTICK METAL BOX
- CAMALEON WEB BOX (17,5x17,5x6c)
- Boîte à tartines TM
- Brosse à cheveux TM

---

### 🔢 NSerieInventory

Numéros de série d'inventaire pour les comptages qui nécessitent le suivi par numéro de série.

**Note:** Le script tente de créer des numéros de série uniquement si:
- Le comptage a l'option `n_serie = True`
- Le produit a l'option `n_serie = True`

---

### ⚠️ EcartComptage

Le script crée automatiquement des écarts si:
- Le même produit est compté plusieurs fois au même emplacement
- Les quantités sont différentes

**Cas couverts:**
- Écarts non résolus (`resolved = False`)
- Écarts résolus (`resolved = True`) avec justification

---

## 🎯 Cas d'utilisation couverts

### 1. Cycle de vie complet d'un inventaire
```
EN PREPARATION → EN REALISATION → TERMINE → CLOTURE
```

### 2. Cycle de vie complet d'un job
```
EN ATTENTE → AFFECTE → PRET → TRANSFERT → ENTAME → VALIDE → TERMINE
```

### 3. Types de comptage
- ✅ **image de stock** - Premier comptage basé sur l'image de stock
- ✅ **en vrac** - Comptage en vrac (article non obligatoire)
- ✅ **par article** - Comptage par article (article obligatoire)
- ✅ Comptage avec traçabilité (lot, série, DLC)
- ✅ Comptage avec variantes
- ✅ Comptage aveugle (sans affichage produit)
- ✅ Comptage complet (toutes options combinées)

### 4. Affectations
- ✅ Affectation avec 1 opérateur
- ✅ Affectation avec 2 opérateurs (binôme)
- ✅ Affectation avec session mobile
- ✅ Affectation sans session

### 5. Ressources
- ✅ Ressources affectées aux jobs
- ✅ Ressources affectées aux inventaires
- ✅ Quantités de ressources

---

## 🔍 Vérification des données

### Via l'admin Django
```
http://localhost:8000/admin/
```

Vous pouvez consulter:
- **Inventory** → inventory
- **Settings** → inventory
- **Comptages** (Counting) → inventory
- **Jobs** → inventory
- **Affectations** (Assigment) → inventory
- **CountingDetails** → inventory

### Via l'API

#### Lister les inventaires
```bash
GET /api/inventory/
```

#### Lister les jobs
```bash
GET /api/jobs/
```

#### Lister les comptages
```bash
GET /api/countings/
```

---

## 📝 Scripts de test

Ces données peuvent être utilisées pour tester:

1. **L'API mobile de comptage**
   ```bash
   python test_mobile_counting_detail_api.py
   ```

2. **L'API d'affectation**
   ```bash
   python test_assignment_api_simple.py
   ```

3. **L'API de synchronisation**
   ```bash
   python test_sync_debug.py
   ```

---

## 🔄 Réinitialisation

Pour recréer les données à partir de zéro:

```bash
python populate_inventory_data.py
```

**⚠️ Attention:** Ceci supprime TOUTES les données de l'app inventory avant de les recréer.

---

## 📌 Points importants

1. **Les références sont uniques** - Chaque objet a une référence unique générée automatiquement

2. **Les dates sont cohérentes** - Les dates de transition respectent l'ordre chronologique

3. **Les relations sont complètes** - Tous les liens FK sont correctement établis

4. **Les données sont réalistes** - Utilisation de vrais produits et emplacements de la base masterdata

5. **Tous les cas sont couverts** - Le script crée des exemples pour chaque configuration possible

---

## 🐛 Dépannage

### Problème: "ERREUR: la valeur d'une clé dupliquée"
**Solution:** Relancer le script, il nettoie automatiquement les anciennes données

### Problème: "Aucun produit actif trouvé"
**Solution:** Vérifier que la base masterdata contient des produits avec `Product_Status = 'ACTIVE'`

### Problème: "Aucun emplacement actif trouvé"
**Solution:** Vérifier que la base masterdata contient des emplacements avec `is_active = True`

---

## 📚 Ressources

- **Script principal:** `populate_inventory_data.py`
- **Modèles inventory:** `apps/inventory/models.py`
- **Modèles masterdata:** `apps/masterdata/models.py`

---

**Date de création:** 2025-10-08  
**Version:** 1.0

