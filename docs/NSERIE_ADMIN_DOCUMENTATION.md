# Documentation Admin NSerie

## Vue d'ensemble

L'admin NSerie permet de gérer les numéros de série des produits dans l'interface d'administration Django. Il offre des fonctionnalités complètes pour l'import/export, la recherche, le filtrage et la gestion des numéros de série.

## Configuration Admin

### Classe Admin
```python
@admin.register(NSerie)
class NSerieAdmin(ImportExportModelAdmin):
    resource_class = NSerieResource
    list_display = ('reference', 'n_serie', 'get_product_name', 'status', 'get_product_family', 
                   'date_fabrication', 'date_expiration', 'warranty_end_date', 'is_expired', 'is_warranty_valid')
    list_filter = ('status', 'product__Product_Family', 'date_fabrication', 'date_expiration', 'warranty_end_date')
    search_fields = ('reference', 'n_serie', 'product__Short_Description', 'product__Internal_Product_Code', 'description')
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted', 'reference')
    readonly_fields = ('reference',)
    date_hierarchy = 'created_at'
```

### Colonnes d'affichage (list_display)

1. **reference** : Référence unique du numéro de série
2. **n_serie** : Numéro de série
3. **get_product_name** : Nom du produit associé
4. **status** : Statut du numéro de série
5. **get_product_family** : Famille du produit
6. **date_fabrication** : Date de fabrication
7. **date_expiration** : Date d'expiration
8. **warranty_end_date** : Date de fin de garantie
9. **is_expired** : Calculé - si le numéro de série est expiré
10. **is_warranty_valid** : Calculé - si la garantie est encore valide

### Filtres disponibles (list_filter)

- **Status** : ACTIVE, INACTIVE, USED, EXPIRED, BLOCKED
- **Product Family** : Famille du produit
- **Date fabrication** : Date de fabrication
- **Date expiration** : Date d'expiration
- **Warranty end date** : Date de fin de garantie

### Champs de recherche (search_fields)

- **reference** : Référence du numéro de série
- **n_serie** : Numéro de série
- **product__Short_Description** : Description du produit
- **product__Internal_Product_Code** : Code interne du produit
- **description** : Description du numéro de série

## Fonctionnalités

### 1. Import/Export

L'admin utilise `ImportExportModelAdmin` avec `NSerieResource` pour permettre l'import et l'export des numéros de série.

#### Format d'import/export
```csv
numéro de série,produit,statut,description,date fabrication,date expiration,date fin garantie
NS-001-2024,PROD-001,ACTIVE,Numéro de série de test,2024-01-01,2026-01-01,2025-01-01
```

#### Champs supportés
- **numéro de série** : Numéro de série unique
- **produit** : Code interne du produit (Internal_Product_Code)
- **statut** : ACTIVE, INACTIVE, USED, EXPIRED, BLOCKED
- **description** : Description optionnelle
- **date fabrication** : Date de fabrication (YYYY-MM-DD)
- **date expiration** : Date d'expiration (YYYY-MM-DD)
- **date fin garantie** : Date de fin de garantie (YYYY-MM-DD)

### 2. Méthodes personnalisées

#### get_product_name(obj)
Retourne le nom du produit associé au numéro de série.
```python
def get_product_name(self, obj):
    return obj.product.Short_Description if obj.product else '-'
```

#### get_product_family(obj)
Retourne la famille du produit associé au numéro de série.
```python
def get_product_family(self, obj):
    return obj.product.Product_Family.family_name if obj.product and obj.product.Product_Family else '-'
```

### 3. Propriétés calculées

#### is_expired
Vérifie si le numéro de série est expiré en comparant la date d'expiration avec la date actuelle.
```python
@property
def is_expired(self):
    if self.date_expiration:
        from django.utils import timezone
        return timezone.now().date() > self.date_expiration
    return False
```

#### is_warranty_valid
Vérifie si la garantie est encore valide en comparant la date de fin de garantie avec la date actuelle.
```python
@property
def is_warranty_valid(self):
    if self.warranty_end_date:
        from django.utils import timezone
        return timezone.now().date() <= self.warranty_end_date
    return False
```

## Utilisation

