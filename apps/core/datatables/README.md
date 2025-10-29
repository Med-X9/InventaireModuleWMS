# Package DataTable ServerSide

## Vue d'ensemble

Ce package fournit une solution complète pour gérer les tableaux de données avec pagination, tri, recherche, filtres avancés **et export Excel/CSV**. Il est conçu selon les principes SOLID et offre une architecture modulaire et extensible.

## ✨ Nouvelles fonctionnalités

- ✅ **Export Excel (.xlsx)** - Activé par défaut sur toutes les APIs DataTable
- ✅ **Export CSV (.csv)** - Activé par défaut sur toutes les APIs DataTable
- ✅ **Export avec filtres** - Respecte automatiquement tous les filtres, recherches et tris
- ✅ **Nom de fichier avec timestamp** - Format: `export_YYYYMMDD_HHMMSS.xlsx`
- ✅ **Configuration flexible** - Activable/désactivable par API

## Structure du package

```
datatables/
├── __init__.py          # Export des classes principales
├── base.py              # Classes de base et interfaces
├── mixins.py            # Mixins pour les vues (avec export intégré)
├── filters.py           # Filtres personnalisés
├── serializers.py       # Sérialiseurs personnalisés
├── exporters.py         # ⭐ NOUVEAU - Exporteurs Excel/CSV
├── README.md            # Cette documentation
├── EXPORT_USAGE.md      # ⭐ NOUVEAU - Guide d'utilisation de l'export
├── FRONTEND_BACKEND_CONTRACT.md   # Contrat frontend-backend
├── INTEGRATION_VUE3_TS.md         # Guide Vue 3 + TypeScript
└── INTEGRATION_FRONTEND.md        # Guide d'intégration frontend
```

## Composants principaux

### 1. **Interfaces (SOLID)**

#### `IDataTableConfig`
Interface pour la configuration DataTable :
```python
@abstractmethod
def get_search_fields(self) -> List[str]:
    """Retourne les champs de recherche"""

@abstractmethod
def get_order_fields(self) -> List[str]:
    """Retourne les champs de tri"""

@abstractmethod
def get_default_order(self) -> str:
    """Retourne l'ordre par défaut"""

@abstractmethod
def get_page_size(self) -> int:
    """Retourne la taille de page"""
```

#### `IDataTableProcessor`
Interface pour le processeur DataTable :
```python
@abstractmethod
def process(self, request: HttpRequest, queryset: QuerySet) -> JsonResponse:
    """Traite la requête DataTable"""
```

#### `IDataTableFilter`
Interface pour les filtres :
```python
@abstractmethod
def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
    """Applique les filtres au queryset"""
```

#### `IDataTableSerializer`
Interface pour les sérialiseurs :
```python
@abstractmethod
def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
    """Sérialise le queryset"""
```

#### ⭐ `IDataTableExporter` (NOUVEAU)
Interface pour les exporteurs :
```python
@abstractmethod
def export(self, queryset: QuerySet, serializer_class: Optional[type] = None, 
           filename: str = 'export') -> HttpResponse:
    """Exporte le queryset vers un format spécifique"""
```

### 2. **Implémentations**

#### `DataTableConfig`
Configuration centralisée avec validation :
```python
class DataTableConfig(IDataTableConfig):
    def __init__(self, 
                 search_fields: List[str] = None,
                 order_fields: List[str] = None,
                 default_order: str = '-created_at',
                 page_size: int = 25,
                 min_page_size: int = 1,
                 max_page_size: int = 100):
        self.search_fields = search_fields or []
        self.order_fields = order_fields or []
        self.default_order = default_order
        self.page_size = page_size
        self.min_page_size = min_page_size
        self.max_page_size = max_page_size
```

#### `DataTableProcessor`
Processeur principal qui orchestre toutes les opérations :
```python
class DataTableProcessor(IDataTableProcessor):
    def __init__(self, 
                 config: IDataTableConfig,
                 filter_handler: IDataTableFilter = None,
                 serializer_handler: IDataTableSerializer = None):
        self.config = config
        self.filter_handler = filter_handler or DataTableFilter()
        self.serializer_handler = serializer_handler or DataTableSerializer()
    
    def process(self, request: HttpRequest, queryset: QuerySet) -> JsonResponse:
        # 1. Extraction des paramètres
        # 2. Application des filtres
        # 3. Recherche globale
        # 4. Tri
        # 5. Pagination
        # 6. Sérialisation
        # 7. Format de réponse
```

