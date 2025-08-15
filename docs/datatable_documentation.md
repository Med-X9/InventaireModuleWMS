# Documentation DataTable ServerSide

## Vue d'ensemble

Le système DataTable ServerSide de ce projet permet de gérer facilement les tableaux de données avec pagination, tri, recherche et filtres avancés. Il est basé sur les principes SOLID et utilise une architecture modulaire.

## Architecture

### Composants principaux

#### 1. **DataTableConfig** (`apps/core/datatables/base.py`)
Configuration centralisée pour les paramètres DataTable :
- Champs de recherche
- Champs de tri autorisés
- Ordre par défaut
- Taille de page

#### 2. **DataTableProcessor** (`apps/core/datatables/base.py`)
Processeur principal qui gère :
- Extraction des paramètres DataTable
- Application des filtres
- Recherche globale
- Tri
- Pagination
- Sérialisation

#### 3. **DataTableMixin** (`apps/core/datatables/mixins.py`)
Mixin pour ajouter facilement DataTable à n'importe quelle vue.

#### 4. **DataTableListView** (`apps/core/datatables/mixins.py`)
Vue spécialisée pour les listes avec DataTable intégré.

## Utilisation dans les vues d'inventaire

### 1. Vue avec DataTable complet

```python
class InventoryListView(DataTableListView):
    """
    Vue pour lister les inventaires avec pagination et filtres.
    Supporte à la fois l'API REST normale et DataTable ServerSide.
    """
    filterset_class = InventoryFilter
    ordering = '-created_at'
    pagination_class = StandardResultsSetPagination

    def get_datatable_queryset(self):
        """Queryset pour DataTable"""
        return Inventory.objects.filter(is_deleted=False)

    def get_datatable_config(self):
        """Configuration DataTable personnalisée"""
        return DataTableConfig(
            search_fields=['label', 'reference', 'status', 'inventory_type'],
            order_fields=['id', 'reference', 'label', 'date', 'status', 'inventory_type'],
            default_order='-created_at',
            page_size=25,
            min_page_size=1,
            max_page_size=100
        )

    def get_datatable_filter(self):
        """Filtre DataTable avec filtres avancés"""
        composite_filter = CompositeDataTableFilter()
        composite_filter.add_filter(DjangoFilterDataTableFilter(self.filterset_class))
        composite_filter.add_filter(DateRangeFilter('date'))
        composite_filter.add_filter(StatusFilter('status'))
        return composite_filter

    def get_datatable_serializer(self):
        """Sérialiseur DataTable"""
        return DataTableSerializer(InventoryDetailSerializer)
```

### 2. Vue rapide avec `quick_datatable_view`

```python
# Création d'une vue DataTable en une seule ligne
InventoryDataTableView = quick_datatable_view(
    model_class=Inventory,
    serializer_class=InventoryDetailSerializer,
    filterset_class=InventoryFilter,
    search_fields=['label', 'reference', 'status', 'inventory_type'],
    order_fields=['id', 'reference', 'label', 'date', 'status', 'inventory_type'],
    default_order='-created_at',
    page_size=25
)
```

## Fonctionnalités

### 1. **Détection automatique du format de requête**

Le système détecte automatiquement si c'est une requête DataTable ou REST API :

```python
def is_datatable_request(request: HttpRequest) -> bool:
    """Vérifie si c'est une requête DataTable"""
    datatable_params = ['draw', 'start', 'length', 'search[value]']
    return any(param in request.GET for param in datatable_params)
```

### 2. **Recherche globale**

Recherche dans plusieurs champs simultanément :
```python
search_fields = ['label', 'reference', 'status', 'inventory_type']
```

### 3. **Tri avancé**

Support du tri DataTable et REST API :
- **DataTable** : `order[0][column]=2&order[0][dir]=asc`
- **REST API** : `ordering=label` ou `ordering=-label`

### 4. **Filtres composites**

Combinaison de différents types de filtres :
```python
composite_filter = CompositeDataTableFilter()
composite_filter.add_filter(DjangoFilterDataTableFilter(filterset_class))
composite_filter.add_filter(DateRangeFilter('date'))
composite_filter.add_filter(StatusFilter('status'))
```

### 5. **Pagination flexible**

- Taille de page paramétrable
- Limites min/max configurables
- Support des paramètres DataTable et REST

## Formats de réponse

### 1. **Réponse DataTable**

```json
{
    "draw": 1,
    "recordsTotal": 150,
    "recordsFiltered": 25,
    "data": [...],
    "pagination": {
        "current_page": 1,
        "total_pages": 6,
        "has_next": true,
        "has_previous": false
    }
}
```

### 2. **Réponse REST API**

```json
{
    "count": 150,
    "results": [...],
    "next": "http://api/inventories/?page=2",
    "previous": null,
    "pagination": {
        "current_page": 1,
        "total_pages": 6,
        "has_next": true,
        "has_previous": false
    }
}
```

