# Guide d'utilisation rapide DataTable

## Démarrage rapide

### 1. **Créer une vue DataTable simple**

```python
from apps.core.datatables.mixins import DataTableListView
from apps.core.datatables.base import DataTableConfig

class MonInventaireView(DataTableListView):
    def get_datatable_config(self):
        return DataTableConfig(
            search_fields=['label', 'reference'],
            order_fields=['id', 'label', 'date'],
            default_order='-date',
            page_size=25
        )
    
    def get_datatable_queryset(self):
        return Inventory.objects.filter(is_deleted=False)
```

### 2. **Créer une vue DataTable en une ligne**

```python
from apps.core.datatables.mixins import quick_datatable_view

MonInventaireView = quick_datatable_view(
    model_class=Inventory,
    serializer_class=InventorySerializer,
    search_fields=['label', 'reference'],
    order_fields=['id', 'label', 'date'],
    default_order='-date',
    page_size=25
)
```

## Paramètres de requête

### **DataTable**
```
GET /api/inventories/?draw=1&start=0&length=25&search[value]=test&order[0][column]=2&order[0][dir]=asc
```

### **REST API**
```
GET /api/inventories/?page=1&page_size=25&search=test&ordering=label
```

## Paramètres de Tri et Filtrage Complets

### Tri sur Tous les Champs

#### Champs de Base
```bash
# Tri par ID
GET /api/inventory/?ordering=id
GET /api/inventory/?ordering=-id

# Tri par référence
GET /api/inventory/?ordering=reference
GET /api/inventory/?ordering=-reference

# Tri par label
GET /api/inventory/?ordering=label
GET /api/inventory/?ordering=-label

# Tri par statut
GET /api/inventory/?ordering=status
GET /api/inventory/?ordering=-status

# Tri par type d'inventaire
GET /api/inventory/?ordering=inventory_type
GET /api/inventory/?ordering=-inventory_type
```

#### Champs de Date
```bash
# Tri par date d'inventaire
GET /api/inventory/?ordering=date
GET /api/inventory/?ordering=-date

# Tri par date de création
GET /api/inventory/?ordering=created_at
GET /api/inventory/?ordering=-created_at

# Tri par date de mise à jour
GET /api/inventory/?ordering=updated_at
GET /api/inventory/?ordering=-updated_at

# Tri par dates de statut
GET /api/inventory/?ordering=en_preparation_status_date
GET /api/inventory/?ordering=-en_preparation_status_date
GET /api/inventory/?ordering=en_realisation_status_date
GET /api/inventory/?ordering=-en_realisation_status_date
GET /api/inventory/?ordering=termine_status_date
GET /api/inventory/?ordering=-termine_status_date
GET /api/inventory/?ordering=cloture_status_date
GET /api/inventory/?ordering=-cloture_status_date
```

### Filtrage sur Tous les Champs

#### Filtres Simples
```bash
# Filtre par ID
GET /api/inventory/?id=1

# Filtre par référence
GET /api/inventory/?reference=INV-2f6f00-9025-1847

# Filtre par label
GET /api/inventory/?label=FM5

# Filtre par statut
GET /api/inventory/?status=EN PREPARATION

# Filtre par type d'inventaire
GET /api/inventory/?inventory_type=GENERAL
```

#### Filtres de Date
```bash
# Date exacte
GET /api/inventory/?date_exact=2025-07-02
GET /api/inventory/?created_at_exact=2025-07-02

# Plage de dates
GET /api/inventory/?date_start=2025-01-01&date_end=2025-12-31
GET /api/inventory/?created_at_start=2025-01-01&created_at_end=2025-12-31

# Dates de statut
GET /api/inventory/?en_preparation_status_date_exact=2025-07-02
GET /api/inventory/?en_realisation_status_date_exact=2025-07-02
GET /api/inventory/?termine_status_date_exact=2025-07-02
GET /api/inventory/?cloture_status_date_exact=2025-07-02
```

