from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

from ..services.counting_tracking_service import CountingTrackingService
from ..services.job_detail_tracking_service import JobDetailTrackingService
from ..serializers.counting_tracking_serializer import InventoryCountingTrackingSerializer
from ..serializers.job_detail_tracking_serializer import JobDetailTrackingSerializer
from ..exceptions.inventory_exceptions import InventoryNotFoundError
from apps.core.datatables.mixins import ServerSideDataTableView
from apps.core.datatables.base import IDataTableFilter
from apps.core.datatables.filters import CompositeDataTableFilter, FilterMappingFilter
from ..utils.response_utils import success_response, error_response

logger = logging.getLogger(__name__)


class InventoryCountingTrackingView(APIView):
    """
    API pour le suivi d'un inventaire regroupé par comptages avec leurs jobs et emplacements.
    
    Cette vue respecte l'architecture Repository/Service/View :
    - La vue appelle le service (pas le repository directement)
    - Le service gère la logique métier
    - Le repository gère l'accès aux données
    """
    
    def get(self, request, inventory_id):
        """
        Récupère le suivi d'un inventaire avec tous ses comptages, jobs et emplacements.
        
        Paramètres de requête:
            counting_order (requis): Ordre du comptage à filtrer (ex: ?counting_order=1)
        
        Args:
            inventory_id: ID de l'inventaire à suivre
            
        Returns:
            Response avec les données de l'inventaire regroupées par comptages
        """
        try:
            # Validation de sécurité: vérifier que inventory_id est un entier positif
            try:
                inventory_id = int(inventory_id)
                if inventory_id <= 0:
                    return Response(
                        {'error': 'L\'ID de l\'inventaire doit être un nombre entier positif'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'error': 'L\'ID de l\'inventaire doit être un nombre entier valide'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extraire le paramètre de filtre par ordre de comptage (obligatoire)
            counting_order = request.query_params.get('counting_order')
            if counting_order is None:
                return Response(
                    {'error': 'Le paramètre counting_order est requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                counting_order = int(counting_order)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Le paramètre counting_order doit être un nombre entier'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialiser le service et récupérer l'inventaire avec toutes ses relations
            counting_tracking_service = CountingTrackingService()
            inventory = counting_tracking_service.get_inventory_counting_tracking(inventory_id, counting_order)
            
            # Sérialiser les données
            serializer = InventoryCountingTrackingSerializer(inventory)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire {inventory_id} non trouvé: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du suivi de l'inventaire {inventory_id}: {str(e)}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobDetailTrackingView(ServerSideDataTableView):
    """
    Vue DataTable pour récupérer les JobDetail avec leurs Assignment.
    Supporte les filtres: warehouse_id, inventory_id, counting_order
    
    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés
    - Tri DataTable (order[0][column]=index&order[0][dir]=asc/desc)
    - Recherche sur champs multiples
    - Pagination optimisée
    - Sérialisation flexible
    
    PARAMÈTRES DE REQUÊTE SUPPORTÉS:
    - Filtres: warehouse_id, inventory_id, counting_order (requis)
    - Tri: ordering=field ou ordering=-field
    - Tri DataTable: order[0][column]=index&order[0][dir]=asc/desc
    - Recherche: search=terme
    - Pagination: page=1&page_size=25
    """
    
    # Configuration de base
    serializer_class = JobDetailTrackingSerializer
    
    # Champs de recherche et tri
    search_fields = [
        'job_reference', 'location_reference', 'status', 'assignment_status',
        'assignment_reference'
    ]
    order_fields = [
        'job_reference', 'location_reference', 'status', 'en_attente_date',
        'termine_date', 'assignment_status', 'transfert_date', 'entame_date',
        'termine_date_assignment'
    ]
    default_order = 'job_reference'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 100
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = JobDetailTrackingService()
    
    def _get_results_data(
        self,
        inventory_id: int = None,
        warehouse_id: int = None,
        counting_order: int = None
    ) -> list:
        """
        Récupère les données brutes depuis le service.
        
        Returns:
            Liste de dictionnaires contenant JobDetail avec Assignment
        """
        return self.service.get_job_details_with_assignments(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
            counting_order=counting_order
        )
    
    def _apply_search_on_list(self, data_list: list, search_term: str) -> list:
        """
        Applique la recherche sur une liste de dictionnaires.
        """
        if not search_term:
            return data_list
        
        search_clean = search_term.lower().strip()
        if not search_clean:
            return data_list
        
        filtered = []
        for item in data_list:
            job_detail = item.get('job_detail')
            assignment = item.get('assignment')
            
            # Rechercher dans les champs du JobDetail
            if job_detail:
                if (search_clean in str(job_detail.job.reference).lower() or
                    search_clean in str(job_detail.location.location_reference).lower() or
                    search_clean in str(job_detail.status).lower()):
                    filtered.append(item)
                    continue
            
            # Rechercher dans les champs de l'Assignment
            if assignment:
                if (search_clean in str(assignment.reference).lower() or
                    search_clean in str(assignment.status).lower()):
                    filtered.append(item)
        
        return filtered
    
    def _apply_ordering_on_list(self, data_list: list, ordering: str) -> list:
        """
        Applique le tri sur une liste de dictionnaires.
        """
        if not ordering:
            ordering = self.default_order
        
        reverse = ordering.startswith('-')
        field = ordering.lstrip('-')
        
        def sort_key(item):
            job_detail = item.get('job_detail')
            assignment = item.get('assignment')
            
            # Mapping des champs vers les valeurs réelles
            field_mapping = {
                'job_reference': lambda: job_detail.job.reference if job_detail else '',
                'location_reference': lambda: job_detail.location.location_reference if job_detail else '',
                'status': lambda: job_detail.status if job_detail else '',
                'en_attente_date': lambda: job_detail.en_attente_date if job_detail and job_detail.en_attente_date else None,
                'termine_date': lambda: job_detail.termine_date if job_detail and job_detail.termine_date else None,
                'assignment_status': lambda: assignment.status if assignment else '',
                'transfert_date': lambda: assignment.transfert_date if assignment and assignment.transfert_date else None,
                'entame_date': lambda: assignment.entame_date if assignment and assignment.entame_date else None,
                'termine_date_assignment': lambda: assignment.updated_at if assignment and assignment.status == 'TERMINE' else None,
            }
            
            getter = field_mapping.get(field)
            if getter:
                value = getter()
            else:
                value = None
            
            # Gérer les valeurs None
            if value is None:
                if field.endswith('_date') or 'date' in field:
                    return float('-inf') if not reverse else float('inf')
                return '' if not reverse else 'zzz'
            
            # Pour les dates, convertir en timestamp
            if hasattr(value, 'timestamp'):
                return value.timestamp()
            
            # Pour les autres, convertir en string
            return str(value).lower()
        
        return sorted(data_list, key=sort_key, reverse=reverse)
    
    def handle_datatable_request(self, request, *args, **kwargs):
        """
        Gère les requêtes DataTable avec traitement sur liste de dictionnaires.
        """
        try:
            # Extraire les paramètres de filtre requis
            inventory_id = request.GET.get('inventory_id')
            warehouse_id = request.GET.get('warehouse_id')
            counting_order = request.GET.get('counting_order')
            
            # Validation des paramètres requis
            if not inventory_id:
                return error_response(
                    message="Le paramètre inventory_id est requis",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not warehouse_id:
                return error_response(
                    message="Le paramètre warehouse_id est requis",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not counting_order:
                return error_response(
                    message="Le paramètre counting_order est requis",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                inventory_id = int(inventory_id)
                warehouse_id = int(warehouse_id)
                counting_order = int(counting_order)
            except (ValueError, TypeError):
                return error_response(
                    message="Les paramètres inventory_id, warehouse_id et counting_order doivent être des nombres entiers",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer les données depuis le service
            results = self._get_results_data(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
                counting_order=counting_order
            )
            logger.debug(f"Données récupérées: {len(results)} résultats")
            
            # Appliquer la recherche
            search_term = request.GET.get('search', {}).get('value', '') if isinstance(request.GET.get('search'), dict) else request.GET.get('search', '')
            if not search_term:
                search_term = request.GET.get('search', '')
            
            if search_term:
                logger.debug(f"Recherche appliquée: '{search_term}'")
                results = self._apply_search_on_list(results, search_term)
                logger.debug(f"Après recherche: {len(results)} résultats")
            
            # Appliquer le tri DataTable
            ordering_applied = False
            order_index = 0
            
            while f'order[{order_index}][column]' in request.GET:
                try:
                    column_index = int(request.GET.get(f'order[{order_index}][column]', 0))
                    direction = request.GET.get(f'order[{order_index}][dir]', 'asc')
                    
                    if 0 <= column_index < len(self.order_fields):
                        field = self.order_fields[column_index]
                        ordering = f"-{field}" if direction == 'desc' else field
                        logger.info(f"Tri DataTable appliqué: colonne {column_index} -> champ '{field}' direction '{direction}'")
                        results = self._apply_ordering_on_list(results, ordering)
                        ordering_applied = True
                        order_index += 1
                except (ValueError, IndexError) as e:
                    logger.warning(f"Erreur lors du tri DataTable: {e}")
                    break
            
            # Si aucun tri DataTable n'a été appliqué, utiliser le tri par défaut
            if not ordering_applied:
                logger.debug(f"Aucun tri DataTable détecté, utilisation du tri par défaut: '{self.default_order}'")
                results = self._apply_ordering_on_list(results, self.default_order)
            
            # Pagination DataTable
            try:
                start = int(request.GET.get('start', 0))
                length = int(request.GET.get('length', self.page_size))
                length = min(max(self.min_page_size, length), self.max_page_size)
            except (ValueError, TypeError):
                start = 0
                length = self.page_size
            
            total_count = len(results)
            paginated_results = results[start:start + length]
            
            # Sérialisation
            serializer = self.serializer_class(paginated_results, many=True)
            
            # Réponse DataTable
            draw = int(request.GET.get('draw', 1))
            return Response({
                'draw': draw,
                'recordsTotal': total_count,
                'recordsFiltered': total_count,
                'data': serializer.data
            })
            
        except Exception as error:
            logger.error(
                f"Erreur inattendue lors de la récupération des JobDetail: {str(error)}",
                exc_info=True
            )
            return error_response(
                message="Une erreur inattendue est survenue lors de la récupération des données",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def handle_rest_request(self, request, *args, **kwargs):
        """
        Gère les requêtes REST API normales avec pagination simple.
        """
        try:
            # Extraire les paramètres de filtre requis
            inventory_id = request.GET.get('inventory_id')
            warehouse_id = request.GET.get('warehouse_id')
            counting_order = request.GET.get('counting_order')
            
            # Validation des paramètres requis
            if not inventory_id:
                return error_response(
                    message="Le paramètre inventory_id est requis",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not warehouse_id:
                return error_response(
                    message="Le paramètre warehouse_id est requis",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not counting_order:
                return error_response(
                    message="Le paramètre counting_order est requis",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                inventory_id = int(inventory_id)
                warehouse_id = int(warehouse_id)
                counting_order = int(counting_order)
            except (ValueError, TypeError):
                return error_response(
                    message="Les paramètres inventory_id, warehouse_id et counting_order doivent être des nombres entiers",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer les données depuis le service
            results = self._get_results_data(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
                counting_order=counting_order
            )
            
            # Appliquer la recherche
            search_term = request.GET.get('search', '')
            if search_term:
                results = self._apply_search_on_list(results, search_term)
            
            # Appliquer le tri REST API
            ordering = request.GET.get('ordering', self.default_order)
            results = self._apply_ordering_on_list(results, ordering)
            
            # Pagination REST API
            try:
                page = max(1, int(request.GET.get('page', 1)))
                page_size = min(max(self.min_page_size, int(request.GET.get('page_size', self.page_size))), self.max_page_size)
            except (ValueError, TypeError):
                page = 1
                page_size = self.page_size
            
            start = (page - 1) * page_size
            end = start + page_size
            paginated_results = results[start:end]
            
            # Sérialisation
            serializer = self.serializer_class(paginated_results, many=True)
            
            total_count = len(results)
            return Response({
                'count': total_count,
                'results': serializer.data,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            })
            
        except Exception as error:
            logger.error(
                f"Erreur inattendue lors de la récupération des JobDetail: {str(error)}",
                exc_info=True
            )
            return error_response(
                message="Une erreur inattendue est survenue lors de la récupération des données",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


