"""
Package QueryModel - Export des classes principales

Ce package fournit une solution complète pour gérer les tableaux de données avec pagination,
tri, recherche et filtres avancés via QueryModel (format AG-Grid compatible).
Il est conçu selon les principes SOLID, KISS et DRY.

PRINCIPES:
- SOLID : Architecture modulaire et extensible
- KISS : Simplicité et facilité d'utilisation
- DRY : Réutilisation maximale du code

VERSION: 2.0.0
"""
__version__ = "2.0.0"

# =============================================================================
# EXPORT QUERY MODEL (Support QueryModel uniquement)
# =============================================================================

# QueryModel Models - Modèles de données
from .models import (
    SortDirection,            # Direction de tri (asc/desc)
    FilterType,               # Types de filtres (text, number, date, set)
    FilterOperator,           # Opérateurs de filtres (equals, contains, etc.)
    SortModelItem,            # Modèle de tri (sort)
    FilterModelItem,          # Modèle de filtre (filters)
    QueryModel                # Modèle de requête complet (page, pageSize, search, sort, filters)
)

# QueryModel Engines - Moteurs de traitement
from .engines import (
    FilterEngine,             # Moteur de filtrage (QueryModel → Q())
    SortEngine,               # Moteur de tri multi-colonnes
    PaginationEngine          # Moteur de pagination (infinite scroll)
)

# QueryModel Operators - Registry d'opérateurs
from .operators import (
    OperatorRegistry          # Registry pour convertir opérateurs AG-Grid → Django ORM
)

# QueryModel DataSource - Sources de données
from .datasource import (
    IDataSource,              # Interface pour sources de données
    QuerySetDataSource,       # DataSource pour QuerySet Django
    ListDataSource,           # DataSource pour liste de dictionnaires
    CallableDataSource,       # DataSource pour fonction callable
    DataSourceFactory         # Factory pour créer des DataSource
)

# QueryModel Response - Modèle de réponse
from .response import (
    ResponseModel             # Modèle de réponse compatible AG-Grid
)

# QueryModel Mixin - Mixin pour intégration simple
from .mixins import (
    QueryModelMixin,          # Mixin pour ajouter support QueryModel
    QueryModelView,           # Vue complète avec support QueryModel
    ServerSideDataTableView   # Alias de compatibilité (utilise QueryModelView)
)

# Request Handler - Détection et extraction de paramètres
from .request_handler import (
    RequestFormatDetector,    # Détecteur de format QueryModel
    RequestParameterExtractor # Extracteur de paramètres
)

# =============================================================================
# EXPORT PUBLIC - Toutes les classes et fonctions disponibles
# =============================================================================

__all__ = [
    # =====================================================================
    # QUERY MODEL (Support QueryModel uniquement)
    # =====================================================================
    'SortDirection',                 # Direction de tri (asc/desc)
    'FilterType',                    # Types de filtres (text, number, date, set)
    'FilterOperator',                # Opérateurs de filtres (equals, contains, etc.)
    'SortModelItem',                 # Modèle de tri (sort)
    'FilterModelItem',               # Modèle de filtre (filters)
    'QueryModel',                    # Modèle de requête complet
    'FilterEngine',                  # Moteur de filtrage
    'SortEngine',                    # Moteur de tri multi-colonnes
    'PaginationEngine',              # Moteur de pagination (infinite scroll)
    'OperatorRegistry',              # Registry d'opérateurs
    'IDataSource',                   # Interface pour sources de données
    'QuerySetDataSource',            # DataSource pour QuerySet
    'ListDataSource',                # DataSource pour liste de dicts
    'CallableDataSource',            # DataSource pour fonction callable
    'DataSourceFactory',             # Factory pour créer des DataSource
    'ResponseModel',                 # Modèle de réponse QueryModel
    'QueryModelMixin',               # Mixin pour support QueryModel
    'QueryModelView',                # Vue complète avec support QueryModel
    'ServerSideDataTableView',       # Alias de compatibilité
    'RequestFormatDetector',         # Détecteur de format QueryModel
    'RequestParameterExtractor',     # Extracteur de paramètres
]

# =============================================================================
# VERSION ET MÉTADONNÉES
# =============================================================================

__version__ = "2.0.0"
__author__ = "Équipe de développement"
__description__ = "Package QueryModel pour Django REST Framework"
__keywords__ = ["querymodel", "django", "rest", "api", "pagination", "sorting", "filtering", "ag-grid"]

# =============================================================================
# DOCUMENTATION RAPIDE
# =============================================================================

"""
EXEMPLES D'UTILISATION:

1. Vue simple avec QueryModel:
    from apps.core.datatables import QueryModelView
    
    class MonInventaireView(QueryModelView):
        model = Inventory
        serializer_class = InventorySerializer
        column_field_mapping = {
            'id': 'id',
            'label': 'label',
            'date': 'date'
        }

2. Vue avec liste de dictionnaires:
    from apps.core.datatables import QueryModelMixin, APIView
    from apps.core.datatables.datasource import DataSourceFactory
    
    class MyView(QueryModelMixin, APIView):
        serializer_class = MySerializer
        column_field_mapping = {
            'id': 'id',
            'name': 'name'
        }
        
        def get_data_source(self):
            data_list = self.service.get_data()
            return DataSourceFactory.create(data_list)

FORMAT DE RÉPONSE QueryModel:

{
    "success": true,
    "rowData": [...],
    "rowCount": 150
}

PARAMÈTRES DE REQUÊTE SUPPORTÉS:

1. POST avec JSON body:
    POST /api/inventories/
    {
        "page": 1,
        "pageSize": 10,
        "search": "ink",
        "sort": [{"colId": "label", "sort": "asc"}],
        "filters": {
            "status": ["active", "pending"],
            "label": {"type": "text", "operator": "contains", "value": "test"}
        }
    }

2. GET avec query params:
    GET /api/inventories/?page=1&pageSize=10&search=ink&sort=[{"colId":"label","sort":"asc"}]&filters={"status":["active","pending"]}

PRINCIPES ARCHITECTURAUX:

- SOLID: Chaque classe respecte les principes SOLID
- DRY: Évite la duplication de code avec les mixins
- Séparation des responsabilités: Configuration, filtrage, sérialisation séparés
- Extensibilité: Interfaces pour créer des filtres et sérialiseurs personnalisés
- Performance: Optimisations de requête intégrées
- Sécurité: Validation des paramètres et protection contre les injections
"""