### 3. **Mixins pour les vues**

#### `DataTableMixin`
Mixin de base pour ajouter DataTable à n'importe quelle vue :
```python
class DataTableMixin:
    datatable_config = None
    datatable_filter = None
    datatable_serializer = None
    
    def get_datatable_config(self) -> DataTableConfig:
        """Retourne la configuration DataTable"""
    
    def get_datatable_filter(self) -> IDataTableFilter:
        """Retourne le filtre DataTable"""
    
    def get_datatable_serializer(self) -> IDataTableSerializer:
        """Retourne le sérialiseur DataTable"""
    
    def get_datatable_queryset(self) -> QuerySet:
        """Retourne le queryset pour DataTable"""
    
    def get_datatable_response(self, request: HttpRequest) -> JsonResponse:
        """Traite la requête DataTable"""
```

#### `DataTableListView`
Vue spécialisée pour les listes avec DataTable intégré :
```python
class DataTableListView(DataTableAPIView):
    def get_rest_response(self, request):
        """Réponse REST API pour les listes"""
```

### 4. **Filtres**

#### `DjangoFilterDataTableFilter`
Intégration avec Django Filter :
```python
class DjangoFilterDataTableFilter(IDataTableFilter):
    def __init__(self, filterset_class=None):
        self.filterset_class = filterset_class
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if self.filterset_class:
            filterset = self.filterset_class(request.GET, queryset=queryset)
            return filterset.qs
        return queryset
```

#### `CompositeDataTableFilter`
Combinaison de plusieurs filtres :
```python
class CompositeDataTableFilter(IDataTableFilter):
    def __init__(self):
        self.filters = []
    
    def add_filter(self, filter_handler: IDataTableFilter):
        self.filters.append(filter_handler)
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        for filter_handler in self.filters:
            queryset = filter_handler.apply_filters(request, queryset)
        return queryset
```

#### `DateRangeFilter`
Filtre spécialisé pour les plages de dates :
```python
class DateRangeFilter(IDataTableFilter):
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        start_date = request.GET.get(f'{self.field_name}_start')
        end_date = request.GET.get(f'{self.field_name}_end')
        
        if start_date:
            queryset = queryset.filter(**{f'{self.field_name}__gte': start_date})
        if end_date:
            queryset = queryset.filter(**{f'{self.field_name}__lte': end_date})
        
        return queryset
```

#### `StatusFilter`
Filtre spécialisé pour les statuts :
```python
class StatusFilter(IDataTableFilter):
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        status = request.GET.get(self.field_name)
        if status:
            queryset = queryset.filter(**{self.field_name: status})
        return queryset
```

### 5. **Sérialiseurs**

#### `DataTableSerializer`
Sérialiseur de base utilisant DRF :
```python
class DataTableSerializer(IDataTableSerializer):
    def __init__(self, serializer_class=None):
        self.serializer_class = serializer_class
    
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        if self.serializer_class:
            serializer = self.serializer_class(queryset, many=True)
            return serializer.data
        return list(queryset.values())
```

#### `CustomDataTableSerializer`
Sérialiseur personnalisé :
```python
class CustomDataTableSerializer(IDataTableSerializer):
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        # Logique de sérialisation personnalisée
        return [{"id": obj.id, "label": obj.label} for obj in queryset]
```

#### `NestedDataTableSerializer`
Sérialiseur pour données imbriquées :
```python
class NestedDataTableSerializer(IDataTableSerializer):
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        # Sérialisation avec données imbriquées
        return [{
            "id": obj.id,
            "label": obj.label,
            "warehouse": {
                "id": obj.warehouse.id,
                "name": obj.warehouse.name
            }
        } for obj in queryset]
```

#### `AggregatedDataTableSerializer`
Sérialiseur pour données agrégées :
```python
class AggregatedDataTableSerializer(IDataTableSerializer):
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        # Sérialisation avec données agrégées
        return [{
            "id": obj.id,
            "label": obj.label,
            "total_stocks": obj.total_stocks,
            "completed_count": obj.completed_count
        } for obj in queryset]
```

## Fonctions utilitaires

### `is_datatable_request()`
Détecte si une requête est au format DataTable :
```python
def is_datatable_request(request: HttpRequest) -> bool:
    datatable_params = ['draw', 'start', 'length', 'search[value]']
    return any(param in request.GET for param in datatable_params)
```

