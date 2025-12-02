from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError
from ..serializers import (
    InventoryJobCreateSerializer,
    JobSerializer
)
from ..utils.response_utils import success_response, error_response, validation_error_response

from ..repositories.job_repository import JobRepository
from ..services.job_service import JobService
from ..serializers.job_serializer import (
    JobCreateRequestSerializer,
    JobRemoveEmplacementsSerializer,
    JobAddEmplacementsSerializer,
    JobValidateRequestSerializer,
    JobListWithLocationsSerializer,
    JobDeleteRequestSerializer,
    JobReadyRequestSerializer,
    JobFullDetailSerializer,
    JobPendingSerializer,
    JobResetAssignmentsRequestSerializer,
    PendingJobReferenceSerializer,
    JobTransferRequestSerializer,
    JobManualEntryRequestSerializer,
    JobProgressByCountingSerializer,
    JobWithAssignmentsSerializer,
    AssignmentFlatSerializer,
    JobDetailSimpleSerializer
)
from ..serializers.job_assignment_batch_serializer import JobBatchAssignmentRequestSerializer
from ..usecases.job_batch_assignment import JobBatchAssignmentUseCase
from ..exceptions import JobCreationError
import logging
from datetime import datetime
from ..models import Job, Warehouse, Assigment, JobDetail
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from ..filters.job_filters import JobFilter, JobFullDetailFilter, PendingJobFilter
from apps.core.datatables.mixins import ServerSideDataTableView

logger = logging.getLogger(__name__)


