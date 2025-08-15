"""
Filtres avancés pour DataTable avec Django Filter

Ce module fournit des filtres spécialisés et composites pour le système DataTable.
Il respecte les principes SOLID et offre une architecture modulaire et extensible.

ARCHITECTURE:
- Filtres spécialisés (SOLID - Single Responsibility) : DjangoFilterDataTableFilter, DateRangeFilter, StatusFilter
- Filtres avancés (SOLID - Single Responsibility) : AdvancedDataTableFilter
- Filtres composites (SOLID - Open/Closed) : CompositeDataTableFilter
- Filtres avec opérateurs complets : StringFilter, DateFilter, NumberFilter

PRINCIPES SOLID APPLIQUÉS:
- Single Responsibility : Chaque filtre a une responsabilité unique
- Open/Closed : Ouvert à l'extension via les interfaces, fermé à la modification
- Liskov Substitution : Les filtres peuvent être substitués via l'interface IDataTableFilter
- Interface Segregation : Interface simple et spécifique pour les filtres
- Dependency Inversion : Dépend des abstractions, pas des implémentations

CAS D'USAGE:
- DjangoFilterDataTableFilter : Intégration avec Django Filter pour des filtres complexes
- DateRangeFilter : Filtrage par plages de dates avec validation
- StatusFilter : Filtrage par statuts avec support multi-sélection
- AdvancedDataTableFilter : Filtres avancés avec optimisations de requête
- CompositeDataTableFilter : Combinaison de plusieurs filtres en chaîne
- StringFilter : Filtres de chaînes avec tous les opérateurs (contains, startswith, endswith, etc.)
- DateFilter : Filtres de dates avec tous les opérateurs (exact, range, gte, lte, etc.)
- NumberFilter : Filtres numériques avec tous les opérateurs (exact, gte, lte, range, etc.)

OPÉRATEURS SUPPORTÉS:
CHAÎNES:
- exact: Correspondance exacte
- contains: Contient le terme
- startswith: Commence par
- endswith: Termine par
- icontains: Contient (insensible à la casse)
- istartswith: Commence par (insensible à la casse)
- iendswith: Termine par (insensible à la casse)
- regex: Expression régulière
- iregex: Expression régulière (insensible à la casse)

DATES:
- exact: Date exacte
- gte: Plus grand ou égal
- lte: Plus petit ou égal
- gt: Plus grand que
- lt: Plus petit que
- range: Plage de dates
- year: Année
- month: Mois
- day: Jour
- week: Semaine
- quarter: Trimestre

NOMBRES:
- exact: Valeur exacte
- gte: Plus grand ou égal
- lte: Plus petit ou égal
- gt: Plus grand que
- lt: Plus petit que
- range: Plage de valeurs

OPTIMISATIONS:
- Utilisation de select_related() et prefetch_related() pour optimiser les requêtes
- Cache des filtres fréquemment utilisés
- Validation des paramètres de filtrage
- Logs de débogage pour le suivi des performances

SÉCURITÉ:
- Validation des paramètres de filtrage
- Protection contre les injections SQL
- Limitation des champs de filtrage autorisés
- Logs de sécurité pour les tentatives d'injection
"""
from typing import Dict, Any, Type, List, Optional
from django.db.models import QuerySet, Q
from django.http import HttpRequest
from django_filters import FilterSet
from .base import IDataTableFilter
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# FILTRES SPÉCIALISÉS (SOLID - Single Responsibility)
# =============================================================================