## Configuration avancée

### 1. **Filtres personnalisés**

```python
class CustomDataTableFilter(IDataTableFilter):
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        # Logique de filtrage personnalisée
        if request.GET.get('status'):
            queryset = queryset.filter(status=request.GET['status'])
        return queryset
```

### 2. **Sérialiseurs personnalisés**

```python
class CustomDataTableSerializer(IDataTableSerializer):
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        # Logique de sérialisation personnalisée
        return [{"id": obj.id, "label": obj.label} for obj in queryset]
```

### 3. **Configuration dynamique**

```python
def get_datatable_config(self):
    """Configuration dynamique basée sur l'utilisateur"""
    user = self.request.user
    if user.is_superuser:
        return DataTableConfig(
            search_fields=['label', 'reference', 'status', 'inventory_type', 'created_by'],
            order_fields=['id', 'reference', 'label', 'date', 'status', 'inventory_type', 'created_by'],
            page_size=50
        )
    else:
        return DataTableConfig(
            search_fields=['label', 'reference', 'status'],
            order_fields=['id', 'reference', 'label', 'date'],
            page_size=25
        )
```

## Tests et débogage

### 1. **Vue de test pour le tri**

```python
class InventoryOrderingTestView(APIView):
    """Vue de test pour vérifier le tri"""
    
    def get(self, request):
        """Teste différents paramètres de tri"""
        # Test avec différents paramètres de tri
        test_params = [
            ('ordering=label', 'Tri par label'),
            ('ordering=-label', 'Tri par label décroissant'),
            ('order[0][column]=2&order[0][dir]=asc', 'Tri DataTable colonne 2'),
            ('order[0][column]=2&order[0][dir]=desc', 'Tri DataTable colonne 2 décroissant'),
        ]
        
        # Logique de test...
```

### 2. **Logs de débogage**

Le système inclut des logs détaillés pour le débogage :
```python
logger.debug(f"Tri DataTable - order_column: {order_column}, order_dir: {order_dir}")
logger.debug(f"Champs de tri autorisés: {order_fields}")
```

## Bonnes pratiques

### 1. **Sécurité**
- Validation des champs de tri autorisés
- Limitation de la taille de page
- Protection contre les injections SQL

### 2. **Performance**
- Utilisation d'index sur les champs de tri
- Optimisation des requêtes avec `select_related()` et `prefetch_related()`
- Pagination côté serveur

### 3. **Maintenabilité**
- Configuration centralisée
- Séparation des responsabilités (SOLID)
- Code réutilisable avec les mixins

### 4. **Extensibilité**
- Interfaces pour les filtres et sérialiseurs personnalisés
- Support de nouveaux formats de réponse
- Architecture modulaire

## Exemples d'utilisation

### 1. **Liste simple avec recherche**

```python
class SimpleInventoryView(DataTableListView):
    def get_datatable_config(self):
        return DataTableConfig(
            search_fields=['label', 'reference'],
            order_fields=['id', 'label', 'date'],
            default_order='-date',
            page_size=20
        )
    
    def get_datatable_queryset(self):
        return Inventory.objects.filter(is_deleted=False)
```

### 2. **Liste avec filtres avancés**

```python
class AdvancedInventoryView(DataTableListView):
    def get_datatable_filter(self):
        composite_filter = CompositeDataTableFilter()
        composite_filter.add_filter(DjangoFilterDataTableFilter(InventoryFilter))
        composite_filter.add_filter(DateRangeFilter('date'))
        composite_filter.add_filter(StatusFilter('status'))
        return composite_filter
```

### 3. **Liste avec données agrégées**

```python
class InventoryStatsView(DataTableListView):
    def get_datatable_serializer(self):
        return AggregatedDataTableSerializer(InventoryDetailSerializer)
    
    def get_datatable_queryset(self):
        return Inventory.objects.filter(is_deleted=False).annotate(
            total_stocks=Count('stocks'),
            completed_count=Count('stocks', filter=Q(stocks__status='completed'))
        )
```

## Migration depuis l'ancien système

### 1. **Vue existante**

```python
class OldInventoryView(APIView):
    def get(self, request):
        # Ancienne logique...
```

### 2. **Vue avec DataTable**

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

## Support et maintenance

### 1. **Logs**
- Logs détaillés pour le débogage
- Gestion des erreurs avec try/catch
- Messages d'erreur informatifs

### 2. **Tests**
- Tests unitaires pour chaque composant
- Tests d'intégration pour les vues
- Tests de performance

### 3. **Documentation**
- Documentation des interfaces
- Exemples d'utilisation
- Guide de migration

Cette architecture DataTable offre une solution robuste et flexible pour gérer les tableaux de données avec toutes les fonctionnalités modernes attendues d'une interface utilisateur professionnelle. 