class JobCreateAPIView(APIView):
    def post(self, request, inventory_id, warehouse_id):
        serializer = JobCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Formater les erreurs de manière sécurisée
            error_messages = []
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    error_messages.append(f"{field}: {', '.join(str(e) for e in errors)}")
                else:
                    error_messages.append(f"{field}: {str(errors)}")
            
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': ' | '.join(error_messages)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        emplacements = serializer.validated_data['emplacements']
        
        try:
            # Utiliser le use case pour la logique métier
            from ..usecases.job_creation import JobCreationUseCase
            use_case = JobCreationUseCase()
            result = use_case.execute(inventory_id, warehouse_id, emplacements)
            
            return Response({
                'success': True,
                'message': result['message'],
                'data': result
            }, status=status.HTTP_201_CREATED)
        except JobCreationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JobValidateView(APIView):
    def post(self, request):
        serializer = JobValidateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Formater les erreurs de manière sécurisée
            error_messages = []
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    error_messages.append(f"{field}: {', '.join(str(e) for e in errors)}")
                else:
                    error_messages.append(f"{field}: {str(errors)}")
            
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': ' | '.join(error_messages)
            }, status=status.HTTP_400_BAD_REQUEST)
        job_ids = serializer.validated_data['job_ids']
        try:
            job_service = JobService()
            result = job_service.validate_jobs(job_ids)
            return Response({
                'success': True,
                'message': 'Jobs validés avec succès',
            }, status=status.HTTP_200_OK)
        except JobCreationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JobReadyView(APIView):
    """
    Vue pour marquer tous les assignments d'un job comme PRET
    
    Permet de mettre en statut PRET tous les assignments avec statut AFFECTE des jobs spécifiés.
    Le paramètre counting_order est ignoré (conservé pour rétrocompatibilité).
    """
    
    def post(self, request):
        """
        Marque tous les assignments avec statut AFFECTE des jobs spécifiés comme PRET
        
        Body attendu:
        {
            "job_ids": [1, 2, 3],
            "counting_order": 2  # optionnel, ignoré (conservé pour rétrocompatibilité)
        }
        """
        serializer = JobReadyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Formater les erreurs de manière sécurisée
            error_messages = []
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    error_messages.append(f"{field}: {', '.join(str(e) for e in errors)}")
                else:
                    error_messages.append(f"{field}: {str(errors)}")
            
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': ' | '.join(error_messages)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        job_ids = serializer.validated_data['job_ids']
        counting_order = serializer.validated_data.get('counting_order')
        
        try:
            # Utiliser le use case pour la logique métier
            from ..usecases.job_ready import JobReadyUseCase
            use_case = JobReadyUseCase()
            result = use_case.execute(job_ids, counting_order)
            
            # Construire la réponse sans counting_order
            response_data = {
                'jobs_processed': result['jobs_processed'],
                'jobs': result['jobs']
            }
            
            return success_response(
                data=response_data,
                message=result['message']
            )
        except JobCreationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class JobDeleteView(APIView):
    def delete(self, request):
        serializer = JobDeleteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        job_ids = serializer.validated_data['job_ids']
        try:
            job_service = JobService()
            
            # Première étape : vérifier que tous les jobs peuvent être supprimés
            validation_errors = []
            
            for job_id in job_ids:
                job = job_service.get_job_by_id(job_id)
                if not job:
                    validation_errors.append(f"Job avec l'ID {job_id} non trouvé")
                elif job.status != 'EN ATTENTE':
                    validation_errors.append(f"Job {job.reference} (ID: {job_id}) ne peut pas être supprimé. Statut actuel : {job.status}")
            
            # Si il y a des erreurs de validation, arrêter tout
            if validation_errors:
                return Response({
                    'success': False,
                    'message': 'Impossible de supprimer les jobs. Vérifications échouées.',
                    'errors': validation_errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Deuxième étape : supprimer tous les jobs dans une transaction
            result = job_service.delete_multiple_jobs(job_ids)
            
            return Response(result, status=status.HTTP_200_OK)
                
        except JobCreationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JobRemoveEmplacementsView(APIView):
    def delete(self, request, job_id):
        """
        Supprime des emplacements d'un job avec gestion des comptages multiples
        """
        # Validation du job_id
        if not job_id or job_id <= 0:
            return Response({
                'success': False,
                'message': 'ID de job invalide',
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation des données de la requête
        serializer = JobRemoveEmplacementsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Erreur de validation des données', 
                'errors': serializer.errors,
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        emplacement_ids = serializer.validated_data['emplacement_ids']
        
        # Validation supplémentaire des emplacement_ids
        if not emplacement_ids or len(emplacement_ids) == 0:
            return Response({
                'success': False,
                'message': 'Liste d\'emplacements vide',
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation des types d'IDs
        invalid_ids = [id for id in emplacement_ids if not isinstance(id, int) or id <= 0]
        if invalid_ids:
            return Response({
                'success': False,
                'message': f'IDs d\'emplacements invalides: {invalid_ids}',
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Utiliser le use case pour la logique métier
            from ..usecases.job_remove_emplacements import JobRemoveEmplacementsUseCase
            use_case = JobRemoveEmplacementsUseCase()
            result = use_case.execute(job_id, emplacement_ids)
            
            return Response({
                'success': True,
                'message': result['message'],
                'data': result
            }, status=status.HTTP_200_OK)
            
        except JobCreationError as e:
            # Erreurs métier - retourner 400 Bad Request
            return Response({
                'success': False,
                'message': str(e),
                'error_type': 'business_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except ValidationError as e:
            # Erreurs de validation Django
            return Response({
                'success': False,
                'message': f'Erreur de validation: {str(e)}',
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Erreurs inattendues - logger et retourner 500
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur inattendue dans JobRemoveEmplacementsView: {str(e)}")
            
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur',
                'error_type': 'internal_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JobAddEmplacementsView(APIView):
    def post(self, request, job_id):
        serializer = JobAddEmplacementsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        emplacement_ids = serializer.validated_data['emplacement_ids']
        
        try:
            # Utiliser le use case pour la logique métier
            from ..usecases.job_add_emplacements import JobAddEmplacementsUseCase
            use_case = JobAddEmplacementsUseCase()
            result = use_case.execute(job_id, emplacement_ids)
            
            return Response({
                'success': True,
                'message': result['message'],
                'data': result
            }, status=status.HTTP_200_OK)
        except JobCreationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PendingJobsReferencesView(ServerSideDataTableView):
    """
    Vue pour lister les jobs en attente avec pagination et filtres DataTable.
    Supporte les paramètres DataTable (start, length, order, search, etc.)
    """
    model = Job
    serializer_class = PendingJobReferenceSerializer
    filterset_class = PendingJobFilter
    
    # Champs de recherche - tous les champs disponibles
    search_fields = [
        'reference', 'status', 'created_at',
        'inventory__reference', 'inventory__label',
        'warehouse__reference', 'warehouse__warehouse_name'
    ]
    
    # Champs de tri - tous les champs disponibles
    order_fields = [
        'id', 'reference', 'status', 'created_at',
        'inventory__reference', 'inventory__label',
        'warehouse__reference', 'warehouse__warehouse_name'
    ]
    default_order = '-created_at'
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    export_filename = 'jobs_en_attente'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..repositories.job_repository import JobRepository
        self.repository = JobRepository()

    def get_datatable_queryset(self):
        """
        Récupère les jobs en attente via le repository avec relations préchargées.
        ⚠️ Règle: La vue ne doit PAS utiliser Job.objects directement.
        """
        warehouse_id = self.kwargs.get('warehouse_id')
        return self.repository.get_pending_jobs_for_warehouse_datatable(warehouse_id)

class JobListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000

class JobListWithLocationsView(ServerSideDataTableView):
    """
    Vue pour lister les jobs avec leurs emplacements - Support DataTable.
    
    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés
    - Recherche sur champs multiples
    - Filtrage avancé par emplacements, statut, dates
    - Pagination optimisée
    - Relations préchargées pour performance
    
    PARAMÈTRES:
    - Tri: ordering=reference, ordering=-created_at, ordering=status
    - Recherche: search=terme
    - Pagination: page=1&page_size=20
    - Filtres: status=valide, location_reference=LOC-xxx, created_at_gte=2024-01-01
    """
    
    model = Job
    serializer_class = JobListWithLocationsSerializer
    filterset_class = JobFilter
    
    # Champs de recherche et tri
    search_fields = [
        'reference', 'status', 'created_at', 'warehouse__warehouse_name',
        'inventory__reference', 'jobdetail__location__location_reference',
        'jobdetail__location__sous_zone__sous_zone_name',
        'jobdetail__location__sous_zone__zone__zone_name'
    ]
    
    order_fields = [
        'id', 'reference', 'status', 'created_at', 'warehouse__warehouse_name'
    ]
    default_order = '-created_at'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    export_filename = 'jobs_avec_emplacements'
    
    # Mapping frontend -> backend pour les filtres (vue générique Jobs / JobManagement)
    filter_aliases = {
        # champs simples
        'id': 'id',
        'reference': 'reference',
        'status': 'status',
        'warehouse_name': 'warehouse__warehouse_name',
        'inventory_reference': 'inventory__reference',

        # filtres sur les emplacements liés
        'location_reference': 'jobdetail__location__location_reference',
        'sous_zone_name': 'jobdetail__location__sous_zone__sous_zone_name',
        'zone_name': 'jobdetail__location__sous_zone__zone__zone_name',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..repositories.job_repository import JobRepository
        self.repository = JobRepository()
    
    def get_datatable_queryset(self):
        """
        Récupère les jobs via le repository avec relations préchargées.
        ⚠️ Règle: La vue ne doit PAS utiliser Job.objects directement.
        """
        return self.repository.get_jobs_for_datatable()

class WarehouseJobsView(ServerSideDataTableView):
    """
    Récupère tous les jobs d'un warehouse spécifique pour un inventaire donné - Support DataTable.
    """
    model = Job
    serializer_class = JobListWithLocationsSerializer
    
    # Champs de recherche - tous les champs disponibles
    search_fields = [
        'reference', 'status', 'created_at',
        'warehouse__warehouse_name', 'warehouse__reference',
        'inventory__reference', 'inventory__label',
        'jobdetail__location__location_reference',
        'jobdetail__location__sous_zone__sous_zone_name',
        'jobdetail__location__sous_zone__zone__zone_name'
    ]
    
    # Champs de tri - tous les champs disponibles
    order_fields = [
        'id', 'reference', 'status', 'created_at',
        'warehouse__warehouse_name', 'inventory__reference'
    ]
    
    default_order = '-created_at'
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    export_filename = 'jobs_par_warehouse'

    # Mapping frontend -> backend pour le DataTable « Jobs créés »
    filter_aliases = {
        'id': 'id',
        'reference': 'reference',
        'status': 'status',
        'created_at': 'created_at',
        'warehouse_name': 'warehouse__warehouse_name',
        'warehouse_reference': 'warehouse__reference',
        'inventory_reference': 'inventory__reference',
        'inventory_label': 'inventory__label',
        'location_reference': 'jobdetail__location__location_reference',
        'zone_name': 'jobdetail__location__sous_zone__zone__zone_name',
        'sous_zone_name': 'jobdetail__location__sous_zone__sous_zone_name',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..repositories.job_repository import JobRepository
        self.repository = JobRepository()

    def get_queryset(self):
        """
        Récupère les jobs via le repository avec relations préchargées.
        Valide que l'inventaire et l'entrepôt existent avant de retourner les jobs.
        Garantit que seuls les jobs d'inventaire pour l'entrepôt spécifié sont retournés.
        ⚠️ Règle: La vue ne doit PAS utiliser Job.objects directement.
        """
        inventory_id = self.kwargs.get('inventory_id')
        warehouse_id = self.kwargs.get('warehouse_id')
        
        # Validation explicite : s'assurer que l'inventaire existe
        inventory = self.repository.get_inventory_by_id(inventory_id)
        if not inventory:
            raise NotFound(f"Inventaire avec l'ID {inventory_id} non trouvé")
        
        # Validation explicite : s'assurer que l'entrepôt existe
        warehouse = self.repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise NotFound(f"Entrepôt avec l'ID {warehouse_id} non trouvé")
        
        # Retourner uniquement les jobs d'inventaire pour l'entrepôt spécifié
        return self.repository.get_jobs_for_inventory_warehouse_datatable(inventory_id, warehouse_id)
    
    def get_datatable_queryset(self):
        """
        Alias pour compatibilité avec l'ancien code.
        Délègue à get_queryset().
        """
        return self.get_queryset()


class JobFullDetailListView(ServerSideDataTableView):
    """
    Vue pour lister les jobs valides et entamés avec détails complets - Support DataTable.
    
    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés
    - Tri DataTable (order[0][column]=index&order[0][dir]=asc/desc)
    - Recherche sur champs multiples
    - Filtrage avancé avec django-filter
    - Pagination optimisée
    - Sérialisation flexible avec relations préchargées
    
    PARAMÈTRES DE REQUÊTE SUPPORTÉS:
    - Tri: ordering=reference, ordering=-created_at, ordering=status
    - Tri DataTable: order[0][column]=2&order[0][dir]=asc
    - Recherche: search=terme
    - Pagination: page=1&page_size=25
    - Filtres: status=valide, reference=JOB-xxx, emplacement_reference=LOC-xxx
    
    STATUTS INCLUS: VALIDE, AFFECTE, TRANSFERT, PRET, ENTAME
    """
    
    # Configuration de base
    model = Job
    serializer_class = JobFullDetailSerializer
    
    # Champs de recherche et tri - tous les champs disponibles
    search_fields = [
        'reference', 'status', 'created_at',
        'warehouse__warehouse_name', 'warehouse__reference',
        'inventory__reference', 'inventory__label',
        'jobdetail__location__location_reference',
        'jobdetail__location__sous_zone__sous_zone_name',
        'jobdetail__location__sous_zone__zone__zone_name',
        'assigment__counting__reference', 'assigment__counting__order',
        'assigment__session__username', 'assigment__status',
        'jobdetailressource__ressource__reference',
        'jobdetailressource__ressource__name'
    ]
    
    order_fields = [
        'id', 'reference', 'status', 'created_at',
        'warehouse__warehouse_name', 'warehouse__reference',
        'inventory__reference', 'inventory__label',
        'assigment__counting__order', 'assigment__status'
    ]
    default_order = '-created_at'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    export_filename = 'jobs_details_complets'
    
    # Champs de filtrage automatique
    filter_fields = [
        'status', 'reference', 'id',
        'emplacement_reference', 'sous_zone', 'zone',
        'session_username', 'ressource_reference', 'assignment_status',
        'counting_order'
    ]
    
    # Mapping frontend -> backend pour les filtres (JobTracking / Affecter)
    filter_aliases = {
        # identifiant / référence de job
        'id': 'id',
        'job': 'reference',
        'reference': 'reference',

        # statut du job
        'status': 'status',
        'statut': 'status',

        # emplacement et zones
        'emplacement': 'jobdetail__location__location_reference',
        'location_reference': 'jobdetail__location__location_reference',
        'zone_name': 'jobdetail__location__sous_zone__zone__zone_name',
        'sous_zone_name': 'jobdetail__location__sous_zone__sous_zone_name',

        # affectations / équipes / ressources
        'session': 'assigment__session__username',
        'team1': 'assigment__session__username',
        'team2': 'assigment__session__username',
        'ressource': 'jobdetailressource__ressource__reference',
        'resources': 'jobdetailressource__ressource__reference',
        'assignment_status': 'assigment__status',
        'counting_order': 'assigment__counting__order',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = JobRepository()
    
    def get_datatable_queryset(self):
        """
        Récupère les jobs validés et entamés via le repository avec relations préchargées.
        ⚠️ Règle: La vue ne doit PAS utiliser Job.objects directement.
        """
        warehouse_id = self.kwargs.get('warehouse_id')
        inventory_id = self.kwargs.get('inventory_id')
        return self.repository.get_validated_jobs_datatable(warehouse_id, inventory_id)

class JobPendingListView(ServerSideDataTableView):
    """
    Liste tous les jobs en attente avec leurs détails - Support DataTable.
    
    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés
    - Recherche sur champs multiples
    - Filtrage avancé avec django-filter
    - Pagination optimisée
    - Relations préchargées pour performance
    
    PARAMÈTRES:
    - Tri: ordering=reference, ordering=-created_at
    - Recherche: search=terme
    - Pagination: page=1&page_size=20
    - Filtres: reference=JOB-xxx, emplacement_reference=LOC-xxx
    """
    
    model = Job
    serializer_class = JobPendingSerializer
    filterset_class = JobFullDetailFilter
    
    # Champs de recherche et tri - tous les champs disponibles
    search_fields = [
        'reference', 'status', 'created_at',
        'warehouse__warehouse_name', 'warehouse__reference',
        'inventory__reference', 'inventory__label',
        'jobdetail__location__location_reference',
        'jobdetail__location__sous_zone__sous_zone_name',
        'jobdetail__location__sous_zone__zone__zone_name',
        'assigment__counting__reference', 'assigment__counting__order',
        'assigment__session__username', 'assigment__status',
        'jobdetailressource__ressource__reference',
        'jobdetailressource__ressource__name'
    ]
    
    order_fields = [
        'id', 'reference', 'status', 'created_at',
        'warehouse__warehouse_name', 'inventory__reference'
    ]
    default_order = '-created_at'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    export_filename = 'jobs_en_attente_liste'
    
    # Mapping pour les filtres
    filter_aliases = {
        'reference': 'reference',
        'status': 'status',
        'emplacement': 'jobdetail__location__location_reference',
        'session': 'assigment__session__username',
        'ressource': 'jobdetailressource__ressource__reference',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.repository = JobRepository()
    
    def get_datatable_queryset(self):
        """
        Récupère les jobs en attente via le repository avec relations préchargées.
        ⚠️ Règle: La vue ne doit PAS utiliser Job.objects directement.
        """
        return self.repository.get_pending_jobs_datatable()

class JobResetAssignmentsView(APIView):
    """
    Remet les assignements de plusieurs jobs en attente selon leur statut actuel
    """
    def post(self, request):
        serializer = JobResetAssignmentsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Formater les erreurs de manière sécurisée
            error_messages = []
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    error_messages.append(f"{field}: {', '.join(str(e) for e in errors)}")
                else:
                    error_messages.append(f"{field}: {str(errors)}")
            
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': ' | '.join(error_messages)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        job_ids = serializer.validated_data['job_ids']
        try:
            job_service = JobService()
            result = job_service.reset_jobs_assignments(job_ids)
            return success_response(
                data=result,
                message=f'{result["jobs_reset"]} jobs remis en attente avec succès'
            )
        except JobCreationError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                message="Une erreur inattendue s'est produite",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobTransferView(APIView):
    """
    Vue pour transférer les assignments par comptage qui sont au statut PRET.
    
    Règles métier :
    - Seuls les assignments au statut PRET peuvent être transférés
    - L'assignment doit correspondre au counting_order spécifié
    - Si l'assignment n'est pas PRET ou ne correspond pas au counting_order, 
      retourne un message d'erreur avec la référence du job et la raison
    """
    def post(self, request):
        serializer = JobTransferRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        job_ids = serializer.validated_data['job_ids']
        counting_orders = serializer.validated_data['counting_order']
        
        try:
            job_service = JobService()
            result = job_service.transfer_assignments_by_jobs_and_counting_orders(job_ids, counting_orders)
            return success_response(
                data=result,
                message=f'{result["total_transferred"]} assignment(s) transféré(s) avec succès'
            )
        except JobCreationError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors du transfert : {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors du transfert",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobManualEntryView(APIView):
    """
    Vue pour mettre les jobs et leurs assignments en statut SAISIE MANUELLE.
    
    Règles métier :
    - Seuls les jobs au statut PRET, TRANSFERT ou ENTAME peuvent être mis en saisie manuelle
    - Seuls les assignments au statut PRET, TRANSFERT ou ENTAME peuvent être mis en saisie manuelle
    - L'assignment doit correspondre au counting_order spécifié
    - Si le job ou l'assignment n'est pas dans un statut valide ou ne correspond pas au counting_order, 
      retourne un message d'erreur avec la référence du job et la raison
    """
    def post(self, request):
        serializer = JobManualEntryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        job_ids = serializer.validated_data['job_ids']
        counting_orders = serializer.validated_data['counting_order']
        
        try:
            job_service = JobService()
            result = job_service.set_manual_entry_status_by_jobs_and_counting_orders(job_ids, counting_orders)
            return success_response(
                data=result,
                message=f'{result["total_jobs"]} job(s) et {result["total_assignments"]} assignment(s) mis en saisie manuelle avec succès'
            )
        except JobCreationError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la mise en saisie manuelle : {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la mise en saisie manuelle",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 


class JobBatchAssignmentView(APIView):
    """
    API pour affecter des sessions et ressources à plusieurs jobs en lot
    """
    def post(self, request):
        try:
            print(request.data)
            serializer = JobBatchAssignmentRequestSerializer(data=request.data)
            if not serializer.is_valid():
                # Formater les erreurs de manière sécurisée
                error_messages = []
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        for error in errors:
                            if isinstance(error, dict):
                                # Si l'erreur est un dictionnaire, extraire le message
                                error_messages.append(f"{field}: {str(error)}")
                            else:
                                error_messages.append(f"{field}: {str(error)}")
                    else:
                        error_messages.append(f"{field}: {str(errors)}")
                
                return Response({
                    'success': False,
                    'message': 'Erreur de validation des données',
                    'errors': ' | '.join(error_messages)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            assignments_data = serializer.validated_data['assignments']
            
            # Utiliser le use case pour la logique métier
            use_case = JobBatchAssignmentUseCase()
            result = use_case.execute(assignments_data)
            
            return Response({
                'success': True,
                'message': result['message'],
                'data': result
            }, status=status.HTTP_200_OK)
            
        except JobCreationError as e:
            return Response({
                'success': False,
                'message': 'Erreur lors du traitement',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur dans JobBatchAssignmentView: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur',
                'errors': {
                    'detail': f'Erreur interne : {str(e)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


class JobProgressByCountingView(APIView):
    """
    Vue pour afficher l'avancement des emplacements par job et par counting
    """
    def get(self, request, job_id):
        try:
            job_service = JobService()
            progress_data = job_service.get_job_progress_by_counting(job_id)
            
            if progress_data['success']:
                return Response({
                    'success': True,
                    'data': progress_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': progress_data['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryProgressByCountingView(APIView):
    """
    Vue pour afficher l'avancement global d'un inventaire par counting
    """
    def get(self, request, inventory_id):
        try:
            job_service = JobService()
            progress_data = job_service.get_inventory_progress_by_counting(inventory_id)
            
            if progress_data['success']:
                return Response({
                    'success': True,
                    'data': progress_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': progress_data['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobsWithAssignmentsByWarehouseAndCountingView(ServerSideDataTableView):
    """
    API pour récupérer les jobs avec leurs assignments filtrés par warehouse et ordre de comptage.
    Support DataTable avec pagination, tri, recherche et filtrage.
    
    GET /api/inventory/warehouse/<int:warehouse_id>/counting/<int:counting_order>/jobs/
    
    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés
    - Recherche sur champs multiples
    - Filtrage avancé
    - Pagination optimisée
    - Relations préchargées pour performance
    
    PARAMÈTRES:
    - Tri: ordering=reference, ordering=-created_at, ordering=status
    - Recherche: search=terme
    - Pagination: page=1&page_size=20
    - Filtres: status=TERMINE, job_id=88, personne_1=BOUFENZI
    """
    
    # Configuration de base
    model = Assigment
    serializer_class = AssignmentFlatSerializer
    
    # Champs de recherche - tous les champs disponibles
    search_fields = [
        'job__reference',
        'job__status',
        'reference',
        'status',
        'counting__reference',
        'counting__order',
        'session__username',
        'personne__nom',
        'personne__prenom',
        'personne_two__nom',
        'personne_two__prenom',
        'job__warehouse__warehouse_name',
        'job__warehouse__reference',
        'job__inventory__reference',
        'job__inventory__label'
    ]
    
    # Champs de tri - tous les champs disponibles
    order_fields = [
        'id',
        'job_id',
        'job__reference',
        'job__status',
        'reference',
        'status',
        'counting__order',
        'counting__reference',
        'transfert_date',
        'entame_date',
        'affecte_date',
        'pret_date',
        'date_start',
        'created_at',
        'updated_at',
        'session__username',
        'personne__nom',
        'personne_two__nom'
    ]
    default_order = '-created_at'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    export_filename = 'jobs_avec_assignments'
    
    # Mapping frontend -> backend pour le filtrage par colonnes
    filter_aliases = {
        'job_id': 'job__id',
        'job_reference': 'job__reference',
        'job_status': 'job__status',
        'reference': 'reference',
        'status': 'status',
        'counting_order': 'counting__order',
        'counting_reference': 'counting__reference',
        'session_info': 'session__username',
        'personne_1': 'personne__nom',
        'personne_2': 'personne_two__nom',
        'warehouse_name': 'job__warehouse__warehouse_name',
        'inventory_reference': 'job__inventory__reference'
    }
    
    # Champs de date pour filtrage automatique
    date_fields = [
        'transfert_date',
        'entame_date',
        'affecte_date',
        'pret_date',
        'date_start',
        'created_at',
        'updated_at'
    ]
    
    # Champs de statut pour filtrage automatique
    status_fields = ['status', 'job__status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..repositories.job_repository import JobRepository
        self.repository = JobRepository()
    
    def get_datatable_queryset(self):
        """
        Récupère le queryset d'assignments filtrés par warehouse et counting_order.
        ⚠️ Règle: La vue ne doit PAS utiliser Assigment.objects directement.
        """
        warehouse_id = self.kwargs.get('warehouse_id')
        counting_order = self.kwargs.get('counting_order')
        
        # Valider les paramètres
        if not warehouse_id or warehouse_id <= 0:
            raise ValueError("L'ID de l'entrepôt doit être un entier positif")
        
        if not counting_order or counting_order <= 0:
            raise ValueError("L'ordre du comptage doit être un entier positif")
        
        return self.repository.get_assignments_by_warehouse_and_counting_queryset(
            warehouse_id=warehouse_id,
            counting_order=counting_order
        )


class JobDetailsByJobAndCountingView(ServerSideDataTableView):
    """
    Vue DataTable pour récupérer les JobDetail d'un job filtrés par ordre de comptage.
    Supporte automatiquement : tri, recherche, filtrage, pagination.
    Retourne uniquement location, status et les dates.
    """
    
    # Configuration minimale
    model = JobDetail
    serializer_class = JobDetailSimpleSerializer
    
    # Champs de recherche
    search_fields = [
        'location__location_reference',
        'location__sous_zone__sous_zone_name',
        'location__sous_zone__zone__zone_name',
        'status'
    ]
    
    # Champs de tri
    order_fields = [
        'id',
        'location__location_reference',
        'location__sous_zone__sous_zone_name',
        'status',
        'en_attente_date',
        'termine_date',
        'location__created_at',
        'location__updated_at'
    ]
    
    # Mapping frontend -> backend pour le filtrage par colonnes
    filter_aliases = {
        'id': 'location__id',
        'location_reference': 'location__location_reference',
        'sous_zone_name': 'location__sous_zone__sous_zone_name',
        'zone_name': 'location__sous_zone__zone__zone_name',
        'is_active': 'location__is_active',
        'status': 'status',
        'en_attente_date': 'en_attente_date',
        'termine_date': 'termine_date',
        'created_at': 'location__created_at',
        'updated_at': 'location__updated_at'
    }
    
    # Configuration par défaut
    default_order = 'location__location_reference'
    page_size = 20
    export_filename = 'job_details_par_comptage'
    
    # Champs de date pour filtrage automatique
    date_fields = ['en_attente_date', 'termine_date', 'location__created_at', 'location__updated_at']
    
    # Champs de statut pour filtrage automatique
    status_fields = ['status', 'location__is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = JobRepository()
    
    def get_datatable_queryset(self):
        """
        Récupère le queryset de JobDetail filtrés par job_id et counting_order.
        ⚠️ Règle: La vue ne doit PAS utiliser JobDetail.objects directement.
        """
        job_id = self.kwargs.get('job_id')
        counting_order = self.kwargs.get('counting_order')
        
        # Valider les paramètres
        if not job_id or job_id <= 0:
            return JobDetail.objects.none()
        
        if not counting_order or counting_order <= 0:
            return JobDetail.objects.none()
        
        # Récupérer le queryset via le repository
        return self.repository.get_job_details_by_job_and_counting_order_queryset(
            job_id=job_id,
            counting_order=counting_order
        ) 