#### Filtres Multiples
```bash
# Statuts multiples
GET /api/inventory/?status_in=EN PREPARATION,EN REALISATION,TERMINE

# Types d'inventaire multiples
GET /api/inventory/?inventory_type_in=GENERAL,TOURNANT
```

### Recherche Globale

La recherche globale fonctionne sur tous les champs configurés :
```bash
# Recherche dans tous les champs
GET /api/inventory/?search=FM5
GET /api/inventory/?search=INV-2f6f00
GET /api/inventory/?search=EN PREPARATION
```

### Combinaison de Paramètres

Vous pouvez combiner tous ces paramètres :
```bash
# Tri + Filtre + Pagination
GET /api/inventory/?ordering=-created_at&status=EN PREPARATION&page=1&page_size=10

# Recherche + Tri + Filtre
GET /api/inventory/?search=FM5&ordering=label&inventory_type=GENERAL

# Filtre de date + Tri + Pagination
GET /api/inventory/?date_start=2025-01-01&ordering=-date&page=2&page_size=25

# Filtres multiples + Tri + Recherche
GET /api/inventory/?status_in=EN PREPARATION,EN REALISATION&ordering=created_at&search=INV&page=1&page_size=50
```

### Tri DataTable (Format DataTable)

Pour les requêtes DataTable, utilisez le format :
```bash
# Tri par colonne (index basé sur order_fields)
GET /api/inventory/?order[0][column]=2&order[0][dir]=asc   # Tri par label
GET /api/inventory/?order[0][column]=3&order[0][dir]=desc  # Tri par date
GET /api/inventory/?order[0][column]=4&order[0][dir]=asc   # Tri par status
```

### Pagination

```bash
# Pagination simple
GET /api/inventory/?page=1&page_size=25

# Pagination avec tri
GET /api/inventory/?page=2&page_size=10&ordering=-created_at

# Pagination DataTable
GET /api/inventory/?start=0&length=25&draw=1
```

## Exemples d'Utilisation Pratiques

### 1. Lister les inventaires les plus récents
```bash
GET /api/inventory/?ordering=-created_at&page=1&page_size=10
```

### 2. Filtrer par statut et trier par date
```bash
GET /api/inventory/?status=EN PREPARATION&ordering=date&page=1&page_size=25
```

### 3. Rechercher et trier par référence
```bash
GET /api/inventory/?search=INV&ordering=reference&page=1&page_size=50
```

### 4. Filtre de plage de dates avec tri
```bash
GET /api/inventory/?date_start=2025-01-01&date_end=2025-12-31&ordering=-created_at&page=1&page_size=20
```

### 5. Filtres multiples avec pagination
```bash
GET /api/inventory/?status_in=EN PREPARATION,EN REALISATION&inventory_type=GENERAL&ordering=label&page=1&page_size=15
```

## Configuration des champs

### **Champs de recherche**
```python
search_fields = ['label', 'reference', 'status', 'inventory_type']
```

### **Champs de tri**
```python
order_fields = ['id', 'reference', 'label', 'date', 'status', 'inventory_type']
```

### **Ordre par défaut**
```python
default_order = '-created_at'  # Plus récent en premier
```

## Filtres avancés

### **Filtre avec Django Filter**
```python
def get_datatable_filter(self):
    return DjangoFilterDataTableFilter(InventoryFilter)
```

### **Filtre composite**
```python
def get_datatable_filter(self):
    composite_filter = CompositeDataTableFilter()
    composite_filter.add_filter(DjangoFilterDataTableFilter(InventoryFilter))
    composite_filter.add_filter(DateRangeFilter('date'))
    composite_filter.add_filter(StatusFilter('status'))
    return composite_filter
```

## Formats de réponse

### **DataTable**
```json
{
    "draw": 1,
    "recordsTotal": 150,
    "recordsFiltered": 25,
    "data": [...],
    "pagination": {...}
}
```

### **REST API**
```json
{
    "count": 150,
    "results": [...],
    "next": "http://api/inventories/?page=2",
    "previous": null,
    "pagination": {...}
}
```

## Exemples pratiques