### 1. Accès à l'admin

1. Connectez-vous à l'interface d'administration Django
2. Naviguez vers "Masterdata" > "Numéros de série"
3. Vous verrez la liste de tous les numéros de série

### 2. Création d'un numéro de série

1. Cliquez sur "Ajouter numéro de série"
2. Remplissez les champs :
   - **Numéro de série** : Numéro unique
   - **Produit** : Sélectionnez un produit qui supporte les numéros de série (n_serie=True)
   - **Statut** : ACTIVE par défaut
   - **Description** : Description optionnelle
   - **Date de fabrication** : Date de fabrication
   - **Date d'expiration** : Date d'expiration
   - **Date de fin de garantie** : Date de fin de garantie
3. Cliquez sur "Enregistrer"

### 3. Modification d'un numéro de série

1. Cliquez sur le numéro de série à modifier
2. Modifiez les champs nécessaires
3. Cliquez sur "Enregistrer"

### 4. Suppression d'un numéro de série

1. Sélectionnez le numéro de série à supprimer
2. Cliquez sur "Supprimer"
3. Confirmez la suppression

### 5. Import de numéros de série

1. Cliquez sur "Importer"
2. Sélectionnez le fichier CSV/Excel
3. Vérifiez les données
4. Cliquez sur "Confirmer l'import"

### 6. Export de numéros de série

1. Sélectionnez les numéros de série à exporter
2. Cliquez sur "Exporter"
3. Choisissez le format (CSV, Excel, etc.)

## Filtres et recherche

### Filtrage par statut
- **ACTIVE** : Numéros de série actifs
- **INACTIVE** : Numéros de série inactifs
- **USED** : Numéros de série utilisés
- **EXPIRED** : Numéros de série expirés
- **BLOCKED** : Numéros de série bloqués

### Filtrage par famille de produit
Sélectionnez une famille de produit pour voir tous les numéros de série des produits de cette famille.

### Filtrage par dates
- **Date de fabrication** : Filtre par date de fabrication
- **Date d'expiration** : Filtre par date d'expiration
- **Date de fin de garantie** : Filtre par date de fin de garantie

### Recherche
Utilisez la barre de recherche pour trouver des numéros de série par :
- Numéro de série
- Description du produit
- Code interne du produit
- Description du numéro de série

## Validation

### Validation automatique
- Vérification que le produit supporte les numéros de série (n_serie=True)
- Vérification de l'unicité du numéro de série pour le produit
- Validation des dates (fabrication ≤ expiration)

### Messages d'erreur
- "Ce produit ne supporte pas les numéros de série"
- "Ce numéro de série existe déjà pour ce produit"
- "Date d'expiration doit être postérieure à la date de fabrication"

## Hiérarchie par date

L'admin utilise `date_hierarchy = 'created_at'` pour organiser les numéros de série par date de création, facilitant la navigation temporelle.

## Champs en lecture seule

- **reference** : Généré automatiquement lors de la création

## Champs exclus

- **created_at** : Date de création (géré automatiquement)
- **updated_at** : Date de modification (géré automatiquement)
- **deleted_at** : Date de suppression (géré automatiquement)
- **is_deleted** : Indicateur de suppression (géré automatiquement)
- **reference** : Référence (généré automatiquement)

## Intégration avec l'API Mobile

L'admin NSerie est complètement intégré avec l'API mobile qui récupère les numéros de série via le champ `numeros_serie` dans la réponse API.

## Tests

### Scripts de test disponibles
- `test_nserie_admin_simple.py` : Test de la configuration admin
- `test_nserie_admin.py` : Test complet avec données

### Fonctionnalités testées
- ✅ Enregistrement dans l'admin Django
- ✅ Configuration des colonnes d'affichage
- ✅ Configuration des filtres
- ✅ Configuration des champs de recherche
- ✅ Méthodes personnalisées
- ✅ Propriétés calculées
- ✅ Configuration de la ressource d'import/export

## Conclusion

L'admin NSerie offre une interface complète et intuitive pour la gestion des numéros de série, avec des fonctionnalités avancées d'import/export, de filtrage et de recherche. Il s'intègre parfaitement avec le reste du système et l'API mobile.