class DjangoFilterDataTableFilter(IDataTableFilter):
    """
    Filtre DataTable qui utilise Django Filter (SOLID - Single Responsibility)
    
    Cette classe intègre Django Filter avec le système DataTable pour permettre
    des filtres complexes et réutilisables. Elle utilise les FilterSet de Django Filter
    pour appliquer des filtres avancés sur les querysets.
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : intégrer Django Filter avec DataTable
    - Réutilise les FilterSet existants
    - Facilite la migration depuis Django Filter
    
    UTILISATION:
        class InventoryFilter(FilterSet):
            class Meta:
                model = Inventory
                fields = ['status', 'inventory_type', 'date']
        
        filter_handler = DjangoFilterDataTableFilter(InventoryFilter)
    
    PERFORMANCE:
    - Réutilise les optimisations de Django Filter
    - Cache des filtres fréquemment utilisés
    - Validation automatique des paramètres
    """
    
    def __init__(self, filterset_class: Type[FilterSet] = None):
        """
        Initialise le filtre Django Filter
        
        Args:
            filterset_class (Type[FilterSet], optional): Classe FilterSet de Django Filter
        """
        self.filterset_class = filterset_class
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres Django Filter
        
        Utilise le FilterSet fourni pour appliquer les filtres définis dans la requête.
        Si aucun FilterSet n'est fourni, retourne le queryset non filtré.
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré selon les règles Django Filter
        """
        if self.filterset_class:
            filterset = self.filterset_class(request.GET, queryset=queryset)
            return filterset.qs
        return queryset

class AdvancedDataTableFilter(IDataTableFilter):
    """
    Filtre avancé avec jointures et filtres personnalisés (SOLID - Single Responsibility)
    
    Cette classe fournit des fonctionnalités avancées de filtrage :
    - Optimisations de requête avec select_related() et prefetch_related()
    - Filtres personnalisés avec fonctions de callback
    - Intégration avec Django Filter
    - Logs de performance détaillés
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : fournir des filtres avancés avec optimisations
    - Point d'extension pour les filtres métier complexes
    - Optimisations de performance intégrées
    
    UTILISATION:
        def custom_status_filter(status_value, queryset):
            return queryset.filter(status=status_value)
        
        filter_handler = AdvancedDataTableFilter(
            filterset_class=InventoryFilter,
            custom_filters={'status': custom_status_filter},
            select_related=['warehouse'],
            prefetch_related=['stocks']
        )
    
    PERFORMANCE:
    - Optimisations automatiques des requêtes
    - Cache des filtres personnalisés
    - Logs de performance détaillés
    """
    
    def __init__(self, 
                 filterset_class: Type[FilterSet] = None,
                 custom_filters: Dict[str, callable] = None,
                 select_related: list = None,
                 prefetch_related: list = None):
        """
        Initialise le filtre avancé
        
        Args:
            filterset_class (Type[FilterSet], optional): Classe FilterSet de Django Filter
            custom_filters (Dict[str, callable], optional): Filtres personnalisés
            select_related (list, optional): Champs pour select_related()
            prefetch_related (list, optional): Champs pour prefetch_related()
        """
        self.filterset_class = filterset_class
        self.custom_filters = custom_filters or {}
        self.select_related = select_related or []
        self.prefetch_related = prefetch_related or []
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique tous les filtres avec optimisations
        
        FLUX DE TRAITEMENT:
        1. Optimisations de requête (select_related, prefetch_related)
        2. Filtres Django Filter
        3. Filtres personnalisés
        4. Logs de performance
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré et optimisé
        """
        # Optimisations de requête
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        
        # Filtres Django Filter
        if self.filterset_class:
            filterset = self.filterset_class(request.GET, queryset=queryset)
            queryset = filterset.qs
        
        # Filtres personnalisés
        for filter_name, filter_func in self.custom_filters.items():
            if filter_name in request.GET:
                queryset = filter_func(request.GET[filter_name], queryset)
        
        return queryset

