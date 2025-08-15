"""
Package DataTable ServerSide - Export des classes principales

Ce package fournit une solution complète pour gérer les tableaux de données avec pagination,
tri, recherche et filtres avancés. Il est conçu selon les principes SOLID et offre une
architecture modulaire et extensible.

ARCHITECTURE:
- Interfaces (SOLID) : IDataTableConfig, IDataTableProcessor, IDataTableFilter, IDataTableSerializer
- Implémentations : DataTableConfig, DataTableProcessor, DataTableFilter, DataTableSerializer
- Filtres : DjangoFilterDataTableFilter, DateRangeFilter, StatusFilter, CompositeDataTableFilter
- Sérialiseurs : CustomDataTableSerializer, NestedDataTableSerializer, AggregatedDataTableSerializer
- Mixins : DataTableMixin, DataTableAPIView, DataTableListView
- Utilitaires : datatable_view, quick_datatable_view, is_datatable_request

UTILISATION RAPIDE:
    from apps.core.datatables import DataTableListView, DataTableConfig
    
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

FONCTIONNALITÉS:
- Détection automatique du format de requête (DataTable vs REST API)
- Recherche globale dans plusieurs champs
- Tri avancé supportant DataTable et REST API
- Filtres composites combinant différents types de filtres
- Pagination flexible avec limites configurables
- Sérialisation personnalisable
- Architecture extensible via les interfaces

PRINCIPES SOLID:
- Single Responsibility : Chaque classe a une responsabilité unique
- Open/Closed : Ouvert à l'extension, fermé à la modification
- Liskov Substitution : Les interfaces peuvent être substituées
- Interface Segregation : Interfaces spécifiques et cohérentes
- Dependency Inversion : Dépend des abstractions, pas des implémentations
"""

# =============================================================================
# EXPORT DES CLASSES DE BASE (Interfaces et Implémentations)
# =============================================================================

# Base classes - Classes de base avec interfaces SOLID
from .base import (
    # Interfaces (SOLID - Interface Segregation)
    IDataTableConfig,        # Interface pour la configuration
    IDataTableProcessor,     # Interface pour le processeur
    IDataTableFilter,        # Interface pour les filtres
    IDataTableSerializer,    # Interface pour les sérialiseurs
    
    # Implémentations (SOLID - Single Responsibility)
    DataTableConfig,         # Configuration centralisée avec validation
    DataTableProcessor,      # Processeur principal orchestrant toutes les opérations
    DataTableFilter,         # Filtres par défaut
    DataTableSerializer      # Sérialiseur par défaut utilisant DRF
)

# =============================================================================
# EXPORT DES FILTRES (Filtres spécialisés et composites)
# =============================================================================

# Filters - Filtres avancés pour différents cas d'usage
from .filters import (
    # Filtres spécialisés (SOLID - Single Responsibility)
    DjangoFilterDataTableFilter,  # Intégration avec Django Filter
    AdvancedDataTableFilter,      # Filtre avancé avec jointures et optimisations
    DateRangeFilter,              # Filtre spécialisé pour les plages de dates
    StatusFilter,                 # Filtre spécialisé pour les statuts
    
    # Filtre composite (SOLID - Open/Closed)
    CompositeDataTableFilter      # Combine plusieurs filtres en chaîne
)

# =============================================================================
# EXPORT DES SÉRIALISEURS (Sérialiseurs spécialisés et composites)
# =============================================================================

# Serializers - Sérialiseurs pour différents formats de données
from .serializers import (
    # Sérialiseurs spécialisés (SOLID - Single Responsibility)
    CustomDataTableSerializer,     # Sérialiseur avec mapping et champs calculés
    NestedDataTableSerializer,     # Sérialiseur pour données imbriquées
    AggregatedDataTableSerializer, # Sérialiseur avec agrégations
    
    # Sérialiseur composite (SOLID - Open/Closed)
    CompositeDataTableSerializer   # Combine plusieurs sérialiseurs
)

# =============================================================================
# EXPORT DES MIXINS (Mixins pour les vues et utilitaires)
# =============================================================================

# Mixins - Mixins pour ajouter DataTable aux vues et utilitaires
from .mixins import (
    # Mixins de base (DRY - Don't Repeat Yourself)
    DataTableMixin,           # Mixin de base pour ajouter DataTable à n'importe quelle vue
    DataTableAPIView,         # Vue API avec DataTable intégré
    DataTableListView,        # Vue spécialisée pour les listes avec DataTable
    
    # Décorateurs et utilitaires (DRY)
    datatable_view,           # Décorateur pour transformer une vue en DataTable
    quick_datatable_view,     # Fonction pour créer rapidement une vue DataTable
    is_datatable_request      # Fonction utilitaire pour détecter les requêtes DataTable
)

# =============================================================================
# EXPORT PUBLIC - Toutes les classes et fonctions disponibles
# =============================================================================