### `quick_datatable_view()`
Crée rapidement une vue DataTable :
```python
def quick_datatable_view(model_class,
                        serializer_class=None,
                        filterset_class=None,
                        search_fields=None,
                        order_fields=None,
                        default_order='-created_at',
                        page_size=25):
    """Crée rapidement une vue DataTable"""
```

### `datatable_view()`
Décorateur pour transformer une vue en DataTable :
```python
def datatable_view(config: DataTableConfig = None, 
                  filter_class: Type[IDataTableFilter] = None,
                  serializer_class: Type[IDataTableSerializer] = None):
    """Décorateur pour transformer une vue en DataTable"""
```

## Utilisation

### 1. **Vue simple**
```python
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

### 2. **Vue avec filtres**
```python
class InventaireAvecFiltresView(DataTableListView):
    def get_datatable_config(self):
        return DataTableConfig(
            search_fields=['label', 'reference', 'status'],
            order_fields=['id', 'label', 'date', 'status'],
            default_order='-date',
            page_size=25
        )
    
    def get_datatable_filter(self):
        composite_filter = CompositeDataTableFilter()
        composite_filter.add_filter(DjangoFilterDataTableFilter(InventoryFilter))
        composite_filter.add_filter(DateRangeFilter('date'))
        composite_filter.add_filter(StatusFilter('status'))
        return composite_filter
    
    def get_datatable_queryset(self):
        return Inventory.objects.filter(is_deleted=False)
```

### 3. **Vue rapide**
```python
InventaireRapideView = quick_datatable_view(
    model_class=Inventory,
    serializer_class=InventorySerializer,
    search_fields=['label', 'reference'],
    order_fields=['id', 'label', 'date'],
    default_order='-date',
    page_size=25
)
```

## Formats de réponse

### **DataTable**
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

### **REST API**
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

## Tests

### **Test de tri**
```python
# REST API
GET /api/inventories/?ordering=label
GET /api/inventories/?ordering=-label

# DataTable
GET /api/inventories/?order[0][column]=2&order[0][dir]=asc
GET /api/inventories/?order[0][column]=2&order[0][dir]=desc
```

### **Test de recherche**
```python
# REST API
GET /api/inventories/?search=inventaire

# DataTable
GET /api/inventories/?search[value]=inventaire
```

### **Test de pagination**
```python
# REST API
GET /api/inventories/?page=2&page_size=10

# DataTable
GET /api/inventories/?start=20&length=10
```

## Extensibilité

### **Filtre personnalisé**
```python
class MonFiltrePersonnalise(IDataTableFilter):
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        # Logique de filtrage personnalisée
        if request.GET.get('mon_parametre'):
            queryset = queryset.filter(mon_champ=request.GET['mon_parametre'])
        return queryset
```

### **Sérialiseur personnalisé**
```python
class MonSerialiseurPersonnalise(IDataTableSerializer):
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        # Logique de sérialisation personnalisée
        return [{"id": obj.id, "mon_champ": obj.mon_champ} for obj in queryset]
```

## Performance

### **Optimisations recommandées**
1. Utiliser des index sur les champs de tri
2. Optimiser les requêtes avec `select_related()` et `prefetch_related()`
3. Limiter le nombre de champs de recherche
4. Utiliser la pagination côté serveur
5. Mettre en cache les requêtes fréquentes

### **Exemple d'optimisation**
```python
def get_datatable_queryset(self):
    return Inventory.objects.filter(is_deleted=False)\
        .select_related('warehouse')\
        .prefetch_related('stocks')\
        .annotate(
            total_stocks=Count('stocks'),
            completed_count=Count('stocks', filter=Q(stocks__status='completed'))
        )
```

## Sécurité

### **Validations**
1. Validation des champs de tri autorisés
2. Limitation de la taille de page
3. Protection contre les injections SQL
4. Validation des paramètres de recherche

### **Exemple de validation**
```python
def get_datatable_config(self):
    return DataTableConfig(
        search_fields=['label', 'reference'],  # Champs autorisés uniquement
        order_fields=['id', 'label', 'date'],  # Champs autorisés uniquement
        default_order='-date',
        page_size=25,
        min_page_size=1,    # Limite minimale
        max_page_size=100   # Limite maximale
    )
```

Ce package offre une solution complète et flexible pour gérer les tableaux de données avec toutes les fonctionnalités modernes attendues d'une interface utilisateur professionnelle. 