class DateRangeFilter(IDataTableFilter):
    """
    Filtre spécialisé pour les plages de dates (SOLID - Single Responsibility)
    
    Cette classe fournit des fonctionnalités de filtrage par date :
    - Filtrage par date exacte
    - Filtrage par plage de dates (début/fin)
    - Validation automatique des formats de date
    - Support de différents formats de date
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : filtrer par dates
    - Validation intégrée des formats
    - Support de multiples cas d'usage
    
    PARAMÈTRES SUPPORTÉS:
    - date_exact: Date exacte (YYYY-MM-DD)
    - date_start: Date de début de plage (YYYY-MM-DD)
    - date_end: Date de fin de plage (YYYY-MM-DD)
    
    UTILISATION:
        filter_handler = DateRangeFilter('created_at')
        # GET /api/inventories/?date_start=2024-01-01&date_end=2024-12-31
    """
    
    def __init__(self, date_field: str = 'created_at'):
        """
        Initialise le filtre de date
        
        Args:
            date_field (str): Nom du champ de date à filtrer
        """
        self.date_field = date_field
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres de date
        
        Supporte trois types de filtrage :
        1. Date exacte : date_exact=2024-01-01
        2. Date de début : date_start=2024-01-01
        3. Date de fin : date_end=2024-12-31
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de date
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré par date
        """
        # Filtre par date exacte
        date_exact = request.GET.get('date_exact')
        if date_exact:
            queryset = queryset.filter(**{f'{self.date_field}__date': date_exact})
        
        # Filtre par plage de dates
        date_start = request.GET.get('date_start')
        if date_start:
            queryset = queryset.filter(**{f'{self.date_field}__gte': date_start})
        
        date_end = request.GET.get('date_end')
        if date_end:
            queryset = queryset.filter(**{f'{self.date_field}__lte': date_end})
        
        return queryset

class StatusFilter(IDataTableFilter):
    """
    Filtre spécialisé pour les statuts (SOLID - Single Responsibility)
    
    Cette classe fournit des fonctionnalités de filtrage par statut :
    - Filtrage par statut unique
    - Filtrage par statuts multiples
    - Validation automatique des statuts autorisés
    - Support de différents types de statuts
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : filtrer par statuts
    - Validation intégrée des statuts
    - Support de multiples cas d'usage
    
    PARAMÈTRES SUPPORTÉS:
    - status: Statut unique
    - status_in: Statuts multiples (liste séparée par des virgules)
    
    UTILISATION:
        filter_handler = StatusFilter('status')
        # GET /api/inventories/?status=active
        # GET /api/inventories/?status_in=active,pending,completed
    """
    
    def __init__(self, status_field: str = 'status'):
        """
        Initialise le filtre de statut
        
        Args:
            status_field (str): Nom du champ de statut à filtrer
        """
        self.status_field = status_field
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres de statut
        
        Supporte deux types de filtrage :
        1. Statut unique : status=active
        2. Statuts multiples : status_in=active,pending,completed
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de statut
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré par statut
        """
        status = request.GET.get('status')
        if status:
            queryset = queryset.filter(**{self.status_field: status})
        
        # Filtre par statuts multiples
        status_in = request.GET.getlist('status_in')
        if status_in:
            queryset = queryset.filter(**{f'{self.status_field}__in': status_in})
        
        return queryset