### **Liste d'inventaires avec filtres**
```python
class InventoryListView(DataTableListView):
    filterset_class = InventoryFilter
    
    def get_datatable_config(self):
        return DataTableConfig(
            search_fields=['label', 'reference', 'status'],
            order_fields=['id', 'label', 'date', 'status'],
            default_order='-date',
            page_size=25
        )
    
    def get_datatable_queryset(self):
        return Inventory.objects.filter(is_deleted=False)
    
    def get_datatable_filter(self):
        composite_filter = CompositeDataTableFilter()
        composite_filter.add_filter(DjangoFilterDataTableFilter(self.filterset_class))
        composite_filter.add_filter(DateRangeFilter('date'))
        return composite_filter
```

### **Liste avec données agrégées**
```python
class InventoryStatsView(DataTableListView):
    def get_datatable_queryset(self):
        return Inventory.objects.filter(is_deleted=False).annotate(
            total_stocks=Count('stocks'),
            completed_count=Count('stocks', filter=Q(stocks__status='completed'))
        )
    
    def get_datatable_config(self):
        return DataTableConfig(
            search_fields=['label', 'reference'],
            order_fields=['id', 'label', 'total_stocks', 'completed_count'],
            default_order='-total_stocks',
            page_size=20
        )
```

## Dépannage

### **Problème : Le tri ne fonctionne pas**
```python
# Vérifier que le champ est dans order_fields
order_fields = ['id', 'label', 'date']  # ✅
order_fields = ['id', 'label', 'invalid_field']  # ❌
```

### **Problème : La recherche ne fonctionne pas**
```python
# Vérifier que le champ est dans search_fields
search_fields = ['label', 'reference']  # ✅
search_fields = ['label', 'invalid_field']  # ❌
```

### **Problème : Pagination incorrecte**
```python
# Vérifier les limites de page_size
DataTableConfig(
    page_size=25,
    min_page_size=1,    # Limite minimale
    max_page_size=100   # Limite maximale
)
```

## Tests

### **Tester le tri**
```python
# Test REST API
GET /api/inventories/?ordering=label
GET /api/inventories/?ordering=-label

# Test DataTable
GET /api/inventories/?order[0][column]=2&order[0][dir]=asc
GET /api/inventories/?order[0][column]=2&order[0][dir]=desc
```

### **Tester la recherche**
```python
# Test REST API
GET /api/inventories/?search=inventaire

# Test DataTable
GET /api/inventories/?search[value]=inventaire
```

### **Tester la pagination**
```python
# Test REST API
GET /api/inventories/?page=2&page_size=10

# Test DataTable
GET /api/inventories/?start=20&length=10
```

## Bonnes pratiques

### **1. Sécurité**
- Toujours valider les champs de tri et de recherche
- Limiter la taille de page pour éviter les surcharges
- Utiliser des filtres appropriés pour les permissions

### **2. Performance**
- Utiliser des index sur les champs de tri
- Optimiser les requêtes avec `select_related()` et `prefetch_related()`
- Limiter le nombre de champs de recherche

### **3. Maintenabilité**
- Utiliser des configurations centralisées
- Documenter les champs disponibles
- Tester les fonctionnalités

### **4. Extensibilité**
- Créer des filtres et sérialiseurs personnalisés si nécessaire
- Utiliser les interfaces pour l'extensibilité
- Maintenir la compatibilité avec l'API REST

## Migration depuis l'ancien système

### **Avant (API REST simple)**
```python
class OldInventoryView(APIView):
    def get(self, request):
        queryset = Inventory.objects.all()
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)
```

### **Après (avec DataTable)**
```python
class NewInventoryView(DataTableListView):
    def get_datatable_config(self):
        return DataTableConfig(
            search_fields=['label', 'reference'],
            order_fields=['id', 'label', 'date'],
            default_order='-date'
        )
    
    def get_datatable_queryset(self):
        return Inventory.objects.filter(is_deleted=False)
```

Cette approche permet de maintenir la compatibilité avec l'API REST existante tout en ajoutant les fonctionnalités DataTable. 

# Guide Rapide DataTable ServerSide

