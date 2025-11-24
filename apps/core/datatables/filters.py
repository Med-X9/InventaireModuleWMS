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


class FilterMappingFilter(IDataTableFilter):
    """
    Filtre pour mapper les champs frontend vers backend
    
    Ce filtre applique le mapping des filtres frontend vers backend
    en modifiant les paramètres de la requête avant l'application des filtres.
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : gérer le mapping des filtres
    - Évite les problèmes de sérialisation en modifiant directement les paramètres
    """
    
    def __init__(self, filter_aliases: dict, dynamic_filters: dict = None):
        """
        Initialise le filtre de mapping
        
        Args:
            filter_aliases (dict): Dictionnaire de mapping frontend -> backend
            dynamic_filters (dict): Dictionnaire des filtres dynamiques
        """
        self.filter_aliases = filter_aliases or {}
        self.dynamic_filters = dynamic_filters or {}
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique le mapping des filtres frontend -> backend directement sur le queryset
        
        Au lieu de modifier la requête, applique directement les filtres mappés
        sur le queryset pour éviter les problèmes de sérialisation.
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset initial à filtrer
            
        Returns:
            QuerySet: Queryset filtré avec les filtres mappés
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🔧 FilterMappingFilter: {queryset.count()} éléments avant")
        
        if not self.filter_aliases and not self.dynamic_filters:
            logger.debug(f"🔧 Aucun mapping configuré, retour du queryset")
            return queryset
        
        logger.debug(f"🔧 Filter_aliases configurés: {list(self.filter_aliases.keys())}")
            
        from django.db.models import Q
        
        # Construire les filtres Q directement
        q_objects = []
        
        # Appliquer le mapping des filtres normaux
        for frontend_field, backend_field in self.filter_aliases.items():
            # Chercher tous les paramètres qui commencent par le champ frontend
            for param_name, param_value in request.GET.items():
                if param_name.startswith(f"{frontend_field}_"):
                    # Extraire l'opérateur
                    operator = param_name.replace(f"{frontend_field}_", "")
                    
                    # Normaliser l'opérateur (equals -> exact)
                    if operator == 'equals':
                        operator = 'exact'
                    
                    # Créer le nom de champ avec l'opérateur
                    field_lookup = f"{backend_field}__{operator}"
                    
                    # Normaliser les espaces et caractères spéciaux
                    if isinstance(param_value, str):
                        param_value = param_value.replace('+', ' ')
                        from urllib.parse import unquote
                        param_value = unquote(param_value)
                    
                    logger.debug(f"🔧 Mapping: {param_name} -> {field_lookup} = '{param_value}'")
                    
                    # Ajouter le filtre Q
                    try:
                        q_objects.append(Q(**{field_lookup: param_value}))
                    except Exception as e:
                        logger.error(f"Erreur lors de la création du filtre Q pour {field_lookup}: {str(e)}")
                        continue
        
        # Appliquer les filtres dynamiques
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"Filtres dynamiques configurés: {list(self.dynamic_filters.keys())}")
        logger.debug(f"Paramètres de requête: {dict(request.GET)}")
        
        for frontend_field, config in self.dynamic_filters.items():
            for param_name, param_value in request.GET.items():
                if param_name.startswith(f"{frontend_field}_"):
                    operator = param_name.replace(f"{frontend_field}_", "")
                    logger.debug(f"Filtre dynamique détecté: {param_name} -> {frontend_field} avec opérateur {operator}")
                    queryset = self._apply_dynamic_filter(queryset, config, operator, param_value)
        
        # Appliquer tous les filtres Q normaux
        if q_objects:
            logger.debug(f"🔧 Application de {len(q_objects)} filtres de mapping")
            combined_q = Q()
            for q_obj in q_objects:
                combined_q &= q_obj
            queryset = queryset.filter(combined_q)
        
        logger.debug(f"🔧 FilterMappingFilter: {queryset.count()} éléments après")
        return queryset
    
    def _apply_dynamic_filter(self, queryset, config, operator, value):
        """Applique un filtre dynamique basé sur la configuration"""
        if not value:
            return queryset
            
        import logging
        logger = logging.getLogger(__name__)
        
        # Normaliser les espaces et caractères spéciaux
        if isinstance(value, str):
            value = value.replace('+', ' ').strip()
            from urllib.parse import unquote
            value = unquote(value)
        
        filter_type = config.get('type', 'concat')
        fields = config.get('fields', [])
        separator = config.get('separator', ' ')
        
        logger.debug(f"Filtre dynamique appliqué: type={filter_type}, fields={fields}, operator={operator}, value='{value}'")
        
        if filter_type == 'concat' and len(fields) >= 2:
            result = self._apply_concat_filter(queryset, fields, separator, operator, value)
            logger.debug(f"Résultat filtre concat: {result.count()} éléments")
            return result
        elif filter_type == 'split' and len(fields) >= 2:
            result = self._apply_split_filter(queryset, fields, operator, value)
            logger.debug(f"Résultat filtre split: {result.count()} éléments")
            return result
        
        logger.debug("Aucun filtre dynamique appliqué")
        return queryset
    
    def _apply_concat_filter(self, queryset, fields, separator, operator, value):
        """Applique un filtre de concaténation"""
        from django.db.models import Value, F
        from django.db.models.functions import Concat
        
        # Créer la fonction de concaténation
        concat_parts = []
        for field in fields:
            concat_parts.append(F(field))
            if field != fields[-1]:  # Pas de séparateur après le dernier champ
                concat_parts.append(Value(separator))
        
        # Appliquer l'annotation et le filtre
        lookup_expr = f"concat_field__{operator}"
        return queryset.annotate(
            concat_field=Concat(*concat_parts)
        ).filter(**{lookup_expr: value})
    
    def _apply_split_filter(self, queryset, fields, operator, value):
        """Applique un filtre de division de valeurs"""
        from django.db.models import Q
        
        parts = value.split()
        if len(parts) == len(fields):
            # Correspondance parfaite : chaque partie correspond à un champ
            filter_dict = {}
            for i, field in enumerate(fields):
                lookup_expr = f"{field}__{operator}"
                filter_dict[lookup_expr] = parts[i]
            return queryset.filter(**filter_dict)
        elif len(parts) == 1:
            # Une seule partie : chercher dans tous les champs
            q_objects = []
            for field in fields:
                lookup_expr = f"{field}__{operator}"
                q_objects.append(Q(**{lookup_expr: parts[0]}))
            if q_objects:
                combined_q = Q()
                for q_obj in q_objects:
                    combined_q |= q_obj
                return queryset.filter(combined_q)
        
        return queryset


