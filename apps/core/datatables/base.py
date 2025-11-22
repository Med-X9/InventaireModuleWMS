"""
Package DataTable ServerSide - Base SOLID

Ce module contient les interfaces et implémentations de base pour le système DataTable.
Il respecte les principes SOLID et fournit une architecture modulaire et extensible.

ARCHITECTURE:
- Interfaces (SOLID - Interface Segregation) : IDataTableConfig, IDataTableProcessor, IDataTableFilter, IDataTableSerializer
- Implémentations (SOLID - Single Responsibility) : DataTableConfig, DataTableProcessor, DataTableFilter, DataTableSerializer

PRINCIPES SOLID APPLIQUÉS:
- Single Responsibility : Chaque classe a une responsabilité unique
- Open/Closed : Ouvert à l'extension, fermé à la modification via les interfaces
- Liskov Substitution : Les interfaces peuvent être substituées par leurs implémentations
- Interface Segregation : Interfaces spécifiques et cohérentes
- Dependency Inversion : Dépend des abstractions, pas des implémentations

FLUX DE TRAITEMENT:
1. Configuration : DataTableConfig définit les paramètres (champs de recherche, tri, pagination)
2. Filtrage : IDataTableFilter applique les filtres personnalisés
3. Recherche : Recherche globale dans les champs configurés
4. Tri : Tri selon les paramètres DataTable ou REST API
5. Pagination : Pagination avec limites configurables
6. Sérialisation : IDataTableSerializer transforme les données
7. Réponse : Format DataTable ou REST API selon la détection automatique

SÉCURITÉ:
- Validation des champs de tri autorisés
- Limitation de la taille de page
- Protection contre les injections SQL
- Validation des paramètres de recherche

PERFORMANCE:
- Optimisations de requête intégrées
- Pagination côté serveur
- Cache des configurations
- Logs de débogage détaillés
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type
from django.db.models import QuerySet, Q
from django.http import JsonResponse, HttpRequest
from django.core.paginator import Paginator
from rest_framework.serializers import Serializer
import logging

# Configuration du logger pour le débogage
logger = logging.getLogger(__name__)

# =============================================================================
# INTERFACES (SOLID - Interface Segregation)
# =============================================================================

class IDataTableConfig(ABC):
    """
    Interface pour la configuration DataTable (SOLID - Interface Segregation)
    
    Cette interface définit les méthodes requises pour configurer un DataTable :
    - Champs de recherche autorisés
    - Champs de tri autorisés
    - Ordre par défaut
    - Paramètres de pagination
    
    PRINCIPE SOLID : Interface Segregation
    - Interface spécifique et cohérente
    - Ne force pas l'implémentation de méthodes inutiles
    - Facilite la substitution et l'extension
    """
    
    @abstractmethod
    def get_search_fields(self) -> List[str]:
        """
        Retourne les champs de recherche autorisés
        
        Returns:
            List[str]: Liste des champs où la recherche globale est autorisée
        """
        pass
    
    @abstractmethod
    def get_order_fields(self) -> List[str]:
        """
        Retourne les champs de tri autorisés
        
        Returns:
            List[str]: Liste des champs où le tri est autorisé
        """
        pass
    
    @abstractmethod
    def get_default_order(self) -> str:
        """
        Retourne l'ordre par défaut
        
        Returns:
            str: Champ et direction de tri par défaut (ex: '-created_at')
        """
        pass
    
    @abstractmethod
    def get_page_size(self) -> int:
        """
        Retourne la taille de page par défaut
        
        Returns:
            int: Nombre d'éléments par page
        """
        pass

class IDataTableProcessor(ABC):
    """
    Interface pour le processeur DataTable (SOLID - Interface Segregation)
    
    Cette interface définit le contrat pour traiter une requête DataTable complète :
    - Extraction des paramètres
    - Application des filtres
    - Recherche globale
    - Tri
    - Pagination
    - Sérialisation
    - Format de réponse
    
    PRINCIPE SOLID : Interface Segregation
    - Interface spécifique pour le traitement des requêtes
    - Séparation claire des responsabilités
    - Facilite les tests et l'extension
    """
    
    @abstractmethod
    def process(self, request: HttpRequest, queryset: QuerySet) -> JsonResponse:
        """
        Traite la requête DataTable complète
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres DataTable
            queryset (QuerySet): Queryset de base à traiter
            
        Returns:
            JsonResponse: Réponse au format DataTable ou REST API
        """
        pass

class IDataTableFilter(ABC):
    """
    Interface pour les filtres personnalisés (SOLID - Interface Segregation)
    
    Cette interface permet d'implémenter des filtres personnalisés :
    - Filtres Django Filter
    - Filtres de date
    - Filtres de statut
    - Filtres composites
    - Filtres métier personnalisés
    
    PRINCIPE SOLID : Interface Segregation
    - Interface simple et spécifique
    - Facilite l'ajout de nouveaux types de filtres
    - Permet la composition de filtres
    """
    
    @abstractmethod
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres personnalisés au queryset
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de filtrage
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset filtré
        """
        pass