## Vue d'ensemble

Ce guide vous montre comment utiliser rapidement le système DataTable ServerSide pour créer des vues avec tri, filtrage, recherche et pagination automatiques.

## Utilisation Rapide avec ServerSideDataTableView

### 1. Configuration Minimale

```python
from apps.core.datatables.mixins import ServerSideDataTableView

class MyListView(ServerSideDataTableView):
    model = MyModel
    serializer_class = MySerializer
    search_fields = ['name', 'description']
    order_fields = ['id', 'name', 'created_at']
```

### 2. Configuration Complète

```python
class InventoryListView(ServerSideDataTableView):
    # Configuration de base
    model = Inventory
    serializer_class = InventorySerializer
    filterset_class = InventoryFilter  # Optionnel - pour django-filter
    
    # Champs de recherche et tri
    search_fields = ['label', 'reference', 'status']
    order_fields = ['id', 'label', 'date', 'created_at', 'status']
    default_order = '-created_at'
    
    # Configuration de pagination
    page_size = 25
    min_page_size = 1
    max_page_size = 100
    
    # Filtres automatiques
    filter_fields = ['status', 'inventory_type']
    date_fields = ['date', 'created_at']
    status_fields = ['status']
```

### 3. Paramètres de Requête Supportés

#### Tri
```bash
# Tri simple
GET /api/inventories/?ordering=label
GET /api/inventories/?ordering=-date
GET /api/inventories/?ordering=created_at

# Tri DataTable
GET /api/inventories/?order[0][column]=2&order[0][dir]=asc
GET /api/inventories/?order[0][column]=3&order[0][dir]=desc
```

#### Recherche
```bash
# Recherche globale
GET /api/inventories/?search=inventaire
```

#### Pagination
```bash
# Pagination REST API
GET /api/inventories/?page=1&page_size=25

# Pagination DataTable
GET /api/inventories/?start=0&length=25&draw=1
```

#### Filtres
```bash
# Filtres simples
GET /api/inventories/?status=active
GET /api/inventories/?inventory_type=general

# Filtres multiples
GET /api/inventories/?status_in=active,pending,completed

# Filtres de date
GET /api/inventories/?date_exact=2024-01-01
GET /api/inventories/?date_start=2024-01-01&date_end=2024-12-31
GET /api/inventories/?created_at_exact=2024-01-01
```

## Exemples d'Utilisation

### Exemple 1 : Vue Simple
```python
class ProductListView(ServerSideDataTableView):
    model = Product
    serializer_class = ProductSerializer
    search_fields = ['name', 'description']
    order_fields = ['id', 'name', 'price', 'created_at']
```

### Exemple 2 : Vue avec Django Filter
```python
class OrderListView(ServerSideDataTableView):
    model = Order
    serializer_class = OrderSerializer
    filterset_class = OrderFilter
    search_fields = ['reference', 'customer_name']
    order_fields = ['id', 'reference', 'total', 'status', 'created_at']
    date_fields = ['created_at', 'updated_at']
    status_fields = ['status']
```

### Exemple 3 : Vue Personnalisée
```python
class CustomInventoryListView(ServerSideDataTableView):
    model = Inventory
    serializer_class = InventorySerializer
    search_fields = ['label', 'reference']
    order_fields = ['id', 'label', 'created_at']
    
    def get_datatable_queryset(self):
        """Queryset personnalisé"""
        return Inventory.objects.filter(is_deleted=False, status='active')
    
    def get_datatable_config(self):
        """Configuration personnalisée"""
        config = super().get_datatable_config()
        config.page_size = 50  # Personnaliser la taille de page
        return config
```

## Fonctionnalités Automatiques

### Tri
- Support des champs de tri configurés dans `order_fields`
- Tri ascendant/descendant avec `ordering=field` ou `ordering=-field`
- Tri DataTable avec `order[0][column]=index&order[0][dir]=asc/desc`

### Recherche
- Recherche globale sur tous les champs dans `search_fields`
- Recherche insensible à la casse
- Support des termes multiples