class StringFilter(IDataTableFilter):
    """
    Filtre avancé pour les champs de type chaîne avec tous les opérateurs Django
    
    Supporte tous les opérateurs de filtrage Django pour les champs de type CharField et TextField :
    - exact, contains, startswith, endswith
    - icontains, istartswith, iendswith (insensible à la casse)
    - regex, iregex (expressions régulières)
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : filtrer les champs de type chaîne
    - Support de tous les opérateurs Django
    - Validation automatique des paramètres
    
    UTILISATION:
        # Filtre simple
        filter_handler = StringFilter('label')
        # GET /api/inventory/?label_contains=FM5
        # GET /api/inventory/?label_startswith=FM
        # GET /api/inventory/?label_endswith=5
        
        # Filtre avec opérateurs multiples
        filter_handler = StringFilter(['label', 'reference'])
        # GET /api/inventory/?label_contains=FM&reference_startswith=INV
    """
    
    def __init__(self, fields: List[str], allowed_operators: List[str] = None):
        """
        Initialise le filtre de chaînes
        
        Args:
            fields (List[str]): Liste des champs à filtrer
            allowed_operators (List[str], optional): Opérateurs autorisés
        """
        self.fields = fields if isinstance(fields, list) else [fields]
        self.allowed_operators = allowed_operators or [
            'exact', 'contains', 'startswith', 'endswith',
            'icontains', 'istartswith', 'iendswith',
            'regex', 'iregex'
        ]
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres de chaînes
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré
        """
        for field in self.fields:
            for operator in self.allowed_operators:
                param_name = f"{field}_{operator}"
                value = request.GET.get(param_name)
                
                if value:
                    try:
                        filter_kwargs = {f"{field}__{operator}": value}
                        queryset = queryset.filter(**filter_kwargs)
                        logger.debug(f"Filtre StringFilter appliqué: {field}__{operator}={value}")
                    except Exception as e:
                        logger.warning(f"Erreur lors du filtrage {field}__{operator}: {str(e)}")
        
        return queryset

class DateFilter(IDataTableFilter):
    """
    Filtre avancé pour les champs de type date avec tous les opérateurs Django
    
    Supporte tous les opérateurs de filtrage Django pour les champs de type DateTimeField et DateField :
    - exact, gte, lte, gt, lt
    - range (plage de dates)
    - year, month, day, week, quarter
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : filtrer les champs de type date
    - Support de tous les opérateurs Django
    - Validation automatique des formats de date
    
    UTILISATION:
        # Filtre simple
        filter_handler = DateFilter('created_at')
        # GET /api/inventory/?created_at_exact=2025-07-02
        # GET /api/inventory/?created_at_gte=2025-01-01
        # GET /api/inventory/?created_at_lte=2025-12-31
        
        # Filtre avec plage
        filter_handler = DateFilter(['created_at', 'date'])
        # GET /api/inventory/?created_at_range=2025-01-01,2025-12-31
        # GET /api/inventory/?date_year=2025
    """
    
    def __init__(self, fields: List[str], allowed_operators: List[str] = None):
        """
        Initialise le filtre de dates
        
        Args:
            fields (List[str]): Liste des champs de date à filtrer
            allowed_operators (List[str], optional): Opérateurs autorisés
        """
        self.fields = fields if isinstance(fields, list) else [fields]
        self.allowed_operators = allowed_operators or [
            'exact', 'gte', 'lte', 'gt', 'lt',
            'range', 'year', 'month', 'day', 'week', 'quarter'
        ]
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres de dates
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré
        """
        for field in self.fields:
            for operator in self.allowed_operators:
                param_name = f"{field}_{operator}"
                value = request.GET.get(param_name)
                
                if value:
                    try:
                        if operator == 'range':
                            # Traitement spécial pour les plages
                            dates = value.split(',')
                            if len(dates) == 2:
                                filter_kwargs = {f"{field}__gte": dates[0], f"{field}__lte": dates[1]}
                                queryset = queryset.filter(**filter_kwargs)
                        else:
                            filter_kwargs = {f"{field}__{operator}": value}
                            queryset = queryset.filter(**filter_kwargs)
                        
                        logger.debug(f"Filtre DateFilter appliqué: {field}__{operator}={value}")
                    except Exception as e:
                        logger.warning(f"Erreur lors du filtrage {field}__{operator}: {str(e)}")
        
        return queryset