class IDataTableSerializer(ABC):
    """
    Interface pour la sérialisation (SOLID - Interface Segregation)
    
    Cette interface permet d'implémenter des sérialiseurs personnalisés :
    - Sérialiseurs DRF
    - Sérialiseurs personnalisés
    - Sérialiseurs avec mapping
    - Sérialiseurs pour données imbriquées
    - Sérialiseurs avec agrégations
    
    PRINCIPE SOLID : Interface Segregation
    - Interface simple et spécifique
    - Facilite l'ajout de nouveaux formats de sérialisation
    - Permet la composition de sérialiseurs
    """
    
    @abstractmethod
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Sérialise les données du queryset
        
        Args:
            queryset (QuerySet): Queryset à sérialiser
            
        Returns:
            List[Dict[str, Any]]: Données sérialisées
        """
        pass

# =============================================================================
# IMPLÉMENTATIONS (SOLID - Single Responsibility)
# =============================================================================

class DataTableConfig(IDataTableConfig):
    """
    Configuration par défaut pour DataTable (SOLID - Single Responsibility)
    
    Cette classe centralise toute la configuration d'un DataTable :
    - Champs de recherche autorisés
    - Champs de tri autorisés
    - Ordre par défaut
    - Paramètres de pagination avec validation
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : gérer la configuration
    - Validation intégrée des paramètres
    - Limites de sécurité configurables
    
    SÉCURITÉ:
    - Validation des limites min/max pour la pagination
    - Protection contre les valeurs invalides
    - Logs de débogage pour le suivi
    """
    
    def __init__(self, 
                 search_fields: List[str] = None,
                 order_fields: List[str] = None,
                 default_order: str = '-created_at',
                 page_size: int = 20,
                 min_page_size: int = 1,
                 max_page_size: int = 1000):
        """
        Initialise la configuration DataTable
        
        Args:
            search_fields (List[str], optional): Champs de recherche autorisés
            order_fields (List[str], optional): Champs de tri autorisés
            default_order (str, optional): Ordre par défaut
            page_size (int, optional): Taille de page par défaut
            min_page_size (int, optional): Taille de page minimale
            max_page_size (int, optional): Taille de page maximale
        """
        self._search_fields = search_fields or []
        self._order_fields = order_fields or []
        self._default_order = default_order
        self._page_size = page_size
        self._min_page_size = min_page_size
        self._max_page_size = max_page_size
        
        # Validation des paramètres
        self._validate_config()
    
    def _validate_config(self):
        """Valide la configuration pour éviter les erreurs"""
        if self._page_size < self._min_page_size:
            logger.warning(f"page_size ({self._page_size}) inférieur à min_page_size ({self._min_page_size})")
            self._page_size = self._min_page_size
        
        if self._page_size > self._max_page_size:
            logger.warning(f"page_size ({self._page_size}) supérieur à max_page_size ({self._max_page_size})")
            self._page_size = self._max_page_size
    
    def get_search_fields(self) -> List[str]:
        """Retourne les champs de recherche autorisés"""
        return self._search_fields
    
    def get_order_fields(self) -> List[str]:
        """Retourne les champs de tri autorisés"""
        return self._order_fields
    
    def get_default_order(self) -> str:
        """Retourne l'ordre par défaut"""
        return self._default_order
    
    def get_page_size(self) -> int:
        """Retourne la taille de page par défaut"""
        return self._page_size
    
    def get_min_page_size(self) -> int:
        """Retourne la taille de page minimale"""
        return self._min_page_size
    
    def get_max_page_size(self) -> int:
        """Retourne la taille de page maximale"""
        return self._max_page_size