### Filtrage
- **Django Filter** : Si `filterset_class` est configuré
- **Filtres de Date** : Automatique pour les champs dans `date_fields`
  - `date_exact=YYYY-MM-DD`
  - `date_start=YYYY-MM-DD&date_end=YYYY-MM-DD`
- **Filtres de Statut** : Automatique pour les champs dans `status_fields`
  - `status=value`
  - `status_in=value1,value2`

### Pagination
- Pagination automatique avec `page_size`
- Support des tailles de page personnalisées
- Limites `min_page_size` et `max_page_size`

## Migration depuis l'Ancien Système

### Avant (Ancien Système)
```python
class InventoryListView(DataTableListView):
    def get_datatable_config(self):
        return DataTableConfig(
            search_fields=['label', 'reference'],
            order_fields=['id', 'label', 'created_at'],
            default_order='-created_at',
            page_size=25
        )
    
    def get_datatable_queryset(self):
        return Inventory.objects.all()
    
    def get_datatable_filter(self):
        return DjangoFilterDataTableFilter(InventoryFilter)
```

### Après (Nouveau Système)
```python
class InventoryListView(ServerSideDataTableView):
    model = Inventory
    serializer_class = InventorySerializer
    filterset_class = InventoryFilter
    search_fields = ['label', 'reference']
    order_fields = ['id', 'label', 'created_at']
    default_order = '-created_at'
    page_size = 25
```

## Bonnes Pratiques

### 1. Configuration des Champs
```python
# ✅ Bon - Champs spécifiques
search_fields = ['name', 'email', 'phone']
order_fields = ['id', 'name', 'created_at', 'status']

# ❌ Éviter - Trop de champs
search_fields = ['name', 'email', 'phone', 'address', 'city', 'country', 'zip']
order_fields = ['id', 'name', 'email', 'phone', 'address', 'city', 'country', 'zip']
```

### 2. Optimisation des Requêtes
```python
class OptimizedListView(ServerSideDataTableView):
    model = Order
    serializer_class = OrderSerializer
    
    def get_datatable_queryset(self):
        """Optimisation avec select_related et prefetch_related"""
        return Order.objects.select_related('customer').prefetch_related('items')
```

### 3. Gestion des Erreurs
```python
class SafeListView(ServerSideDataTableView):
    model = Product
    serializer_class = ProductSerializer
    
    def get_datatable_queryset(self):
        """Queryset sécurisé avec gestion d'erreurs"""
        try:
            return Product.objects.filter(is_active=True)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des produits: {e}")
            return Product.objects.none()
```

## Tests

### Test de Tri
```python
def test_ordering(self):
    response = self.client.get('/api/inventories/?ordering=label')
    self.assertEqual(response.status_code, 200)
    
    response = self.client.get('/api/inventories/?ordering=-created_at')
    self.assertEqual(response.status_code, 200)
```

### Test de Recherche
```python
def test_search(self):
    response = self.client.get('/api/inventories/?search=inventaire')
    self.assertEqual(response.status_code, 200)
```

### Test de Filtrage
```python
def test_filtering(self):
    response = self.client.get('/api/inventories/?status=active')
    self.assertEqual(response.status_code, 200)
    
    response = self.client.get('/api/inventories/?date_exact=2024-01-01')
    self.assertEqual(response.status_code, 200)
```

## Dépannage

### Problème : Le tri ne fonctionne pas
**Solution :** Vérifiez que le champ est dans `order_fields`
```python
order_fields = ['id', 'name', 'created_at']  # ✅
# ordering=name fonctionnera
```

### Problème : La recherche ne fonctionne pas
**Solution :** Vérifiez que le champ est dans `search_fields`
```python
search_fields = ['name', 'description']  # ✅
# search=terme fonctionnera
```

### Problème : Les filtres ne fonctionnent pas
**Solution :** Vérifiez la configuration des filtres
```python
# Pour django-filter
filterset_class = MyFilterSet

# Pour filtres automatiques
date_fields = ['created_at', 'updated_at']
status_fields = ['status']
```