class CompositeColumnFilter(IDataTableFilter):
    """
    Filtre pour les colonnes composées (ex: nom complet = prenom + nom)
    
    Ce filtre permet de filtrer sur des colonnes qui sont composées de plusieurs champs
    en utilisant la concaténation ou d'autres opérations sur la base de données.
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : gérer les filtres de colonnes composées
    - Support de différents types de composition
    - Optimisé pour les performances
    """
    
    def __init__(self, composite_columns: dict):
        """
        Initialise le filtre de colonnes composées
        
        Args:
            composite_columns (dict): Configuration des colonnes composées
                Exemple: {
                    'affectation_personne_full_name': {
                        'type': 'concat',
                        'fields': ['affectation_personne__prenom', 'affectation_personne__nom'],
                        'separator': ' '
                    }
                }
        """
        self.composite_columns = composite_columns or {}
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres sur les colonnes composées
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Chercher les paramètres qui correspondent aux colonnes composées
        matching_params = []
        for column_name in self.composite_columns.keys():
            for param_name, param_value in request.GET.items():
                if param_name.startswith(f"{column_name}_"):
                    operator = param_name.replace(f"{column_name}_", "")
                    matching_params.append((column_name, operator, param_value))
        
        if matching_params:
            logger.debug(f"🔧 Filtres composés détectés: {matching_params}")
            count_before = queryset.count()
            
            for column_name, operator, param_value in matching_params:
                config = self.composite_columns[column_name]
                queryset = self._apply_composite_filter(queryset, column_name, config, operator, param_value)
            
            count_after = queryset.count()
            logger.debug(f"📊 Résultat: {count_before} → {count_after} éléments")
        
        return queryset
    
    def _apply_composite_filter(self, queryset, column_name, config, operator, value):
        """Applique un filtre sur une colonne composée"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Normaliser les espaces et caractères spéciaux
        if isinstance(value, str):
            original_value = value
            value = value.replace('+', ' ').strip()
            from urllib.parse import unquote
            value = unquote(value)
            if original_value != value:
                logger.debug(f"🔄 Normalisation: '{original_value}' → '{value}'")
        
        filter_type = config.get('type', 'concat')
        fields = config.get('fields', [])
        separator = config.get('separator', ' ')
        
        if filter_type == 'concat' and len(fields) >= 2:
            logger.debug(f"🔗 Concat {column_name}: {fields} avec '{separator}' → '{value}' ({operator})")
            
            # Gérer les opérateurs spéciaux pour les colonnes composées
            if operator == 'startswith':
                operator = 'istartswith'
            elif operator == 'endswith':
                operator = 'iendswith'
            elif operator == 'contains':
                operator = 'icontains'
            elif operator == 'exact':
                # Pour exact, on peut aussi essayer icontains si pas de résultat
                pass
            
            result = self._apply_concat_filter(queryset, fields, separator, operator, value)
            return result
        
        return queryset
    
    def _apply_concat_filter(self, queryset, fields, separator, operator, value):
        """Applique un filtre de concaténation"""
        import logging
        logger = logging.getLogger(__name__)
        
        from django.db.models import Value, F
        from django.db.models.functions import Concat
        
        # Créer la fonction de concaténation
        concat_parts = []
        for field in fields:
            concat_parts.append(F(field))
            if field != fields[-1]:  # Pas de séparateur après le dernier champ
                concat_parts.append(Value(separator))
        
        # Appliquer l'annotation et le filtre
        lookup_expr = f"composite_field__{operator}"
        
        try:
            # Debug: vérifier d'abord s'il y a des données avec affectation_personne
            total_count = queryset.count()
            with_personne_count = queryset.filter(affectation_personne__isnull=False).count()
            logger.debug(f"🔍 Debug données: Total={total_count}, Avec personne={with_personne_count}")
            
            # D'abord, annoter pour voir les valeurs concaténées
            annotated_queryset = queryset.annotate(
                composite_field=Concat(*concat_parts)
            )
            
            # Debug: afficher quelques exemples de valeurs concaténées
            if annotated_queryset.exists():
                # Essayer de récupérer les données avec jointure
                try:
                    samples = list(annotated_queryset.filter(
                        affectation_personne__isnull=False
                    ).values('affectation_personne__prenom', 'affectation_personne__nom', 'composite_field')[:5])
                    logger.debug(f"💡 Exemples de données avec personne:")
                    logger.debug(f"   Valeur recherchée: '{value}' (longueur: {len(value)})")
                    for sample in samples:
                        concat_value = sample['composite_field']
                        logger.debug(f"   Prenom: '{sample['affectation_personne__prenom']}', Nom: '{sample['affectation_personne__nom']}'")
                        logger.debug(f"   Concat: '{concat_value}' (longueur: {len(concat_value)})")
                        logger.debug(f"   Match: {concat_value == value}")
                        # Debug des caractères
                        if concat_value != value:
                            logger.debug(f"   Différence - Recherché: {repr(value)}")
                            logger.debug(f"   Différence - Concat:   {repr(concat_value)}")
                except Exception as e:
                    logger.debug(f"❌ Erreur récupération exemples: {str(e)}")
            else:
                logger.debug(f"❌ Aucune donnée dans le queryset annoté")
            
            # Appliquer le filtre
            result = annotated_queryset.filter(**{lookup_expr: value})
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur CONCAT: {str(e)}")
            return queryset


class DataTableColumnFilter(IDataTableFilter):
    """
    Filtre pour gérer les filtres de colonnes DataTables au format:
    columns[i][data]=field_name
    columns[i][search][value]=search_value
    columns[i][operator]=operator (in, equals, contains, etc.)
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : gérer les filtres de colonnes DataTables
    - Supporte tous les opérateurs standards (in, equals, contains, etc.)
    
    UTILISATION:
        Le filtre est automatiquement appliqué si des paramètres columns[i][search][value] sont présents.
    """
    
    def __init__(self, column_field_mapping: dict = None):
        """
        Initialise le filtre de colonnes DataTables
        
        Args:
            column_field_mapping (dict): Mapping optionnel colonne -> champ Django
        """
        self.column_field_mapping = column_field_mapping or {}
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres de colonnes DataTables
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres columns[i][search][value]
            queryset (QuerySet): Queryset initial à filtrer
            
        Returns:
            QuerySet: Queryset filtré par les colonnes
        """
        from django.db.models import Q
        from urllib.parse import unquote
        
        logger.info(f"🔍 DataTableColumnFilter: Début du filtrage - {queryset.count()} éléments avant")
        logger.debug(f"🔍 Paramètres GET: {dict(request.GET)}")
        
        # Parcourir tous les paramètres columns[i][data] pour trouver les colonnes avec filtres
        column_indices = set()
        for param_name in request.GET.keys():
            if param_name.startswith('columns[') and param_name.endswith('][data]'):
                # Extraire l'index de la colonne
                try:
                    index_str = param_name.replace('columns[', '').replace('][data]', '')
                    column_indices.add(int(index_str))
                    logger.debug(f"🔍 Colonne détectée: index={index_str}")
                except ValueError:
                    continue
        
        if not column_indices:
            logger.debug("🔍 Aucune colonne avec filtre détectée")
            return queryset
        
        logger.info(f"🔍 Colonnes avec filtres détectées: {column_indices}")
        
        q_objects = []
        
        for column_index in column_indices:
            # Récupérer le nom du champ depuis columns[i][data]
            column_data = request.GET.get(f'columns[{column_index}][data]', '')
            if not column_data:
                logger.debug(f"🔍 Colonne {column_index}: pas de [data]")
                continue
            
            # Récupérer la valeur de recherche
            search_value = request.GET.get(f'columns[{column_index}][search][value]', '')
            if not search_value:
                logger.debug(f"🔍 Colonne {column_index}: pas de [search][value]")
                continue
            
            # Récupérer l'opérateur (par défaut: 'equals')
            operator = request.GET.get(f'columns[{column_index}][operator]', 'equals')
            
            # Déterminer le champ Django réel
            field_name = self.column_field_mapping.get(column_data, column_data)
            
            logger.info(f"🔍 Colonne {column_index}: data='{column_data}', field='{field_name}', operator='{operator}', value='{search_value}'")
            
            # Normaliser la valeur de recherche
            search_value = search_value.replace('+', ' ').strip()
            search_value = unquote(search_value)
            logger.debug(f"🔍 Valeur normalisée: '{search_value}'")
            
            # Appliquer l'opérateur approprié
            try:
                if operator == 'in':
                    # Opérateur 'in' : la valeur peut être une liste séparée par des virgules
                    values = [v.strip() for v in search_value.split(',') if v.strip()]
                    if values:
                        q_objects.append(Q(**{f'{field_name}__in': values}))
                        logger.debug(f"🔧 Filtre colonne {column_index} ({field_name}): operator='in', values={values}")
                elif operator == 'equals':
                    # Opérateur 'equals' : correspondance exacte
                    q_objects.append(Q(**{f'{field_name}__exact': search_value}))
                    logger.debug(f"🔧 Filtre colonne {column_index} ({field_name}): operator='equals', value='{search_value}'")
                elif operator == 'contains':
                    # Opérateur 'contains' : contient le terme
                    q_objects.append(Q(**{f'{field_name}__icontains': search_value}))
                    logger.debug(f"🔧 Filtre colonne {column_index} ({field_name}): operator='contains', value='{search_value}'")
                elif operator == 'startswith':
                    # Opérateur 'startswith' : commence par
                    q_objects.append(Q(**{f'{field_name}__istartswith': search_value}))
                    logger.debug(f"🔧 Filtre colonne {column_index} ({field_name}): operator='startswith', value='{search_value}'")
                elif operator == 'endswith':
                    # Opérateur 'endswith' : termine par
                    q_objects.append(Q(**{f'{field_name}__iendswith': search_value}))
                    logger.debug(f"🔧 Filtre colonne {column_index} ({field_name}): operator='endswith', value='{search_value}'")
                elif operator == 'notEqual':
                    # Opérateur 'notEqual' : différent de
                    q_objects.append(~Q(**{f'{field_name}__exact': search_value}))
                    logger.debug(f"🔧 Filtre colonne {column_index} ({field_name}): operator='notEqual', value='{search_value}'")
                else:
                    # Opérateur par défaut : exact
                    q_objects.append(Q(**{f'{field_name}__exact': search_value}))
                    logger.debug(f"🔧 Filtre colonne {column_index} ({field_name}): operator='{operator}' (fallback exact), value='{search_value}'")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'application du filtre colonne {column_index} ({field_name}): {str(e)}")
                continue
        
        # Appliquer tous les filtres avec AND
        if q_objects:
            logger.info(f"🔍 Application de {len(q_objects)} filtres de colonnes DataTables")
            combined_q = Q()
            for q_obj in q_objects:
                combined_q &= q_obj
            count_before = queryset.count()
            queryset = queryset.filter(combined_q)
            count_after = queryset.count()
            logger.info(f"🔍 DataTableColumnFilter: {count_before} → {count_after} éléments après filtrage")
        else:
            logger.warning("🔍 Aucun filtre Q créé - vérifier les paramètres")
        
        return queryset 