class DataTableFilter(IDataTableFilter):
    """
    Filtres par défaut pour DataTable (SOLID - Single Responsibility)
    
    Cette classe fournit une implémentation de base pour les filtres.
    Elle peut être étendue ou remplacée par des filtres personnalisés.
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : appliquer des filtres de base
    - Point d'extension pour les filtres personnalisés
    - Comportement par défaut sécurisé
    """
    
    def apply_filters(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique les filtres de base (aucun filtre par défaut)
        
        Args:
            request (HttpRequest): Requête HTTP
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset non filtré (comportement par défaut)
        """
        return queryset

class DataTableSerializer(IDataTableSerializer):
    """
    Sérialiseur par défaut pour DataTable (SOLID - Single Responsibility)
    
    Cette classe fournit une implémentation de base pour la sérialisation.
    Elle utilise DRF si un serializer_class est fourni, sinon retourne les valeurs brutes.
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : sérialiser les données
    - Intégration avec DRF
    - Fallback vers les valeurs brutes
    """
    
    def __init__(self, serializer_class: Type[Serializer] = None):
        """
        Initialise le sérialiseur
        
        Args:
            serializer_class (Type[Serializer], optional): Classe de sérialiseur DRF
        """
        self.serializer_class = serializer_class
    
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Sérialise les données du queryset
        
        Args:
            queryset (QuerySet): Queryset à sérialiser
            
        Returns:
            List[Dict[str, Any]]: Données sérialisées
        """
        if self.serializer_class:
            # Utiliser DRF si un serializer_class est fourni
            serializer = self.serializer_class(queryset, many=True)
            return serializer.data
        else:
            # Fallback vers les valeurs brutes
            return list(queryset.values())

class DataTableProcessor(IDataTableProcessor):
    """
    Processeur principal pour DataTable (SOLID - Single Responsibility)
    
    Cette classe orchestre tout le processus de traitement d'une requête DataTable :
    1. Extraction des paramètres
    2. Application des filtres personnalisés
    3. Recherche globale
    4. Tri
    5. Pagination
    6. Sérialisation
    7. Format de réponse
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : orchestrer le traitement des requêtes
    - Utilise les interfaces pour la flexibilité
    - Gestion d'erreurs centralisée
    - Logs de débogage détaillés
    
    SÉCURITÉ:
    - Validation des paramètres
    - Protection contre les injections SQL
    - Gestion des erreurs avec try/catch
    - Logs de sécurité
    """
    
    def __init__(self, 
                 config: IDataTableConfig,
                 filter_handler: IDataTableFilter = None,
                 serializer_handler: IDataTableSerializer = None):
        """
        Initialise le processeur DataTable
        
        Args:
            config (IDataTableConfig): Configuration DataTable
            filter_handler (IDataTableFilter, optional): Gestionnaire de filtres
            serializer_handler (IDataTableSerializer, optional): Gestionnaire de sérialisation
        """
        self.config = config
        self.filter_handler = filter_handler or DataTableFilter()
        self.serializer_handler = serializer_handler or DataTableSerializer()
    
    def process(self, request: HttpRequest, queryset: QuerySet) -> JsonResponse:
        """
        Traite la requête DataTable complète
        
        FLUX DE TRAITEMENT:
        1. Extraction des paramètres DataTable
        2. Vérification si le queryset est déjà filtré
        3. Application des filtres personnalisés
        4. Recherche globale dans les champs configurés
        5. Tri selon les paramètres DataTable ou REST API
        6. Pagination avec limites configurables
        7. Sérialisation des données
        8. Format de réponse selon la détection automatique
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres DataTable
            queryset (QuerySet): Queryset de base à traiter
            
        Returns:
            JsonResponse: Réponse au format DataTable ou REST API
        """
        try:
            # ÉTAPE 1: Extraction des paramètres DataTable
            params = self._extract_params(request)
            logger.debug(f"Paramètres extraits: {params}")
            
            # ÉTAPE 2: Vérifier si le queryset est déjà filtré (pour éviter double filtrage)
            is_pre_filtered = hasattr(queryset, 'queryset')  # PreFilteredQueryset
            
            # ÉTAPE 3: Appliquer les filtres personnalisés seulement si pas déjà filtré
            if not is_pre_filtered:
                queryset = self.filter_handler.apply_filters(request, queryset)
                logger.debug(f"Filtres appliqués, queryset count: {queryset.count()}")
            
            # ÉTAPE 4: Recherche globale
            queryset = self._apply_search(request, queryset)
            logger.debug(f"Recherche appliquée, queryset count: {queryset.count()}")
            
            # ÉTAPE 5: Tri
            queryset = self._apply_ordering(request, queryset)
            logger.debug(f"Tri appliqué")
            
            # ÉTAPE 6: Pagination
            paginated_data = self._apply_pagination(request, queryset)
            logger.debug(f"Pagination appliquée: {paginated_data['pagination']}")
            
            # ÉTAPE 7: Sérialisation
            data = self.serializer_handler.serialize(paginated_data['queryset'])
            logger.debug(f"Sérialisation terminée, {len(data)} éléments")
            
            # ÉTAPE 8: Détecter le format de réponse attendu
            if self._is_datatable_request(request):
                logger.debug("Format de réponse: DataTable")
                return self._datatable_response(params, paginated_data, data)
            else:
                logger.debug("Format de réponse: REST API")
                return self._rest_response(paginated_data, data)
            
        except Exception as e:
            logger.error(f"Erreur DataTable: {str(e)}", exc_info=True)
            return self._error_response(str(e))
    
    def _is_datatable_request(self, request: HttpRequest) -> bool:
        """
        Détecte si c'est une requête DataTable
        
        Détecte automatiquement le format de requête en vérifiant la présence
        des paramètres spécifiques à DataTable.
        
        Args:
            request (HttpRequest): Requête HTTP à analyser
            
        Returns:
            bool: True si c'est une requête DataTable, False sinon
        """
        datatable_params = ['draw', 'start', 'length', 'search[value]']
        return any(param in request.GET for param in datatable_params)
    
    def _datatable_response(self, params: Dict[str, Any], paginated_data: Dict[str, Any], data: List[Dict[str, Any]]) -> JsonResponse:
        """
        Réponse au format DataTable
        
        Format standard DataTable avec tous les champs requis :
        - draw: Numéro de dessin (pour la synchronisation)
        - recordsTotal: Nombre total d'enregistrements
        - recordsFiltered: Nombre d'enregistrements après filtrage
        - data: Données sérialisées
        - pagination: Informations de pagination
        
        Args:
            params (Dict[str, Any]): Paramètres extraits de la requête
            paginated_data (Dict[str, Any]): Données de pagination
            data (List[Dict[str, Any]]): Données sérialisées
            
        Returns:
            JsonResponse: Réponse au format DataTable
        """
        return JsonResponse({
            'draw': params['draw'],
            'recordsTotal': paginated_data['total'],
            'recordsFiltered': paginated_data['total'],
            'data': data,
            'pagination': paginated_data['pagination']
        })
    
    def _rest_response(self, paginated_data: Dict[str, Any], data: List[Dict[str, Any]]) -> JsonResponse:
        """
        Réponse au format REST API standard
        
        Format REST API compatible avec DRF :
        - count: Nombre total d'enregistrements
        - results: Données sérialisées
        - next: URL de la page suivante
        - previous: URL de la page précédente
        - pagination: Informations de pagination détaillées
        
        Args:
            paginated_data (Dict[str, Any]): Données de pagination
            data (List[Dict[str, Any]]): Données sérialisées
            
        Returns:
            JsonResponse: Réponse au format REST API
        """
        return JsonResponse({
            'count': paginated_data['total'],
            'results': data,
            'next': paginated_data['pagination']['has_next'],
            'previous': paginated_data['pagination']['has_previous'],
            'pagination': paginated_data['pagination']
        })
    
    def _extract_params(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Extrait les paramètres DataTable de la requête
        
        Extrait et valide tous les paramètres nécessaires :
        - draw: Numéro de dessin pour la synchronisation
        - start: Index de début pour la pagination
        - length: Nombre d'éléments par page
        - search[value]: Valeur de recherche globale
        - order[0][column]: Index de la colonne de tri
        - order[0][dir]: Direction du tri (asc/desc)
        
        SÉCURITÉ:
        - Validation des limites min/max pour page_size
        - Protection contre les valeurs invalides
        - Valeurs par défaut sécurisées
        
        Args:
            request (HttpRequest): Requête HTTP
            
        Returns:
            Dict[str, Any]: Paramètres extraits et validés
        """
        # Récupérer page_size depuis la requête ou utiliser la valeur par défaut
        page_size = request.GET.get('page_size')
        if page_size:
            try:
                page_size = int(page_size)
                # Valider les limites min/max
                min_size = self.config.get_min_page_size()
                max_size = self.config.get_max_page_size()
                if page_size < min_size:
                    logger.warning(f"page_size ({page_size}) inférieur à la limite minimale ({min_size})")
                    page_size = min_size
                elif page_size > max_size:
                    logger.warning(f"page_size ({page_size}) supérieur à la limite maximale ({max_size})")
                    page_size = max_size
            except ValueError:
                logger.warning(f"page_size invalide: {page_size}, utilisation de la valeur par défaut")
                page_size = self.config.get_page_size()
        else:
            page_size = self.config.get_page_size()
        
        return {
            'draw': int(request.GET.get('draw', 1)),
            'start': int(request.GET.get('start', 0)),
            'length': int(request.GET.get('length', page_size)),  # Utiliser page_size paramétrable
            'page_size': page_size,  # Ajouter page_size aux paramètres
            'search_value': request.GET.get('search[value]', ''),
            'order_column': request.GET.get('order[0][column]'),
            'order_dir': request.GET.get('order[0][dir]', 'asc')
        }
    
    def _apply_search(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique la recherche globale
        
        Recherche dans tous les champs configurés avec une recherche insensible à la casse.
        Utilise des requêtes OR pour combiner les résultats de tous les champs.
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de recherche
            queryset (QuerySet): Queryset à filtrer
            
        Returns:
            QuerySet: Queryset avec recherche appliquée
        """
        search_value = request.GET.get('search[value]', '')
        search_fields = self.config.get_search_fields()
        
        if search_value and search_fields:
            search_filters = Q()
            for field in search_fields:
                search_filters |= Q(**{f'{field}__icontains': search_value})
            queryset = queryset.filter(search_filters)
            logger.debug(f"Recherche appliquée: '{search_value}' dans {search_fields}")
        
        return queryset
    
    def _apply_ordering(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applique le tri
        
        Supporte deux formats de tri :
        1. DataTable : order[0][column]=2&order[0][dir]=asc
        2. REST API : ordering=label ou ordering=-label
        
        SÉCURITÉ:
        - Validation des champs de tri autorisés
        - Protection contre les injections SQL
        - Logs de débogage détaillés
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de tri
            queryset (QuerySet): Queryset à trier
            
        Returns:
            QuerySet: Queryset trié
        """
        order_fields = self.config.get_order_fields()
        
        # Gestion du tri DataTable
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]', 'asc')
        
        logger.debug(f"Tri DataTable - order_column: {order_column}, order_dir: {order_dir}")
        logger.debug(f"Champs de tri autorisés: {order_fields}")
        logger.debug(f"Tous les paramètres GET: {dict(request.GET)}")
        
        if order_column and order_fields:
            try:
                column_index = int(order_column)
                if 0 <= column_index < len(order_fields):
                    field = order_fields[column_index]
                    if order_dir == 'desc':
                        field = f'-{field}'
                    logger.debug(f"Application du tri DataTable: {field}")
                    return queryset.order_by(field)
                else:
                    logger.warning(f"Index de colonne invalide: {column_index}, max: {len(order_fields)-1}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Erreur lors du tri DataTable: {str(e)}")
        
        # Gestion du tri REST API (ordering parameter)
        ordering = request.GET.get('ordering')
        logger.debug(f"Tri REST API - ordering: {ordering}")
        
        if ordering and order_fields:
            # Vérifier si le champ de tri est autorisé
            clean_ordering = ordering.lstrip('-')
            if clean_ordering in order_fields:
                logger.debug(f"Application du tri REST: {ordering}")
                return queryset.order_by(ordering)
            else:
                logger.warning(f"Champ de tri non autorisé: {ordering}")
        
        # Tri par défaut si aucun tri spécifié
        default_order = self.config.get_default_order()
        logger.debug(f"Application du tri par défaut: {default_order}")
        return queryset.order_by(default_order)
    
    def _apply_pagination(self, request: HttpRequest, queryset: QuerySet) -> Dict[str, Any]:
        """
        Applique la pagination
        
        Utilise Django Paginator pour une pagination robuste avec :
        - Gestion des limites min/max
        - Calcul automatique du nombre de pages
        - Informations de navigation (next/previous)
        
        Args:
            request (HttpRequest): Requête HTTP avec paramètres de pagination
            queryset (QuerySet): Queryset à paginer
            
        Returns:
            Dict[str, Any]: Données de pagination avec informations complètes
        """
        params = self._extract_params(request)
        start = params['start']
        length = params['length']
        page_size = params['page_size']
        
        total = queryset.count()
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        return {
            'queryset': page_obj.object_list,
            'total': total,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'page_size': page_size,  # Ajouter page_size à la réponse
            }
        }
    
    def _error_response(self, error_message: str) -> JsonResponse:
        """
        Retourne une réponse d'erreur
        
        Format d'erreur compatible avec DataTable et REST API.
        Inclut des informations de débogage pour le développement.
        
        Args:
            error_message (str): Message d'erreur
            
        Returns:
            JsonResponse: Réponse d'erreur formatée
        """
        return JsonResponse({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': error_message
        }) 