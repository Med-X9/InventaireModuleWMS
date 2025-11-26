"""
Vue API DataTable pour récupérer les jobs avec leurs assignments et les écarts entre le 1er et 2ème comptage.
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
    Vue DataTable pour récupérer les jobs avec leurs assignments et les écarts entre le 1er et 2ème comptage.
    
    Support DataTable avec pagination, tri, recherche et filtrage.
    
    URL: /api/inventory/{inventory_id}/warehouse/{warehouse_id}/jobs/discrepancies/
    
    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés
    - Recherche sur champs multiples
    - Filtrage avancé
    - Pagination optimisée
    - Support DataTable et REST API
    
    PARAMÈTRES:
    - Tri: ordering=job_reference, ordering=-discrepancy_rate
    - Recherche: search=terme
    - Pagination: page=1&page_size=20
    - Filtres: job_status=VALIDE, discrepancy_rate__gte=10
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
        """Récupère les données brutes depuis le service."""
        return self.job_discrepancy_service.get_jobs_with_discrepancies(
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
    
    def handle_datatable_request(self, request, *args, **kwargs):
        """Gère les requêtes DataTable avec traitement sur liste de dictionnaires."""
        try:
            params, error = self._validate_required_params(request)
            if error:
                return error
            inventory_id, warehouse_id = params
            results = self._get_results_data(inventory_id, warehouse_id)
            paginated_results, total_count = self._process_list_data(results, request)
            serializer = self.serializer_class(paginated_results, many=True)
            return Response({
                'draw': int(request.GET.get('draw', 1)),
                'recordsTotal': total_count,
                'recordsFiltered': total_count,
                'data': serializer.data
            })
        except ValueError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as error:
            logger.error(f"Erreur lors de la récupération des jobs avec écarts: {str(error)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue est survenue",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def handle_rest_request(self, request, *args, **kwargs):
        """Gère les requêtes REST API normales avec pagination simple."""
        try:
            params, error = self._validate_required_params(request)
            if error:
                return error
            inventory_id, warehouse_id = params
            results = self._get_results_data(inventory_id, warehouse_id)
            search_term = request.GET.get('search', '')
            if search_term:
                results = self._apply_search_on_list(results, search_term)
            ordering = request.GET.get('ordering', self.default_order)
            results = self._apply_ordering_on_list(results, ordering)
            try:
                page = max(1, int(request.GET.get('page', 1)))
                page_size = min(max(self.min_page_size, int(request.GET.get('page_size', self.page_size))), self.max_page_size)
            except (ValueError, TypeError):
                page = 1
                page_size = self.page_size
            start = (page - 1) * page_size
            paginated_results = results[start:start + page_size]
            serializer = self.serializer_class(paginated_results, many=True)
            total_count = len(results)
            return Response({
                'count': total_count,
                'results': serializer.data,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            })
        except ValueError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as error:
            logger.error(f"Erreur lors de la récupération des jobs avec écarts: {str(error)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue est survenue",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