### Problème : Performance lente
**Solution :** Optimisez le queryset
```python
def get_datatable_queryset(self):
    return MyModel.objects.select_related('related_model').prefetch_related('many_to_many')
``` 

## Opérateurs de Filtrage Complets

Notre package DataTable supporte **tous les opérateurs Django** pour le filtrage. Voici la liste complète :

### 🔤 **Opérateurs pour les Chaînes (StringFilter)**

#### Opérateurs de Base
```bash
# Correspondance exacte
GET /api/inventory/?label_exact=FM5

# Contient le terme
GET /api/inventory/?label_contains=FM
GET /api/inventory/?reference_contains=INV

# Commence par
GET /api/inventory/?label_startswith=FM
GET /api/inventory/?reference_startswith=INV

# Termine par
GET /api/inventory/?label_endswith=5
GET /api/inventory/?reference_endswith=847
```

#### Opérateurs Insensibles à la Casse
```bash
# Contient (insensible à la casse)
GET /api/inventory/?label_icontains=fm5
GET /api/inventory/?status_icontains=preparation

# Commence par (insensible à la casse)
GET /api/inventory/?label_istartswith=fm
GET /api/inventory/?reference_istartswith=inv

# Termine par (insensible à la casse)
GET /api/inventory/?label_iendswith=5
GET /api/inventory/?reference_iendswith=847
```

#### Expressions Régulières
```bash
# Expression régulière
GET /api/inventory/?label_regex=^FM[0-9]+$
GET /api/inventory/?reference_regex=^INV-.*$

# Expression régulière (insensible à la casse)
GET /api/inventory/?label_iregex=^fm[0-9]+$
GET /api/inventory/?reference_iregex=^inv-.*$
```

### 📅 **Opérateurs pour les Dates (DateFilter)**

#### Opérateurs de Comparaison
```bash
# Date exacte
GET /api/inventory/?created_at_exact=2025-07-02

# Plus grand ou égal
GET /api/inventory/?created_at_gte=2025-01-01

# Plus petit ou égal
GET /api/inventory/?created_at_lte=2025-12-31

# Plus grand que
GET /api/inventory/?created_at_gt=2025-01-01

# Plus petit que
GET /api/inventory/?created_at_lt=2025-12-31
```

#### Plages de Dates
```bash
# Plage de dates (format: date1,date2)
GET /api/inventory/?created_at_range=2025-01-01,2025-12-31
GET /api/inventory/?date_range=2025-07-01,2025-07-31
```

#### Composants de Date
```bash
# Par année
GET /api/inventory/?created_at_year=2025
GET /api/inventory/?date_year=2025

# Par mois
GET /api/inventory/?created_at_month=7
GET /api/inventory/?date_month=7

# Par jour
GET /api/inventory/?created_at_day=2
GET /api/inventory/?date_day=2

# Par semaine
GET /api/inventory/?created_at_week=27
GET /api/inventory/?date_week=27

# Par trimestre
GET /api/inventory/?created_at_quarter=3
GET /api/inventory/?date_quarter=3
```

### 🔢 **Opérateurs pour les Nombres (NumberFilter)**

#### Opérateurs de Comparaison
```bash
# Valeur exacte
GET /api/inventory/?id_exact=1

# Plus grand ou égal
GET /api/inventory/?id_gte=1

# Plus petit ou égal
GET /api/inventory/?id_lte=100

# Plus grand que
GET /api/inventory/?id_gt=0

# Plus petit que
GET /api/inventory/?id_lt=1000
```

#### Plages de Valeurs
```bash
# Plage de valeurs (format: min,max)
GET /api/inventory/?id_range=1,100
GET /api/inventory/?quantity_range=0,1000
```

### 🎯 **Exemples d'Utilisation Avancés**

#### Recherche Complexe de Chaînes
```bash
# Inventaires avec label contenant "FM" et référence commençant par "INV"
GET /api/inventory/?label_contains=FM&reference_startswith=INV

# Inventaires avec statut contenant "PREPARATION" (insensible à la casse)
GET /api/inventory/?status_icontains=preparation

# Inventaires avec référence correspondant à un pattern
GET /api/inventory/?reference_regex=^INV-[a-f0-9]+-[0-9]+-[A-F0-9]+$
```

