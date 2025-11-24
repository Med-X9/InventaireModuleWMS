"""
Mixins et utilitaires pour DataTable ServerSide

Ce module fournit des mixins et des utilitaires pour intégrer facilement
les fonctionnalités DataTable dans les vues Django REST Framework.

PRINCIPES DRY/SOLID:
- DRY (Don't Repeat Yourself) : Réutilisation maximale du code
- SOLID : Séparation des responsabilités et extensibilité
- Interface cohérente pour toutes les vues DataTable

FONCTIONNALITÉS:
- Mixins réutilisables pour les vues DataTable
- Détection automatique des requêtes DataTable
- Configuration flexible et extensible
- Intégration transparente avec Django REST Framework
- Support des filtres Django Filter
- Optimisations de performance automatiques

UTILISATION RAPIDE:
    class MyListView(ServerSideDataTableView):
        model = MyModel
        serializer_class = MySerializer
        search_fields = ['name', 'description']
        order_fields = ['id', 'name', 'created_at']
        
    # Ou avec django-filter:
    class MyListView(ServerSideDataTableView):
        model = MyModel
        serializer_class = MySerializer
        filterset_class = MyFilterSet
        search_fields = ['name', 'description']
        order_fields = ['id', 'name', 'created_at']
"""

import logging
from typing import Type, List, Dict, Any, Optional, Union
from django.http import HttpRequest
from django.db.models import QuerySet, Model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import FilterSet

from .base import DataTableConfig, DataTableProcessor, IDataTableFilter, IDataTableSerializer
from .filters import DjangoFilterDataTableFilter, DateRangeFilter, StatusFilter, CompositeDataTableFilter, FilterMappingFilter
from .serializers import DataTableSerializer
from .exporters import export_manager
from .request_handler import RequestFormatDetector, RequestParameterExtractor

logger = logging.getLogger(__name__)

def is_datatable_request(request: HttpRequest) -> bool:
    """
    Détecte si une requête est une requête DataTable.
    
    DEPRECATED: Use RequestFormatDetector.is_datatable_request() instead.
    Kept for backward compatibility.
    """
    return RequestFormatDetector.is_datatable_request(request)
    """
    Détecte si une requête est une requête DataTable
    
    Vérifie la présence des paramètres DataTable typiques :
    - draw: Paramètre de requête DataTable
    - start: Index de début de pagination
    - length: Nombre d'éléments par page
    - order[0][column]: Colonne de tri
    - search[value]: Valeur de recherche
    
    Args:
        request (HttpRequest): Requête HTTP à analyser
        
    Returns:
        bool: True si c'est une requête DataTable, False sinon
        
    EXEMPLE:
        # Requête DataTable
        GET /api/inventories/?draw=1&start=0&length=10&order[0][column]=2&order[0][dir]=asc
        
        # Requête REST API normale
        GET /api/inventories/?page=1&page_size=10&ordering=name
    """
    if not request or not hasattr(request, 'GET'):
        return False
    
    datatable_params = [
        'draw', 'start', 'length', 
        'order[0][column]', 'order[0][dir]',
        'search[value]', 'search[regex]'
    ]
    
    return any(param in request.GET for param in datatable_params)