__all__ = [
    # =====================================================================
    # CLASSES DE BASE (Interfaces et Implémentations)
    # =====================================================================
    'IDataTableConfig',           # Interface pour la configuration DataTable
    'IDataTableProcessor',        # Interface pour le processeur DataTable
    'IDataTableFilter',           # Interface pour les filtres personnalisés
    'IDataTableSerializer',       # Interface pour les sérialiseurs
    'DataTableConfig',            # Configuration centralisée avec validation
    'DataTableProcessor',         # Processeur principal orchestrant toutes les opérations
    'DataTableFilter',            # Filtres par défaut
    'DataTableSerializer',        # Sérialiseur par défaut utilisant DRF
    
    # =====================================================================
    # FILTRES (Filtres spécialisés et composites)
    # =====================================================================
    'DjangoFilterDataTableFilter',    # Intégration avec Django Filter
    'AdvancedDataTableFilter',        # Filtre avancé avec jointures et optimisations
    'DateRangeFilter',                # Filtre spécialisé pour les plages de dates
    'StatusFilter',                   # Filtre spécialisé pour les statuts
    'CompositeDataTableFilter',       # Combine plusieurs filtres en chaîne
    
    # =====================================================================
    # SÉRIALISEURS (Sérialiseurs spécialisés et composites)
    # =====================================================================
    'CustomDataTableSerializer',      # Sérialiseur avec mapping et champs calculés
    'NestedDataTableSerializer',      # Sérialiseur pour données imbriquées
    'AggregatedDataTableSerializer',  # Sérialiseur avec agrégations
    'CompositeDataTableSerializer',   # Combine plusieurs sérialiseurs
    
    # =====================================================================
    # MIXINS (Mixins pour les vues et utilitaires)
    # =====================================================================
    'DataTableMixin',                # Mixin de base pour ajouter DataTable à n'importe quelle vue
    'DataTableAPIView',              # Vue API avec DataTable intégré
    'DataTableListView',             # Vue spécialisée pour les listes avec DataTable
    'datatable_view',                # Décorateur pour transformer une vue en DataTable
    'quick_datatable_view',          # Fonction pour créer rapidement une vue DataTable
    'is_datatable_request'           # Fonction utilitaire pour détecter les requêtes DataTable
]

# =============================================================================
# VERSION ET MÉTADONNÉES
# =============================================================================

__version__ = "1.0.0"
__author__ = "Équipe de développement"
__description__ = "Package DataTable ServerSide pour Django REST Framework"
__keywords__ = ["datatable", "django", "rest", "api", "pagination", "sorting", "filtering"]

# =============================================================================
# DOCUMENTATION RAPIDE
# =============================================================================

"""
EXEMPLES D'UTILISATION:

1. Vue simple avec DataTable:
    from apps.core.datatables import DataTableListView, DataTableConfig
    
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

2. Vue rapide avec quick_datatable_view:
    from apps.core.datatables import quick_datatable_view
    
    InventaireRapideView = quick_datatable_view(
        model_class=Inventory,
        serializer_class=InventorySerializer,
        search_fields=['label', 'reference'],
        order_fields=['id', 'label', 'date'],
        default_order='-date',
        page_size=25
    )

3. Vue avec filtres avancés:
    from apps.core.datatables import DataTableListView, CompositeDataTableFilter
    
    class InventaireAvecFiltresView(DataTableListView):
        def get_datatable_filter(self):
            composite_filter = CompositeDataTableFilter()
            composite_filter.add_filter(DjangoFilterDataTableFilter(InventoryFilter))
            composite_filter.add_filter(DateRangeFilter('date'))
            composite_filter.add_filter(StatusFilter('status'))
            return composite_filter

FORMATS DE RÉPONSE SUPPORTÉS:

1. DataTable:
    {
        "draw": 1,
        "recordsTotal": 150,
        "recordsFiltered": 25,
        "data": [...],
        "pagination": {...}
    }

2. REST API:
    {
        "count": 150,
        "results": [...],
        "next": "http://api/inventories/?page=2",
        "previous": null,
        "pagination": {...}
    }

PARAMÈTRES DE REQUÊTE SUPPORTÉS:

1. DataTable:
    GET /api/inventories/?draw=1&start=0&length=25&search[value]=test&order[0][column]=2&order[0][dir]=asc

2. REST API:
    GET /api/inventories/?page=1&page_size=25&search=test&ordering=label

PRINCIPES ARCHITECTURAUX:

- SOLID: Chaque classe respecte les principes SOLID
- DRY: Évite la duplication de code avec les mixins
- Séparation des responsabilités: Configuration, filtrage, sérialisation séparés
- Extensibilité: Interfaces pour créer des filtres et sérialiseurs personnalisés
- Performance: Optimisations de requête intégrées
- Sécurité: Validation des paramètres et protection contre les injections
""" 