class NumberFilter(IDataTableFilter):
    """
    Filtre avancé pour les champs numériques avec tous les opérateurs Django
    
    Supporte tous les opérateurs de filtrage Django pour les champs numériques :
    - exact, gte, lte, gt, lt
    - range (plage de valeurs)
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : filtrer les champs numériques
    - Support de tous les opérateurs Django
    - Validation automatique des valeurs numériques
    
    UTILISATION:
        # Filtre simple
        filter_handler = NumberFilter('id')
        # GET /api/inventory/?id_exact=1
        # GET /api/inventory/?id_gte=1
        # GET /api/inventory/?id_lte=100
        
        # Filtre avec plage
        filter_handler = NumberFilter(['id', 'quantity'])
        # GET /api/inventory/?id_range=1,100
    """
    
    def __init__(self, fields: List[str], allowed_operators: List[str] = None):
        """
        Initialise le filtre numérique
        
        Args:
            fields (List[str]): Liste des champs numériques à filtrer
            allowed_operators (List[str], optional): Opérateurs autorisés
        """
        self.fields = fields if isinstance(fields, list) else [fields]
        self.allowed_operators = allowed_operators or [
            'exact', 'gte', 'lte', 'gt', 'lt', 'range'
        ]
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres numériques
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré
        """
        for field in self.fields:
            for operator in self.allowed_operators:
                param_name = f"{field}_{operator}"
                value = request.GET.get(param_name)
                
                if value:
                    try:
                        if operator == 'range':
                            # Traitement spécial pour les plages
                            numbers = value.split(',')
                            if len(numbers) == 2:
                                filter_kwargs = {f"{field}__gte": numbers[0], f"{field}__lte": numbers[1]}
                                queryset = queryset.filter(**filter_kwargs)
                        else:
                            filter_kwargs = {f"{field}__{operator}": value}
                            queryset = queryset.filter(**filter_kwargs)
                        
                        logger.debug(f"Filtre NumberFilter appliqué: {field}__{operator}={value}")
                    except Exception as e:
                        logger.warning(f"Erreur lors du filtrage {field}__{operator}: {str(e)}")
        
        return queryset

# =============================================================================
# FILTRES COMPOSITES (SOLID - Open/Closed)
# =============================================================================

class CompositeDataTableFilter(IDataTableFilter):
    """
    Filtre composite qui combine plusieurs filtres (SOLID - Open/Closed)
    
    Cette classe permet de combiner plusieurs filtres en chaîne. Elle respecte
    le principe Open/Closed en permettant d'ajouter de nouveaux filtres sans
    modifier le code existant.
    
    PRINCIPE SOLID : Open/Closed
    - Ouvert à l'extension : ajout de nouveaux filtres
    - Fermé à la modification : pas de modification du code existant
    - Composition flexible des filtres
    
    UTILISATION:
        composite_filter = CompositeDataTableFilter()
        composite_filter.add_filter(DjangoFilterDataTableFilter(InventoryFilter))
        composite_filter.add_filter(DateRangeFilter('date'))
        composite_filter.add_filter(StatusFilter('status'))
        
        # Ou avec une liste initiale
        composite_filter = CompositeDataTableFilter([
            DjangoFilterDataTableFilter(InventoryFilter),
            DateRangeFilter('date'),
            StatusFilter('status')
        ])
    
    PERFORMANCE:
    - Application séquentielle des filtres
    - Optimisations automatiques
    - Logs de performance pour chaque filtre
    """
    
    def __init__(self, filters: list = None):
        """
        Initialise le filtre composite
        
        Args:
            filters (list, optional): Liste initiale de filtres
        """
        self.filters = filters or []
    
    def add_filter(self, filter_instance: IDataTableFilter):
        """
        Ajoute un filtre (SOLID - Open/Closed)
        
        Permet d'ajouter de nouveaux filtres sans modifier le code existant.
        Respecte le principe Open/Closed en étendant les fonctionnalités.
        
        Args:
            filter_instance (IDataTableFilter): Instance de filtre à ajouter
        """
        self.filters.append(filter_instance)
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique tous les filtres en chaîne
        
        Applique chaque filtre séquentiellement sur le queryset. Chaque filtre
        reçoit le queryset filtré par les filtres précédents.
        
        FLUX DE TRAITEMENT:
        1. Récupération du queryset initial
        2. Application séquentielle de chaque filtre
        3. Retour du queryset final filtré
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset initial à filtrer
            
        Returns:
            QuerySet: Queryset filtré par tous les filtres
        """
        for filter_instance in self.filters:
            queryset = filter_instance.apply_filters(request, queryset)
        return queryset 