def datatable_view(view_class: Type[APIView]) -> Type[APIView]:
    """
    Décorateur pour transformer une vue en vue DataTable
    
    Ce décorateur ajoute automatiquement les fonctionnalités DataTable
    à une vue existante sans modifier son code.
    
    PRINCIPE DRY : Réutilisation du code existant
    PRINCIPE SOLID : Extension sans modification
    
    Args:
        view_class (Type[APIView]): Classe de vue à transformer
        
    Returns:
        Type[APIView]: Classe de vue avec fonctionnalités DataTable
        
    UTILISATION:
        @datatable_view
        class MyListView(APIView):
            def get(self, request):
                # Code existant...
                pass
    """
    if not issubclass(view_class, APIView):
        raise ValueError(f"La classe {view_class.__name__} doit hériter de APIView")
    
    class DataTableWrapper(view_class):
        def get(self, request, *args, **kwargs):
            if is_datatable_request(request):
                return self.handle_datatable_request(request, *args, **kwargs)
            return super().get(request, *args, **kwargs)
        
        def handle_datatable_request(self, request, *args, **kwargs):
            """Gère les requêtes DataTable"""
            try:
                # Configuration par défaut
                config = DataTableConfig(
                    search_fields=getattr(self, 'search_fields', []),
                    order_fields=getattr(self, 'order_fields', []),
                    default_order=getattr(self, 'default_order', '-id'),
                    page_size=getattr(self, 'page_size', 20),
                    min_page_size=getattr(self, 'min_page_size', 1),
                    max_page_size=getattr(self, 'max_page_size', 1000)
                )
                
                # Queryset par défaut
                queryset = self.get_queryset() if hasattr(self, 'get_queryset') else self.model.objects.all()
                
                # Processeur DataTable
                processor = DataTableProcessor(
                    config=config,
                    filter_handler=self.get_datatable_filter(),
                    serializer_handler=self.get_datatable_serializer()
                )
                
                return processor.process(request, queryset)
            except Exception as e:
                logger.error(f"Erreur lors du traitement DataTable: {str(e)}")
                return Response(
                    {"error": "Erreur lors du traitement de la requête DataTable"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        def get_datatable_filter(self):
            """Filtre DataTable par défaut"""
            filterset_class = getattr(self, 'filterset_class', None)
            if filterset_class:
                return DjangoFilterDataTableFilter(filterset_class)
            return None
        
        def get_datatable_serializer(self):
            """Sérialiseur DataTable par défaut"""
            serializer_class = getattr(self, 'serializer_class', None)
            return DataTableSerializer(serializer_class)
    
    return DataTableWrapper

def quick_datatable_view(model_cls: Type[Model] = None,
                        serializer_cls: Type = None,
                        filterset_cls: Type[FilterSet] = None,
                        search_fields_list: List[str] = None,
                        order_fields_list: List[str] = None,
                        default_order_str: str = '-id',
                        page_size_int: int = 20,
                        min_page_size_int: int = 1,
                        max_page_size_int: int = 1000) -> Type[APIView]:
    """
    Crée rapidement une vue DataTable complète
    
    Cette fonction permet de créer une vue DataTable avec une configuration
    minimale, en utilisant des valeurs par défaut intelligentes.
    
    PRINCIPE DRY : Configuration rapide avec valeurs par défaut
    PRINCIPE SOLID : Configuration flexible et extensible
    
    Args:
        model_cls (Type[Model], optional): Classe du modèle Django
        serializer_cls (Type, optional): Classe de sérialiseur DRF
        filterset_cls (Type[FilterSet], optional): Classe FilterSet Django Filter
        search_fields_list (List[str], optional): Champs de recherche
        order_fields_list (List[str], optional): Champs de tri
        default_order_str (str): Tri par défaut
        page_size_int (int): Taille de page par défaut
        min_page_size_int (int): Taille de page minimale
        max_page_size_int (int): Taille de page maximale
        
    Returns:
        Type[APIView]: Classe de vue DataTable complète
        
    UTILISATION:
        # Vue simple
        InventoryView = quick_datatable_view(
            model_cls=Inventory,
            serializer_cls=InventorySerializer,
            search_fields_list=['name', 'description'],
            order_fields_list=['id', 'name', 'created_at']
        )
        
        # Vue avec django-filter
        InventoryView = quick_datatable_view(
            model_cls=Inventory,
            serializer_cls=InventorySerializer,
            filterset_cls=InventoryFilter,
            search_fields_list=['name', 'description'],
            order_fields_list=['id', 'name', 'created_at']
        )
    """
    # Validation des paramètres
    if model_cls and not issubclass(model_cls, Model):
        raise ValueError(f"model_cls doit être une classe Django Model, reçu: {type(model_cls)}")
    
    if page_size_int < min_page_size_int or page_size_int > max_page_size_int:
        raise ValueError(f"page_size_int ({page_size_int}) doit être entre min_page_size_int ({min_page_size_int}) et max_page_size_int ({max_page_size_int})")
    
    class QuickDataTableView(APIView):
        model = model_cls
        serializer_class = serializer_cls
        filterset_class = filterset_cls
        search_fields = search_fields_list or []
        order_fields = order_fields_list or []
        default_order = default_order_str
        page_size = page_size_int
        min_page_size = min_page_size_int
        max_page_size = max_page_size_int
        
        def get(self, request, *args, **kwargs):
            if is_datatable_request(request):
                return self.handle_datatable_request(request, *args, **kwargs)
            return self.handle_rest_request(request, *args, **kwargs)
        
        def handle_datatable_request(self, request, *args, **kwargs):
            """Gère les requêtes DataTable"""
            try:
                config = DataTableConfig(
                    search_fields=self.search_fields,
                    order_fields=self.order_fields,
                    default_order=self.default_order,
                    page_size=self.page_size,
                    min_page_size=self.min_page_size,
                    max_page_size=self.max_page_size
                )
                
                queryset = self.get_queryset()
                processor = DataTableProcessor(
                    config=config,
                    filter_handler=self.get_datatable_filter(),
                    serializer_handler=self.get_datatable_serializer()
                )
                
                return processor.process(request, queryset)
            except Exception as e:
                logger.error(f"Erreur lors du traitement DataTable: {str(e)}")
                return Response(
                    {"error": "Erreur lors du traitement de la requête DataTable"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        def handle_rest_request(self, request, *args, **kwargs):
            """Gère les requêtes REST API normales"""
            try:
                queryset = self.get_queryset()
                
                # Appliquer les filtres si disponible
                filter_handler = self.get_datatable_filter()
                if filter_handler:
                    queryset = filter_handler.apply_filters(request, queryset)
                
                # Appliquer le tri REST API
                ordering = request.GET.get('ordering')
                if ordering:
                    # Vérifier si le champ de tri est autorisé
                    clean_ordering = ordering.lstrip('-')
                    if clean_ordering in self.order_fields:
                        logger.debug(f"Application du tri REST: {ordering}")
                        queryset = queryset.order_by(ordering)
                    else:
                        logger.warning(f"Champ de tri non autorisé: {ordering}")
                else:
                    # Tri par défaut si aucun tri spécifié
                    logger.debug(f"Application du tri par défaut: {self.default_order}")
                    queryset = queryset.order_by(self.default_order)
                
                # Pagination simple
                try:
                    page = max(1, int(request.GET.get('page', 1)))
                    page_size = min(max(self.min_page_size, int(request.GET.get('page_size', self.page_size))), self.max_page_size)
                except (ValueError, TypeError):
                    page = 1
                    page_size = self.page_size
                
                start = (page - 1) * page_size
                end = start + page_size
                
                data = queryset[start:end]
                total_count = queryset.count()
                
                if self.serializer_class:
                    serializer = self.serializer_class(data, many=True)
                    return Response({
                        'count': total_count,
                        'results': serializer.data,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': (total_count + page_size - 1) // page_size
                    })
                else:
                    return Response({
                        'count': total_count,
                        'results': list(data.values()),
                        'page': page,
                        'page_size': page_size,
                        'total_pages': (total_count + page_size - 1) // page_size
                    })
            except Exception as e:
                logger.error(f"Erreur lors du traitement REST API: {str(e)}")
                return Response(
                    {"error": "Erreur lors du traitement de la requête REST API"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        def get_queryset(self):
            """Retourne le queryset de base"""
            if self.model:
                return self.model.objects.all()
            return QuerySet().none()
        
        def get_datatable_filter(self):
            """Filtre DataTable avec support django-filter"""
            if self.filterset_class:
                return DjangoFilterDataTableFilter(self.filterset_class)
            return None
        
        def get_datatable_serializer(self):
            """Sérialiseur DataTable"""
            return DataTableSerializer(self.serializer_class)
    return QuickDataTableView

class DataTableMixin:
    """
    Mixin pour ajouter les fonctionnalités DataTable à une vue
    
    Ce mixin fournit toutes les fonctionnalités DataTable de base :
    - Détection automatique des requêtes DataTable
    - Configuration flexible
    - Support des filtres et sérialiseurs personnalisés
    - Intégration transparente avec DRF
    
    PRINCIPE DRY : Réutilisation des fonctionnalités DataTable
    PRINCIPE SOLID : Séparation des responsabilités
    
    UTILISATION:
        class MyListView(DataTableMixin, APIView):
            def get_datatable_config(self):
                return DataTableConfig(...)
            
            def get_datatable_queryset(self):
                return MyModel.objects.all()
    """
    
    def get(self, request, *args, **kwargs):
        """Gère les requêtes GET avec détection Export/DataTable automatique"""
        # Vérifier si c'est une demande d'export
        export_format = request.GET.get('export')
        if export_format and self.is_export_enabled():
            return self.handle_export_request(request, export_format, *args, **kwargs)
        
        # Sinon, traiter comme requête DataTable normale
        if is_datatable_request(request):
            return self.handle_datatable_request(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)
    
    def _is_query_model_request(self, request) -> bool:
        """
        Détecte si la requête utilise le format QueryModel.
        
        Utilise RequestFormatDetector pour la détection (SOLID - Dependency Inversion).
        """
        return RequestFormatDetector.is_query_model_request(request)
    
    def _get_column_field_mapping_for_querymodel(self) -> Dict[str, str]:
        """
        Crée un mapping column_field_mapping pour QueryModel depuis order_fields.
        
        Utilise order_fields pour créer un mapping col_id -> field_name.
        Si filter_aliases existe, l'utilise aussi.
        """
        mapping = {}
        
        # Utiliser filter_aliases si disponible (plus précis)
        if hasattr(self, 'filter_aliases') and self.filter_aliases:
            mapping.update(self.filter_aliases)
        
        # Ajouter order_fields comme mapping direct (col_id = field_name)
        if hasattr(self, 'order_fields') and self.order_fields:
            for field in self.order_fields:
                if field not in mapping:
                    mapping[field] = field
        
        # Ajouter search_fields aussi
        if hasattr(self, 'search_fields') and self.search_fields:
            for field in self.search_fields:
                if field not in mapping:
                    mapping[field] = field
        
        return mapping
    
    def _handle_querymodel_request(self, request, queryset, *args, **kwargs):
        """
        Gère une requête QueryModel avec les engines.
        
        Utilise FilterEngine, SortEngine et PaginationEngine pour traiter QueryModel.
        Supporte aussi la recherche globale via query params ou request.data.
        """
        from apps.core.datatables.models import QueryModel, FilterModelItem, FilterType, FilterOperator
        from apps.core.datatables.engines import FilterEngine, SortEngine, PaginationEngine
        from django.db.models import Q
        
        logger = logging.getLogger(__name__)
        
        try:
            # Parser QueryModel
            query_model = QueryModel.from_request(request)
            logger.debug(f"🔧 QueryModel détecté: sortModel={len(query_model.sort_model)}, filterModel={len(query_model.filter_model)}")
            
            # Gérer la recherche globale (DRY - utilise RequestParameterExtractor)
            search_value = RequestParameterExtractor.get_search_value(request)
            
            # Appliquer la recherche globale si présente
            if search_value and hasattr(self, 'search_fields') and self.search_fields:
                search_clean = search_value.strip()
                if search_clean:
                    search_query = Q()
                    for field in self.search_fields:
                        search_query |= Q(**{f"{field}__icontains": search_clean})
                    queryset = queryset.filter(search_query)
                    logger.debug(f"🔧 Recherche globale appliquée: '{search_clean}' dans {self.search_fields}")
            
            # Créer le mapping colonnes -> champs
            column_mapping = self._get_column_field_mapping_for_querymodel()
            
            # Appliquer les filtres avec FilterEngine
            if query_model.filter_model:
                filter_engine = FilterEngine(column_mapping)
                queryset = filter_engine.apply_filters(queryset, query_model.filter_model)
                logger.debug(f"🔧 Filtres QueryModel appliqués: {queryset.count()} éléments")
            
            # Appliquer le tri avec SortEngine
            if query_model.sort_model:
                sort_engine = SortEngine(column_mapping)
                queryset = sort_engine.apply_sorting(queryset, query_model.sort_model)
                logger.debug(f"🔧 Tri QueryModel appliqué")
            elif hasattr(self, 'default_order') and self.default_order:
                # Appliquer le tri par défaut si aucun tri dans QueryModel
                queryset = queryset.order_by(self.default_order)
            
            # Paginer avec PaginationEngine
            pagination_engine = PaginationEngine(
                default_page_size=self.page_size,
                max_page_size=self.max_page_size
            )
            pagination_result = pagination_engine.paginate(
                queryset,
                start_row=query_model.start_row,
                end_row=query_model.end_row
            )
            
            paginated_queryset = pagination_result['queryset']
            total_count = pagination_result['total_count']
            
            # Sérialiser
            serializer = self.serializer_class(paginated_queryset, many=True)
            
            # Réponse DataTable (DRY - utilise RequestParameterExtractor)
            response_data = {
                'draw': RequestParameterExtractor.get_draw_value(request),
                'recordsTotal': total_count,
                'recordsFiltered': total_count,
                'data': serializer.data
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement QueryModel: {str(e)}", exc_info=True)
            raise
    
    def handle_datatable_request(self, request, *args, **kwargs):
        """
        Gère les requêtes DataTable avec support QueryModel et format standard.
        
        Détecte automatiquement le format :
        - QueryModel : POST JSON ou GET avec sortModel/filterModel
        - Format standard : Query params DataTable/REST API
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🚀 DataTable: {request.GET.get('affectation_personne_full_name_exact', 'sans filtre')}")
        
        try:
            # S'assurer que les champs sont détectés automatiquement si nécessaire
            self._auto_detect_fields()
            
            # Queryset de base
            queryset = self.get_datatable_queryset()
            if queryset is None:
                logger.warning("get_datatable_queryset() returned None; using empty queryset")
                queryset = self.model.objects.none()
            
            # PRIORITÉ 1: Vérifier si c'est une requête QueryModel
            if self._is_query_model_request(request):
                logger.debug("🔧 Format QueryModel détecté - Utilisation des engines")
                return self._handle_querymodel_request(request, queryset, *args, **kwargs)
            
            # PRIORITÉ 2: Format standard (query params)
            logger.debug("🔧 Format standard détecté - Utilisation du parsing direct")
            
            # Appliquer les filtres Django Filter si configuré (en premier)
            if self.filterset_class:
                logger.debug(f"🔧 Django Filter: {queryset.count()} éléments avant")
                filterset = self.filterset_class(request.GET, queryset=queryset)
                queryset = filterset.qs
                logger.debug(f"🔧 Django Filter: {queryset.count()} éléments après")
                
                # Debug: vérifier si le filtre affectation_personne_full_name_exact existe dans Django Filter
                if 'affectation_personne_full_name_exact' in request.GET:
                    logger.debug(f"🔧 Django Filter cherche: affectation_personne_full_name_exact")
                    logger.debug(f"🔧 Champs disponibles dans Django Filter: {list(filterset.filters.keys())}")
            else:
                logger.debug(f"ℹ️  Aucun filterset_class configuré - Utilisation DataTable uniquement")

            # Appliquer tous les filtres via le filtre composite (inclut DataTableColumnFilter)
            logger.debug(f"🔧 Filtres composites: {queryset.count()} éléments avant")
            filter_handler = self.get_datatable_filter()
            if filter_handler:
                queryset = filter_handler.apply_filters(request, queryset)
            logger.debug(f"🔧 Filtres composites: {queryset.count()} éléments après")
            
            # Recherche globale
            queryset = self.apply_search_direct(queryset, request)
            
            # Tri
            queryset = self.apply_ordering_direct(queryset, request)
            
            # Pagination
            page, page_size = self.get_pagination_from_request(request)
            start = (page - 1) * page_size
            end = start + page_size
            
            total_count = queryset.count()
            data = queryset[start:end]
            
            # Sérialisation
            serializer = self.serializer_class(data, many=True)
            
            # Réponse DataTable
            response_data = {
                'draw': int(request.GET.get('draw', 1)),
                'recordsTotal': total_count,
                'recordsFiltered': total_count,
                'data': serializer.data
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement DataTable: {str(e)}", exc_info=True)
            return Response(
                {"error": "Erreur lors du traitement de la requête DataTable"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_datatable_config(self) -> DataTableConfig:
        """Configuration DataTable - à surcharger"""
        return DataTableConfig(
            search_fields=getattr(self, 'search_fields', []),
            order_fields=getattr(self, 'order_fields', []),
            default_order=getattr(self, 'default_order', '-id'),
            page_size=getattr(self, 'page_size', 20),
            min_page_size=getattr(self, 'min_page_size', 1),
            max_page_size=getattr(self, 'max_page_size', 1000)
        )
    
    def get_datatable_queryset(self) -> QuerySet:
        """Queryset DataTable - à surcharger"""
        if hasattr(self, 'model'):
            return self.model.objects.all()
        return QuerySet()
    
    def get_datatable_filter(self) -> Optional[IDataTableFilter]:
        """Filtre DataTable - à surcharger"""
        if hasattr(self, 'filterset_class'):
            return DjangoFilterDataTableFilter(self.filterset_class)
        return None
    
    def get_datatable_serializer(self) -> IDataTableSerializer:
        """Sérialiseur DataTable - à surcharger"""
        return DataTableSerializer(getattr(self, 'serializer_class', None))
    
    # =========================================================================
    # MÉTHODES D'EXPORT
    # =========================================================================
    
    def is_export_enabled(self) -> bool:
        """
        Vérifie si l'export est activé pour cette vue
        
        Par défaut, l'export est activé. Peut être désactivé en définissant
        enable_export = False dans la vue.
        
        Returns:
            bool: True si l'export est activé
        """
        return getattr(self, 'enable_export', True)
    
    def get_export_formats(self) -> List[str]:
        """
        Retourne la liste des formats d'export supportés
        
        Par défaut: ['excel', 'csv']
        Peut être personnalisé en définissant export_formats dans la vue
        
        Returns:
            List[str]: Liste des formats supportés
        """
        return getattr(self, 'export_formats', ['excel', 'csv'])
    
    def get_export_filename(self, format_name: str) -> str:
        """
        Génère le nom du fichier d'export
        
        Par défaut: export_<timestamp>
        Peut être personnalisé en définissant export_filename dans la vue
        
        Args:
            format_name: Format d'export ('excel', 'csv', etc.)
            
        Returns:
            str: Nom du fichier sans extension
        """
        from datetime import datetime
        
        base_filename = getattr(self, 'export_filename', 'export')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{base_filename}_{timestamp}"
    
    def handle_export_request(self, request, export_format: str, *args, **kwargs):
        """
        Gère les requêtes d'export
        
        Args:
            request: Requête HTTP
            export_format: Format d'export demandé ('excel', 'csv', etc.)
            
        Returns:
            HttpResponse avec le fichier à télécharger
        """
        logger.info(f"Requête d'export: format={export_format}")
        
        try:
            # Vérifier que le format est supporté
            if export_format not in self.get_export_formats():
                return Response(
                    {
                        "error": f"Format d'export non supporté: {export_format}",
                        "supported_formats": self.get_export_formats()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtenir le queryset avec tous les filtres appliqués
            queryset = self.get_export_queryset(request, *args, **kwargs)
            
            # Obtenir le serializer
            serializer_class = getattr(self, 'serializer_class', None)
            
            # Générer le nom du fichier
            filename = self.get_export_filename(export_format)
            
            # Exporter
            logger.info(f"Export de {queryset.count()} éléments vers {export_format}")
            return export_manager.export(
                format_name=export_format,
                queryset=queryset,
                serializer_class=serializer_class,
                filename=filename
            )
            
        except ValueError as e:
            logger.error(f"Erreur de validation lors de l'export: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Erreur lors de l'export: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_export_queryset(self, request, *args, **kwargs) -> QuerySet:
        """
        Obtient le queryset pour l'export avec tous les filtres appliqués
        
        Cette méthode applique les mêmes filtres que pour l'affichage DataTable,
        mais retourne TOUTES les lignes (pas de pagination).
        
        Args:
            request: Requête HTTP avec paramètres de filtrage
            
        Returns:
            QuerySet: Queryset filtré complet
        """
        # Queryset de base
        queryset = self.get_datatable_queryset()
        if queryset is None:
            queryset = self.model.objects.none()
        
        # Appliquer les filtres Django Filter si configuré
        if hasattr(self, 'filterset_class') and self.filterset_class:
            filterset = self.filterset_class(request.GET, queryset=queryset)
            queryset = filterset.qs
        
        # Appliquer le mapping des filtres
        queryset = self.apply_filter_mapping_direct(queryset, request)
        
        # Appliquer la recherche globale
        queryset = self.apply_search_direct(queryset, request)
        
        # Appliquer le tri
        queryset = self.apply_ordering_direct(queryset, request)
        
        return queryset

class DataTableAPIView(DataTableMixin, APIView):
    """
    Vue API avec fonctionnalités DataTable intégrées
    
    Cette classe combine APIView et DataTableMixin pour fournir
    une vue complète avec support automatique des requêtes DataTable
    et REST API normales.
    
    PRINCIPE DRY : Combinaison de fonctionnalités existantes
    PRINCIPE SOLID : Héritage multiple pour séparation des responsabilités
    
    UTILISATION:
        class MyListView(DataTableAPIView):
            model = MyModel
            serializer_class = MySerializer
            search_fields = ['name', 'description']
            order_fields = ['id', 'name', 'created_at']
    """
    pass

class DataTableListView(DataTableAPIView):
    """
    Vue de liste avec fonctionnalités DataTable intégrées
    
    Cette classe spécialise DataTableAPIView pour les vues de liste
    avec des comportements par défaut optimisés.
    
    PRINCIPE DRY : Réutilisation de DataTableAPIView
    PRINCIPE SOLID : Spécialisation pour les vues de liste
    
    UTILISATION:
        class MyListView(DataTableListView):
            model = MyModel
            serializer_class = MySerializer
            search_fields = ['name', 'description']
            order_fields = ['id', 'name', 'created_at']
    """
    pass

class ServerSideDataTableView(DataTableListView):
    """
    Vue DataTable ServerSide complète avec toutes les fonctionnalités
    
    Cette classe fournit une implémentation complète et rapide pour
    créer des vues DataTable avec support automatique de :
    - Tri sur tous les champs configurés
    - Filtrage avancé avec django-filter
    - Recherche sur champs multiples
    - Pagination optimisée
    - Sérialisation flexible
    - Optimisations de performance
    
    PRINCIPE DRY : Configuration minimale avec valeurs par défaut intelligentes
    PRINCIPE SOLID : Extensibilité et séparation des responsabilités
    
    ATTRIBUTS DE CONFIGURATION:
    - model: Classe du modèle Django
    - serializer_class: Classe de sérialiseur DRF
    - filterset_class: Classe FilterSet Django Filter (optionnel)
    - search_fields: Champs de recherche
    - order_fields: Champs de tri
    - default_order: Tri par défaut
    - page_size: Taille de page par défaut
    - filter_fields: Champs de filtrage automatique
    - date_fields: Champs de date pour filtrage automatique
    - status_fields: Champs de statut pour filtrage automatique
    
    UTILISATION RAPIDE:
        class InventoryListView(ServerSideDataTableView):
            model = Inventory
            serializer_class = InventorySerializer
            search_fields = ['label', 'reference', 'status']
            order_fields = ['id', 'label', 'date', 'created_at', 'status']
            filter_fields = ['status', 'inventory_type']
            date_fields = ['date', 'created_at']
            status_fields = ['status']
    
    UTILISATION AVEC DJANGO-FILTER:
        class InventoryListView(ServerSideDataTableView):
            model = Inventory
            serializer_class = InventorySerializer
            filterset_class = InventoryFilter
            search_fields = ['label', 'reference', 'status']
            order_fields = ['id', 'label', 'date', 'created_at', 'status']
    
    PARAMÈTRES DE REQUÊTE SUPPORTÉS:
    - Tri: ordering=field ou ordering=-field
    - Tri DataTable: order[0][column]=index&order[0][dir]=asc/desc
    - Recherche: search=term
    - Pagination: page=1&page_size=25
    - Filtres: field=value, field_exact=value, field_in=value1,value2
    - Dates: date_exact=YYYY-MM-DD, date_start=YYYY-MM-DD, date_end=YYYY-MM-DD
    - Statuts: status=value, status_in=value1,value2
    """
    
    # Configuration de base
    model = None
    serializer_class = None
    filterset_class = None
    
    # Champs de recherche et tri
    search_fields = []
    order_fields = []
    default_order = '-id'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    # Champs de filtrage automatique
    filter_fields = []
    date_fields = []
    status_fields = []
    
    # Mapping des filtres frontend -> backend
    filter_aliases = {}
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec validation des paramètres"""
        super().__init__(*args, **kwargs)
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Valide la configuration de la vue"""
        if not self.model:
            logger.warning(f"Vue {self.__class__.__name__}: model non défini")
        
        if not self.serializer_class:
            logger.warning(f"Vue {self.__class__.__name__}: serializer_class non défini")
        
        if self.page_size < self.min_page_size or self.page_size > self.max_page_size:
            raise ValueError(
                f"page_size ({self.page_size}) doit être entre "
                f"min_page_size ({self.min_page_size}) et max_page_size ({self.max_page_size})"
            )
    
    def _auto_detect_fields(self):
        """
        Détection automatique des champs depuis le modèle et le serializer.
        
        Détecte automatiquement :
        - search_fields et order_fields depuis le serializer
        - date_fields depuis le modèle (DateTimeField, DateField)
        - status_fields depuis le modèle (CharField avec choices)
        """
        # Détection automatique des champs de date depuis le modèle
        if self.model and not self.date_fields:
            from django.db import models
            date_fields = []
            for field in self.model._meta.get_fields():
                if isinstance(field, (models.DateTimeField, models.DateField)):
                    date_fields.append(field.name)
            if date_fields:
                self.date_fields = date_fields
        
        # Détection automatique des champs de statut depuis le modèle
        if self.model and not self.status_fields:
            from django.db import models
            status_fields = []
            for field in self.model._meta.get_fields():
                if isinstance(field, models.CharField) and hasattr(field, 'choices') and field.choices:
                    status_fields.append(field.name)
            if status_fields:
                self.status_fields = status_fields
        
        # Détection automatique des champs depuis le serializer
        if self.serializer_class and (not self.search_fields or not self.order_fields):
            serializer_fields = []
            
            # Méthode 1 : Depuis Meta.fields
            if hasattr(self.serializer_class, 'Meta') and hasattr(self.serializer_class.Meta, 'fields'):
                serializer_fields = list(self.serializer_class.Meta.fields)
            
            # Méthode 2 : Depuis les champs du serializer
            if not serializer_fields:
                try:
                    serializer_instance = self.serializer_class()
                    serializer_fields = [f for f in serializer_instance.fields.keys() if not f.startswith('get_')]
                except:
                    pass
            
            # Utiliser les champs du serializer pour search et order si non définis
            if not self.search_fields and serializer_fields:
                # Exclure les champs non recherchables
                searchable_fields = [
                    f for f in serializer_fields 
                    if not f.endswith('_id') and f not in ['id', 'pk'] and not f.startswith('get_')
                ]
                self.search_fields = searchable_fields[:15]  # Limiter à 15 champs
            
            if not self.order_fields and serializer_fields:
                # Exclure les champs non triables (SerializerMethodField)
                orderable_fields = [
                    f for f in serializer_fields 
                    if not f.startswith('get_') and f not in ['comptages', 'equipe']
                ]
                self.order_fields = orderable_fields[:20]  # Limiter à 20 champs
    
    def get_datatable_config(self) -> DataTableConfig:
        """Configuration DataTable avec détection automatique et valeurs par défaut intelligentes"""
        # Détection automatique si les champs ne sont pas définis
        self._auto_detect_fields()
        
        return DataTableConfig(
            search_fields=self.search_fields,
            order_fields=self.order_fields,
            default_order=self.default_order,
            page_size=self.page_size,
            min_page_size=self.min_page_size,
            max_page_size=self.max_page_size
        )
    
    def get_datatable_queryset(self) -> QuerySet:
        """Queryset avec optimisations automatiques"""
        if not self.model:
            logger.warning(f"Vue {self.__class__.__name__}: model non défini, retourne QuerySet vide")
            return QuerySet()
        
        queryset = self.model.objects.all()
        
        # Optimisations automatiques si le modèle a des relations
        if hasattr(self.model, 'warehouse'):
            queryset = queryset.select_related('warehouse')
        
        if hasattr(self.model, 'stocks'):
            queryset = queryset.prefetch_related('stocks')
        
        return queryset
    
    def get_datatable_filter(self) -> IDataTableFilter:
        """
        Filtre composite avec tous les types de filtres - GESTION AUTOMATIQUE
        
        Le package gère automatiquement :
        - Filtres de date (date_exact, date_start, date_end) pour tous les date_fields
        - Filtres de statut (status, status_in) pour tous les status_fields
        - Mapping des filtres (filter_aliases) avec tous les opérateurs
        - Filtres de colonnes DataTables (columns[i][search][value])
        """
        composite_filter = CompositeDataTableFilter()
        
        # Filtre Django Filter si configuré (optionnel)
        if self.filterset_class:
            composite_filter.add_filter(DjangoFilterDataTableFilter(self.filterset_class))
        
        # Filtres automatiques pour les champs de date
        for date_field in self.date_fields:
            composite_filter.add_filter(DateRangeFilter(date_field))
        
        # Filtres automatiques pour les champs de statut
        for status_field in self.status_fields:
            composite_filter.add_filter(StatusFilter(status_field))
        
        # Filtre de mapping automatique si filter_aliases est défini
        if self.filter_aliases:
            dynamic_filters = getattr(self, 'dynamic_filters', None)
            composite_filter.add_filter(FilterMappingFilter(self.filter_aliases, dynamic_filters))
        
        # Filtre de colonnes DataTables (columns[i][search][value])
        # Créer le mapping colonne -> champ depuis order_fields et filter_aliases
        column_mapping = {}
        if hasattr(self, 'order_fields') and self.order_fields:
            for field in self.order_fields:
                column_mapping[field] = field
        if hasattr(self, 'filter_aliases') and self.filter_aliases:
            column_mapping.update(self.filter_aliases)
        if hasattr(self, 'search_fields') and self.search_fields:
            for field in self.search_fields:
                if field not in column_mapping:
                    column_mapping[field] = field
        
        from .filters import DataTableColumnFilter
        composite_filter.add_filter(DataTableColumnFilter(column_mapping))
        
        return composite_filter
    
    def get_datatable_filter_with_mapping(self, request):
        """Filtre composite avec mapping des filtres frontend -> backend"""
        composite_filter = CompositeDataTableFilter()
        
        # Filtre Django Filter si configuré
        if self.filterset_class:
            composite_filter.add_filter(DjangoFilterDataTableFilter(self.filterset_class))
        
        # Filtres automatiques pour les champs de date
        for date_field in self.date_fields:
            composite_filter.add_filter(DateRangeFilter(date_field))
        
        # Filtres automatiques pour les champs de statut
        for status_field in self.status_fields:
            composite_filter.add_filter(StatusFilter(status_field))
        
        # Ajouter un filtre de mapping si des alias sont définis
        if self.filter_aliases or hasattr(self, 'dynamic_filters'):
            dynamic_filters = getattr(self, 'dynamic_filters', None)
            composite_filter.add_filter(FilterMappingFilter(self.filter_aliases, dynamic_filters))
        
        # Ajouter un filtre pour les colonnes composées
        if hasattr(self, 'composite_columns'):
            from .filters import CompositeColumnFilter
            composite_filter.add_filter(CompositeColumnFilter(self.composite_columns))
        
        # Filtre de colonnes DataTables (columns[i][search][value])
        # Créer le mapping colonne -> champ depuis order_fields et filter_aliases
        column_mapping = {}
        if hasattr(self, 'order_fields') and self.order_fields:
            for field in self.order_fields:
                column_mapping[field] = field
        if hasattr(self, 'filter_aliases') and self.filter_aliases:
            column_mapping.update(self.filter_aliases)
        if hasattr(self, 'search_fields') and self.search_fields:
            for field in self.search_fields:
                if field not in column_mapping:
                    column_mapping[field] = field
        
        from .filters import DataTableColumnFilter
        composite_filter.add_filter(DataTableColumnFilter(column_mapping))
        
        return composite_filter
    
    def apply_filter_mapping_direct(self, queryset, request):
        """Applique le mapping des filtres directement sur le queryset"""
        if not self.filter_aliases and not hasattr(self, 'dynamic_filters'):
            return queryset
            
        import logging
        logger = logging.getLogger(__name__)
            
        from django.db.models import Q
        from .filters import FilterMappingFilter
        
        # Utiliser FilterMappingFilter pour appliquer tous les filtres
        dynamic_filters = getattr(self, 'dynamic_filters', None)
        
        # Appliquer les filtres de mapping normaux
        filter_handler = FilterMappingFilter(self.filter_aliases, dynamic_filters)
        result = filter_handler.apply_filters(request, queryset)
        
        # Appliquer les filtres de colonnes composées
        if hasattr(self, 'composite_columns'):
            from .filters import CompositeColumnFilter
            composite_handler = CompositeColumnFilter(self.composite_columns)
            result = composite_handler.apply_filters(request, result)
        
        return result
    
    def apply_search_direct(self, queryset, request):
        """Applique la recherche globale directement sur le queryset"""
        search = request.GET.get('search[value]', '')
        
        if not search:
            return queryset
        
        # S'assurer que search_fields est défini
        if not hasattr(self, 'search_fields') or not self.search_fields:
            # Essayer de détecter automatiquement depuis la config
            config = self.get_datatable_config()
            search_fields = config.get_search_fields()
            if not search_fields:
                logger.debug("⚠️ Aucun search_fields configuré - recherche globale ignorée")
                return queryset
        else:
            search_fields = self.search_fields
            
        from django.db.models import Q
        
        # Nettoyer la recherche
        search_clean = search.replace('+', ' ').strip()
        if not search_clean:
            return queryset
        
        # Recherche dans tous les champs configurés
        search_query = Q()
        for field in search_fields:
            try:
                search_query |= Q(**{f"{field}__icontains": search_clean})
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de l'ajout du champ '{field}' à la recherche: {e}")
                continue
        
        if search_query:
            queryset = queryset.filter(search_query)
            logger.debug(f"🔍 Recherche globale appliquée: '{search_clean}' dans {search_fields}")
        
        return queryset
    
    def apply_ordering_direct(self, queryset, request):
        """Applique le tri directement sur le queryset"""
        # Vérifier les paramètres DataTable
        if 'order[0][column]' in request.GET:
            try:
                column_index = int(request.GET.get('order[0][column]', 0))
                direction = request.GET.get('order[0][dir]', 'asc')
                
                if 0 <= column_index < len(self.order_fields):
                    field = self.order_fields[column_index]
                    ordering = f"-{field}" if direction == 'desc' else field
                    return queryset.order_by(ordering)
            except (ValueError, IndexError):
                pass
        
        # Fallback vers paramètre REST API
        ordering = request.GET.get('ordering', self.default_order)
        if ordering:
            return queryset.order_by(ordering)
        
        return queryset.order_by(self.default_order)
    
    def get_pagination_from_request(self, request):
        """Convertit les paramètres de pagination DataTable ou REST API"""
        # Vérifier les paramètres DataTable
        if 'start' in request.GET and 'length' in request.GET:
            try:
                start = int(request.GET.get('start', 0))
                length = int(request.GET.get('length', self.page_size))
                length = min(max(self.min_page_size, length), self.max_page_size)
                page = (start // length) + 1
                return page, length
            except (ValueError, TypeError):
                pass
        
        # Fallback vers paramètres REST API
        try:
            page = max(1, int(request.GET.get('page', 1)))
            page_size = min(max(self.min_page_size, int(request.GET.get('page_size', self.page_size))), self.max_page_size)
            return page, page_size
        except (ValueError, TypeError):
            return 1, self.page_size
    
    def get_datatable_serializer(self) -> IDataTableSerializer:
        """Sérialiseur avec fallback intelligent"""
        return DataTableSerializer(self.serializer_class)
    
    def get(self, request, *args, **kwargs):
        """Gère les requêtes GET avec détection automatique et mapping des filtres"""
        # PRIORITÉ 1: Vérifier si c'est une demande d'export
        export_format = request.GET.get('export')
        if export_format and hasattr(self, 'is_export_enabled') and self.is_export_enabled():
            if hasattr(self, 'handle_export_request'):
                return self.handle_export_request(request, export_format, *args, **kwargs)
        
        # PRIORITÉ 2: Vérifier si c'est une requête DataTable
        if is_datatable_request(request):
            return self.handle_datatable_request(request, *args, **kwargs)
        
        # PRIORITÉ 3: Traiter comme requête REST normale
        else:
            return self.handle_rest_request(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """
        Gère les requêtes POST avec support QueryModel (JSON body).
        
        SOLID - Single Responsibility: Routes POST requests
        KISS: Simple routing logic
        """
        # PRIORITÉ 1: Vérifier si c'est une demande d'export
        export_format = RequestParameterExtractor.get_export_format(request)
        if export_format and hasattr(self, 'is_export_enabled') and self.is_export_enabled():
            if hasattr(self, 'handle_export_request'):
                return self.handle_export_request(request, export_format, *args, **kwargs)
        
        # PRIORITÉ 2: Vérifier si c'est une requête QueryModel (POST avec JSON)
        if RequestFormatDetector.is_query_model_request(request):
            return self.handle_datatable_request(request, *args, **kwargs)
        
        # PRIORITÉ 3: Traiter comme requête DataTable standard
        if RequestFormatDetector.is_datatable_request(request):
            return self.handle_datatable_request(request, *args, **kwargs)
        
        # PRIORITÉ 4: Traiter comme requête REST normale
        return self.handle_rest_request(request, *args, **kwargs)
    
    def handle_rest_request(self, request, *args, **kwargs):
        """Gère les requêtes REST API normales avec pagination simple"""
        try:
            queryset = self.get_datatable_queryset()
            
            # Appliquer les filtres si disponible
            filter_handler = self.get_datatable_filter()
            if filter_handler:
                queryset = filter_handler.apply_filters(request, queryset)
            
            # Appliquer le tri REST API
            ordering = request.GET.get('ordering')
            if ordering:
                # Vérifier si le champ de tri est autorisé
                clean_ordering = ordering.lstrip('-')
                if clean_ordering in self.order_fields:
                    logger.debug(f"Application du tri REST: {ordering}")
                    queryset = queryset.order_by(ordering)
                else:
                    logger.warning(f"Champ de tri non autorisé: {ordering}")
            else:
                # Tri par défaut si aucun tri spécifié
                logger.debug(f"Application du tri par défaut: {self.default_order}")
                queryset = queryset.order_by(self.default_order)
            
            # Pagination simple
            try:
                page = max(1, int(request.GET.get('page', 1)))
                page_size = min(max(self.min_page_size, int(request.GET.get('page_size', self.page_size))), self.max_page_size)
            except (ValueError, TypeError):
                page = 1
                page_size = self.page_size
            
            start = (page - 1) * page_size
            end = start + page_size
            
            data = queryset[start:end]
            total_count = queryset.count()
            
            if self.serializer_class:
                serializer = self.serializer_class(data, many=True)
                return Response({
                    'count': total_count,
                    'results': serializer.data,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                })
            else:
                return Response({
                    'count': total_count,
                    'results': list(data.values()),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                })
        except Exception as e:
            logger.error(f"Erreur lors du traitement REST API: {str(e)}")
            return Response(
                {"error": "Erreur lors du traitement de la requête REST API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =============================================================================
# QUERY MODEL MIXIN (Support QueryModel)
# =============================================================================

class QueryModelMixin:
    """
    Mixin pour ajouter le support QueryModel à une vue.
    
    Ce mixin est spécialisé pour le format QueryModel uniquement (sortModel, filterModel).
    Pour un support plus complet (DataTable + QueryModel + REST API), 
    utilisez ServerSideDataTableView.
    
    USAGE SIMPLE:
    
    class MyView(QueryModelMixin, APIView):
        model = MyModel
        serializer_class = MySerializer
        column_field_mapping = {
            'id': 'id',
            'name': 'name',
            'age': 'age'
        }
        
        def get_queryset(self):
            return MyModel.objects.all()
    
    La vue supporte automatiquement:
    - Tri multi-colonnes (sortModel)
    - Filtres complexes (filterModel)
    - Infinite scroll (startRow/endRow)
    - Format de réponse QueryModel
    """
    
    # Configuration requise
    serializer_class: Optional[type] = None
    column_field_mapping: Dict[str, str] = {}  # col_id -> field_name
    
    # Configuration optionnelle
    default_page_size: int = 100
    max_page_size: int = 1000
    
    def get_queryset(self) -> QuerySet:
        """
        Retourne le QuerySet de base.
        
        À surcharger dans la vue pour personnaliser le QuerySet.
        """
        if hasattr(self, 'model'):
            return self.model.objects.all()
        raise NotImplementedError(
            "Vous devez soit définir 'model' soit surcharger 'get_queryset()'"
        )
    
    def get_data_source(self):
        """
        Retourne la source de données.
        
        Par défaut, utilise get_queryset(). Peut être surchargé pour
        utiliser une liste de dictionnaires ou une fonction callable.
        """
        from .datasource import DataSourceFactory
        queryset = self.get_queryset()
        return DataSourceFactory.create(queryset)
    
    def get_column_field_mapping(self) -> Dict[str, str]:
        """
        Retourne le mapping colonnes -> champs Django.
        
        Par défaut, utilise self.column_field_mapping.
        Peut être surchargé pour un mapping dynamique.
        """
        return getattr(self, 'column_field_mapping', {})
    
    def get_serializer_class(self) -> type:
        """Retourne la classe de serializer"""
        if self.serializer_class is None:
            raise NotImplementedError(
                "Vous devez définir 'serializer_class'"
            )
        return self.serializer_class
    
    def serialize_data(
        self,
        data: Union[QuerySet, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Sérialise les données avec le serializer.
        
        Args:
            data: QuerySet ou liste de dictionnaires
            
        Returns:
            Liste de dictionnaires sérialisés
        """
        serializer_class = self.get_serializer_class()
        
        if isinstance(data, QuerySet):
            # QuerySet -> utiliser many=True
            serializer = serializer_class(data, many=True)
            return serializer.data
        elif isinstance(data, list):
            # Liste de dicts -> sérialiser chaque élément
            serializer = serializer_class(data, many=True)
            return serializer.data
        else:
            # Convertir en liste si nécessaire
            data_list = list(data) if hasattr(data, '__iter__') else [data]
            serializer = serializer_class(data_list, many=True)
            return serializer.data
    
    def process_request(
        self,
        request: HttpRequest,
        *args,
        **kwargs
    ) -> Response:
        """
        Traite une requête complète au format QueryModel.
        
        FLUX:
        1. Parser QueryModel depuis la requête
        2. Récupérer la source de données
        3. Appliquer les filtres (FilterEngine)
        4. Appliquer le tri (SortEngine)
        5. Paginer (PaginationEngine)
        6. Sérialiser les données
        7. Retourner ResponseModel
        
        Args:
            request: Requête HTTP
            *args, **kwargs: Arguments additionnels
            
        Returns:
            Response DRF avec format QueryModel
        """
        from .models import QueryModel
        from .engines import FilterEngine, SortEngine, PaginationEngine
        from .response import ResponseModel
        
        try:
            # 1. Parser QueryModel
            query_model = QueryModel.from_request(request)
            
            # 2. Récupérer la source de données
            data_source = self.get_data_source()
            data = data_source.get_data()
            
            # 3. Appliquer les filtres (si QuerySet)
            if isinstance(data, QuerySet):
                column_mapping = self.get_column_field_mapping()
                filter_engine = FilterEngine(column_mapping)
                data = filter_engine.apply_filters(data, query_model.filter_model)
            
            # 4. Appliquer le tri (si QuerySet)
            if isinstance(data, QuerySet):
                column_mapping = self.get_column_field_mapping()
                sort_engine = SortEngine(column_mapping)
                data = sort_engine.apply_sorting(data, query_model.sort_model)
            
            # 5. Paginer
            if isinstance(data, QuerySet):
                pagination_engine = PaginationEngine(
                    default_page_size=self.default_page_size,
                    max_page_size=self.max_page_size
                )
                pagination_result = pagination_engine.paginate(
                    data,
                    start_row=query_model.start_row,
                    end_row=query_model.end_row
                )
                paginated_data = pagination_result['queryset']
                total_count = pagination_result['total_count']
            else:
                # Pour les listes, paginer manuellement
                start = query_model.start_row
                end = query_model.end_row or (start + self.default_page_size)
                total_count = len(data)
                paginated_data = data[start:end]
            
            # 6. Sérialiser
            serialized_data = self.serialize_data(paginated_data)
            
            # 7. Retourner ResponseModel
            response_model = ResponseModel.from_data(
                data=serialized_data,
                total_count=total_count
            )
            
            return Response(response_model.to_dict(), status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement QueryModel: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": f"Erreur lors du traitement: {str(e)}",
                    "rowData": [],
                    "rowCount": 0
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QueryModelView(QueryModelMixin, APIView):
    """
    Vue complète avec support QueryModel.
    
    Cette classe est spécialisée pour le format QueryModel uniquement.
    Pour un support plus complet (DataTable + QueryModel + REST API), 
    utilisez ServerSideDataTableView.
    
    USAGE:
    
    class MyView(QueryModelView):
        model = MyModel
        serializer_class = MySerializer
        column_field_mapping = {
            'id': 'id',
            'name': 'name'
        }
    
    La vue expose automatiquement:
    - POST /api/my-view/ (avec QueryModel dans le body)
    - GET /api/my-view/?sortModel=...&filterModel=... (format QueryModel)
    """
    
    def post(self, request, *args, **kwargs):
        """
        POST pour requêtes QueryModel (format JSON dans body).
        
        Body attendu:
        {
            "sortModel": [...],
            "filterModel": {...},
            "startRow": 0,
            "endRow": 100
        }
        """
        return self.process_request(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """
        GET pour requêtes QueryModel (format query params).
        
        Query params:
        - sortModel: JSON string
        - filterModel: JSON string
        - startRow: int
        - endRow: int
        """
        return self.process_request(request, *args, **kwargs) 