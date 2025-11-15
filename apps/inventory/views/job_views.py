from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from ..serializers import (
    InventoryJobCreateSerializer,
    JobSerializer
)
from apps.core.datatables.filters import CompositeDataTableFilter, DjangoFilterDataTableFilter, FilterMappingFilter

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
    JobProgressByCountingSerializer
)
from ..serializers.job_assignment_batch_serializer import JobBatchAssignmentRequestSerializer
from ..usecases.job_batch_assignment import JobBatchAssignmentUseCase
from ..exceptions import JobCreationError
import logging
from datetime import datetime
from ..models import Job, Warehouse
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
    Vue pour marquer plusieurs jobs et un comptage spécifique comme PRET
    
    Permet de mettre en statut PRET plusieurs jobs et un comptage spécifique identifié par son ordre (1, 2 ou 3).
    """
    
    def post(self, request):
        """
        Marque plusieurs jobs et un comptage spécifique (par ordre) comme PRET
        
        Body attendu:
        {
            "job_ids": [1, 2, 3],
            "counting_order": 1  # ou 2, ou 3
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
        counting_order = serializer.validated_data['counting_order']
        
        try:
            # Utiliser le use case pour la logique métier
            from ..usecases.job_ready import JobReadyUseCase
            use_case = JobReadyUseCase()
            result = use_case.execute(job_ids, counting_order)
            
            return Response({
                'success': True,
                'message': result['message'],
                'data': {
                    'counting_order': result['counting_order'],
                    'jobs_processed': result['jobs_processed'],
                    'assignments_processed': result['assignments_processed'],
                    'jobs': result['jobs'],
                    'assignments': result['assignments']
                }
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
    search_fields = ['reference', 'inventory__reference', 'inventory__label', 'warehouse__reference', 'warehouse__warehouse_name']
    order_fields = ['created_at', 'reference', 'inventory__reference', 'warehouse__warehouse_name']
    default_order = '-created_at'
    page_size = 20
    min_page_size = 1
    max_page_size = 100
    
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
    max_page_size = 100

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
    max_page_size = 100
    
    # Mapping pour les filtres
    filter_aliases = {
        'reference': 'reference',
        'status': 'status',
        'warehouse': 'warehouse__warehouse_name',
        'inventory': 'inventory__reference',
        'location': 'jobdetail__location__location_reference',
        'sous_zone': 'jobdetail__location__sous_zone__sous_zone_name',
        'zone': 'jobdetail__location__sous_zone__zone__zone_name',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..repositories.job_repository import JobRepository
        self.repository = JobRepository()
    
    def get_datatable_filter(self):
        """Filtre unifié qui gère automatiquement tout"""

        
        composite_filter = CompositeDataTableFilter()
        
        # Filtre Django Filter si configuré
        if self.filterset_class:
            composite_filter.add_filter(DjangoFilterDataTableFilter(self.filterset_class))
        
        # Filtre de mapping qui gère automatiquement tous les opérateurs
        mapping_filter = FilterMappingFilter(self.filter_aliases)
        composite_filter.add_filter(mapping_filter)
        
        return composite_filter
    
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
    search_fields = ['reference']
    order_fields = ['created_at', 'status', 'reference']
    default_order = '-created_at'
    page_size = 20
    min_page_size = 1
    max_page_size = 100
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..repositories.job_repository import JobRepository
        self.repository = JobRepository()

    def get_datatable_queryset(self):
        """
        Récupère les jobs via le repository avec relations préchargées.
        ⚠️ Règle: La vue ne doit PAS utiliser Job.objects directement.
        """
        inventory_id = self.kwargs.get('inventory_id')
        warehouse_id = self.kwargs.get('warehouse_id')
        return self.repository.get_jobs_for_inventory_warehouse_datatable(inventory_id, warehouse_id)


class JobFullDetailListView(ServerSideDataTableView):
    """
    Vue pour lister les jobs valides avec détails complets - Support DataTable.
    
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
    """
    
    # Configuration de base
    model = Job
    serializer_class = JobFullDetailSerializer
    
    # Champs de recherche et tri
    search_fields = [
        'reference', 'status', 'created_at', 'warehouse__warehouse_name',
        'inventory__reference', 'inventory__label', 'jobdetail__location__location_reference',
        'assigment__counting__reference', 'assigment__session__username',
        'jobdetailressource__ressource__reference'
    ]
    
    order_fields = [
        'id', 'reference', 'status', 'created_at', 'warehouse__warehouse_name',
        'inventory__reference', 'inventory__label'
    ]
    default_order = '-created_at'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 100
    
    # Champs de filtrage automatique
    filter_fields = [
        'status', 'reference', 'id',
        'emplacement_reference', 'sous_zone', 'zone',
        'session_username', 'ressource_reference', 'assignment_status',
        'counting_order'
    ]
    
    # Mapping pour les filtres
    filter_aliases = {
        'reference': 'reference',
        'status': 'status',
        'emplacement': 'jobdetail__location__location_reference',
        'session': 'assigment__session__username',
        'ressource': 'jobdetailressource__ressource__reference',
        'assignment_status': 'assigment__status',
        'counting_order': 'assigment__counting__order',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = JobRepository()
    
    def get_datatable_filter(self):
        """Filtre unifié qui gère automatiquement tout"""

        
        composite_filter = CompositeDataTableFilter()
        
        # Filtre Django Filter si configuré
        if self.filterset_class:
            composite_filter.add_filter(DjangoFilterDataTableFilter(self.filterset_class))
        
        # Filtre de mapping qui gère automatiquement tous les opérateurs
        mapping_filter = FilterMappingFilter(self.filter_aliases)
        composite_filter.add_filter(mapping_filter)
        
        return composite_filter

    def get_datatable_queryset(self):
        """
        Récupère les jobs validés via le repository avec relations préchargées.
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
    
    # Champs de recherche et tri
    search_fields = [
        'reference', 'status', 'created_at',
        'jobdetail__location__location_reference',
        'assigment__counting__reference', 'assigment__session__username',
        'jobdetailressource__ressource__reference'
    ]
    
    order_fields = [
        'id', 'reference', 'status', 'created_at'
    ]
    default_order = '-created_at'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 100
    
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
    
    def get_datatable_filter(self):
        """Filtre unifié qui gère automatiquement tout"""
        
        composite_filter = CompositeDataTableFilter()
        
        # Filtre Django Filter si configuré
        if self.filterset_class:
            composite_filter.add_filter(DjangoFilterDataTableFilter(self.filterset_class))
        
        # Filtre de mapping qui gère automatiquement tous les opérateurs
        mapping_filter = FilterMappingFilter(self.filter_aliases)
        composite_filter.add_filter(mapping_filter)
        
        return composite_filter

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
            return Response({
                'success': True,
                'message': f'{result["jobs_reset"]} jobs remis en attente avec succès',
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

class JobTransferView(APIView):
    """
    Vue pour transférer les jobs par comptage qui sont au statut PRET
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
            result = job_service.transfer_jobs_by_counting_orders(job_ids, counting_orders)
            return Response({
                'success': True,
                'message': f'{result["total_transferred"]} jobs transférés avec succès',
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