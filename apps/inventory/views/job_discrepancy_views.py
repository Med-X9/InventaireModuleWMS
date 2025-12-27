"""
Vue API DataTable pour récupérer les jobs avec leurs assignments et les écarts entre tous les comptages.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

from ..services.job_discrepancy_service import JobDiscrepancyService
from ..serializers.job_discrepancy_serializer import JobDiscrepancySerializer
from ..utils.response_utils import success_response, error_response
from apps.core.datatables.mixins import ServerSideDataTableView

logger = logging.getLogger(__name__)


class JobDiscrepancyView(ServerSideDataTableView):
    """
    Vue DataTable pour récupérer les écarts des jobs avec format compatible DataTable.

    Retourne les informations essentielles au format attendu par DataTable :
    - Informations de base du job
    - Métriques d'écarts (count, rate, lignes)
    - Assignments standardisés
    - Écarts dynamiques par counting_order

    Support DataTable avec pagination, tri, recherche et filtrage.

    URL: /api/inventory/{inventory_id}/warehouse/{warehouse_id}/jobs/discrepancies/

    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés
    - Recherche sur champs multiples
    - Filtrage avancé
    - Pagination optimisée

    PARAMÈTRES:
    - Tri: ordering=job_reference, ordering=-discrepancy_rate
    - Recherche: search=terme
    - Pagination: page=1&page_size=20
    - Filtres: job_status=ENTAME, discrepancy_rate__gte=10
    """
    permission_classes = [IsAuthenticated]
    serializer_class = JobDiscrepancySerializer
    
    # Champs de recherche
    search_fields = [
        'job_reference',
        'job_status',
        'discrepancy_count',
        'discrepancy_rate',
    ]

    # Champs de tri
    order_fields = [
        'job_id',
        'job_reference',
        'job_status',
        'discrepancy_count',
        'discrepancy_rate',
        'total_lines_counting_1',
        'total_lines_counting_2',
        'common_lines_count',
    ]
    default_order = 'job_reference'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_discrepancy_service = JobDiscrepancyService()
    
    def _get_results_data(self, inventory_id: int, warehouse_id: int) -> list:
        """Récupère les données brutes depuis le service (format simplifié)."""
        return self.job_discrepancy_service.get_jobs_discrepancies_simplified(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        )
    
    def _apply_search_on_list(self, data_list: list, search_term: str) -> list:
        """Applique la recherche sur une liste de dictionnaires."""
        if not search_term:
            return data_list
        search_clean = search_term.lower().strip()
        if not search_clean:
            return data_list
        filtered = []
        for item in data_list:
            if (search_clean in str(item.get('job_reference', '')).lower() or
                search_clean in str(item.get('job_status', '')).lower() or
                search_clean in str(item.get('discrepancy_count', '')).lower() or
                search_clean in str(item.get('discrepancy_rate', '')).lower()):
                filtered.append(item)
        return filtered
    
    def _apply_ordering_on_list(self, data_list: list, ordering: str) -> list:
        """Applique le tri sur une liste de dictionnaires."""
        if not ordering:
            ordering = self.default_order
        reverse = ordering.startswith('-')
        field = ordering.lstrip('-')
        
        def sort_key(item):
            value = item.get(field)
            if value is None:
                if field.endswith('_rate') or field.endswith('_count'):
                    return float('-inf') if not reverse else float('inf')
                return '' if not reverse else 'zzz'
            if isinstance(value, (int, float)):
                return value
            return str(value).lower()
        
        return sorted(data_list, key=sort_key, reverse=reverse)
    
    def _process_list_data(self, results: list, request) -> tuple:
        """Traite les données de liste : filtres, recherche, tri, pagination."""
        # Recherche
        search_term = request.GET.get('search', {}).get('value', '') if isinstance(request.GET.get('search'), dict) else request.GET.get('search', '')
        if not search_term:
            search_term = request.GET.get('search', '')
        if search_term:
            results = self._apply_search_on_list(results, search_term)
        
        # Tri
        ordering_applied = False
        order_index = 0
        while f'order[{order_index}][column]' in request.GET:
            try:
                column_index = int(request.GET.get(f'order[{order_index}][column]', 0))
                direction = request.GET.get(f'order[{order_index}][dir]', 'asc')
                if 0 <= column_index < len(self.order_fields):
                    field = self.order_fields[column_index]
                    ordering = f"-{field}" if direction == 'desc' else field
                    results = self._apply_ordering_on_list(results, ordering)
                    ordering_applied = True
                    order_index += 1
            except (ValueError, IndexError):
                break
        
        # Tri REST API
        if not ordering_applied:
            ordering = request.GET.get('ordering', self.default_order)
            results = self._apply_ordering_on_list(results, ordering)
        
        # Pagination
        try:
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', self.page_size))
            length = min(max(self.min_page_size, length), self.max_page_size)
        except (ValueError, TypeError):
            start = 0
            length = self.page_size
        
        total_count = len(results)
        paginated_results = results[start:start + length]
        return paginated_results, total_count
    
    def _validate_required_params(self, request) -> tuple:
        """Valide et extrait les paramètres requis."""
        inventory_id = request.GET.get('inventory_id') or self.kwargs.get('inventory_id')
        warehouse_id = request.GET.get('warehouse_id') or self.kwargs.get('warehouse_id')
        
        if not inventory_id:
            return None, error_response(
                message="Le paramètre inventory_id est requis",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if not warehouse_id:
            return None, error_response(
                message="Le paramètre warehouse_id est requis",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            return (int(inventory_id), int(warehouse_id)), None
        except (ValueError, TypeError):
            return None, error_response(
                message="Les paramètres inventory_id et warehouse_id doivent être des nombres entiers",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    def get_data_source(self):
        """Retourne la source de données depuis le service (liste de dictionnaires)."""
        from apps.core.datatables.datasource import DataSourceFactory
        
        # Valider les paramètres
        params, error = self._validate_required_params(self.request)
        if error:
            raise ValueError(str(error))
        
        inventory_id, warehouse_id = params
        results = self._get_results_data(inventory_id, warehouse_id)
        return DataSourceFactory.create(results)
    
    def get_column_field_mapping(self):
        """Mapping des colonnes frontend -> backend."""
        return {
            'job_id': 'job_id',
            'job_reference': 'job_reference',
            'job_status': 'job_status',
            'discrepancy_count': 'discrepancy_count',
            'discrepancy_rate': 'discrepancy_rate',
            'total_lines_counting_1': 'total_lines_counting_1',
            'total_lines_counting_2': 'total_lines_counting_2',
            'common_lines_count': 'common_lines_count',
        }
    
    def process_request(self, request, *args, **kwargs):
        """
        Surcharge process_request pour garantir que les données restent des listes.
        
        Cette méthode intercepte le processus pour s'assurer que les données
        de type liste ne sont jamais converties en QuerySet.
        """
        from apps.core.datatables.models import QueryModel
        from apps.core.datatables.engines import FilterEngine, SortEngine, PaginationEngine
        from apps.core.datatables.response import ResponseModel
        from rest_framework.response import Response
        from django.db.models import QuerySet
        
        try:
            # 1. Vérifier si export demandé
            export_format = request.GET.get('export') or (request.data.get('export') if hasattr(request, 'data') and isinstance(request.data, dict) else None)
            
            # 2. Parser QueryModel
            query_model = QueryModel.from_request(request)
            
            # 3. Récupérer la source de données
            data_source = self.get_data_source()
            data = data_source.get_data()
            
            # S'assurer que data est une liste, pas un QuerySet
            if isinstance(data, QuerySet):
                logger.error(
                    f"QuerySet détecté dans process_request pour {self.__class__.__name__}. "
                    "Cela ne devrait pas arriver car get_data_source() retourne une liste."
                )
                # Convertir en liste vide pour éviter les erreurs
                data = []
            
            # 4. Appliquer la recherche globale si présente
            if query_model.search and isinstance(data, list):
                search_clean = query_model.search.strip()
                if search_clean:
                    search_fields = getattr(self, 'search_fields', [])
                    if not search_fields:
                        search_fields = list(self.get_column_field_mapping().values())
                    
                    # Recherche sur liste de dictionnaires
                    filtered_data = []
                    for item in data:
                        match_found = False
                        for field in search_fields:
                            value = item.get(field)
                            if value is not None and search_clean.lower() in str(value).lower():
                                filtered_data.append(item)
                                match_found = True
                                break
                        if not match_found:
                            for key, value in item.items():
                                if value is not None and search_clean.lower() in str(value).lower():
                                    filtered_data.append(item)
                                    break
                    data = filtered_data
            
            # 5. Appliquer les filtres (seulement si liste)
            if isinstance(data, list):
                column_mapping = self.get_column_field_mapping()
                filter_engine = FilterEngine(column_mapping)
                data = filter_engine.apply_filters(data, query_model.filters)
            
            # 6. Appliquer le tri (seulement si liste)
            if isinstance(data, list):
                column_mapping = self.get_column_field_mapping()
                sort_engine = SortEngine(column_mapping)
                data = sort_engine.apply_sorting(data, query_model.sort)
            
            # 7. Si export demandé
            if export_format and isinstance(data, list):
                serializer_class = self.get_serializer_class()
                filename = getattr(self, 'export_filename', 'export')
                if serializer_class:
                    serializer = serializer_class(data, many=True)
                    serialized_data = [dict(item) for item in serializer.data]
                else:
                    serialized_data = data
                return self._export_from_list(serialized_data, export_format, filename)
            
            # 8. Paginer (seulement si liste)
            if isinstance(data, list):
                pagination_engine = PaginationEngine(
                    default_page_size=getattr(self, 'default_page_size', 20),
                    max_page_size=getattr(self, 'max_page_size', 1000)
                )
                pagination_result = pagination_engine.paginate(
                    data,
                    page=query_model.page,
                    page_size=query_model.page_size
                )
                paginated_data = pagination_result['queryset']
                total_count = pagination_result['total_count']
            else:
                paginated_data = []
                total_count = 0
            
            # 9. Sérialiser
            serialized_data = self.serialize_data(paginated_data)
            
            # 10. Retourner ResponseModel
            response_model = ResponseModel.from_data(
                data=serialized_data,
                total_count=total_count,
                page=query_model.page,
                page_size=query_model.page_size
            )
            
            return Response(response_model.to_dict(), status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement QueryModel: {str(e)}", exc_info=True)
            return error_response(
                message=f"Erreur lors du traitement de la requête: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def serialize_data(self, data):
        """
        Sérialise les données avec JobDiscrepancySerializer.
        
        Surcharge pour gérer correctement les listes de dictionnaires
        et éviter les erreurs de relations Django.
        """
        serializer_class = self.get_serializer_class()
        
        if isinstance(data, list):
            # Liste de dicts -> sérialiser chaque élément
            serializer = serializer_class(data, many=True)
            return serializer.data
        else:
            # Convertir en liste si nécessaire
            data_list = list(data) if hasattr(data, '__iter__') else [data]
            serializer = serializer_class(data_list, many=True)
            return serializer.data