#### Filtrage Complexe de Dates
```bash
# Inventaires créés en 2025
GET /api/inventory/?created_at_year=2025

# Inventaires créés en juillet 2025
GET /api/inventory/?created_at_year=2025&created_at_month=7

# Inventaires créés entre janvier et juin 2025
GET /api/inventory/?created_at_range=2025-01-01,2025-06-30

# Inventaires avec date d'inventaire en 2025
GET /api/inventory/?date_year=2025
```

#### Combinaisons Complexes
```bash
# Inventaires avec label contenant "FM", créés en 2025, avec ID > 0
GET /api/inventory/?label_contains=FM&created_at_year=2025&id_gt=0

# Inventaires avec référence commençant par "INV", statut "EN PREPARATION", créés en juillet
GET /api/inventory/?reference_startswith=INV&status_exact=EN PREPARATION&created_at_month=7

# Inventaires avec ID entre 1 et 100, créés en 2025, avec label contenant "FM"
GET /api/inventory/?id_range=1,100&created_at_year=2025&label_contains=FM
```

### 🔧 **Configuration des Filtres**

#### Dans votre Vue
```python
class InventoryListView(ServerSideDataTableView):
    # ... configuration de base ...
    
    def get_datatable_filter(self) -> IDataTableFilter:
        """Filtre composite avec tous les opérateurs"""
        composite_filter = CompositeDataTableFilter()
        
        # Filtres de chaînes avec tous les opérateurs
        composite_filter.add_filter(StringFilter([
            'label', 'reference', 'status', 'inventory_type'
        ]))
        
        # Filtres de dates avec tous les opérateurs
        composite_filter.add_filter(DateFilter([
            'date', 'created_at', 'updated_at'
        ]))
        
        # Filtres numériques
        composite_filter.add_filter(NumberFilter(['id']))
        
        return composite_filter
```

#### Filtres Personnalisés
```python
# Filtres de chaînes avec opérateurs limités
composite_filter.add_filter(StringFilter(
    fields=['label', 'reference'],
    allowed_operators=['exact', 'contains', 'startswith']
))

# Filtres de dates avec opérateurs limités
composite_filter.add_filter(DateFilter(
    fields=['created_at', 'date'],
    allowed_operators=['exact', 'gte', 'lte', 'range']
))

# Filtres numériques avec opérateurs limités
composite_filter.add_filter(NumberFilter(
    fields=['id'],
    allowed_operators=['exact', 'gte', 'lte']
))
```

### 📊 **Performance et Optimisation**

#### Bonnes Pratiques
```bash
# ✅ Bon - Utiliser des opérateurs spécifiques
GET /api/inventory/?label_exact=FM5

# ✅ Bon - Utiliser des plages pour les dates
GET /api/inventory/?created_at_range=2025-01-01,2025-12-31

# ❌ Éviter - Recherche trop large
GET /api/inventory/?label_contains=a

# ❌ Éviter - Plages trop larges
GET /api/inventory/?created_at_gte=2020-01-01
```

#### Index Recommandés
```python
# Dans votre modèle Django
class Inventory(models.Model):
    label = models.CharField(max_length=200, db_index=True)
    reference = models.CharField(max_length=50, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    date = models.DateTimeField(db_index=True)
```

### 🛡️ **Sécurité**

#### Validation Automatique
- Tous les opérateurs sont validés automatiquement
- Protection contre les injections SQL
- Limitation des champs de filtrage autorisés
- Logs de sécurité pour les tentatives d'injection

#### Logs de Débogage
```python
# Les filtres appliqués sont loggés automatiquement
logger.debug(f"Filtre StringFilter appliqué: label__contains=FM5")
logger.debug(f"Filtre DateFilter appliqué: created_at__year=2025")
logger.debug(f"Filtre NumberFilter appliqué: id__gte=1")
``` 