from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from ..serializers import (
    InventoryJobCreateSerializer,
    JobSerializer
)
from ..services.job_service import JobService
from ..serializers.job_serializer import (
    InventoryJobRetrieveSerializer, 
    InventoryJobUpdateSerializer,
    JobAssignmentRequestSerializer,
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

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

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
    def post(self, request):
        print(request.data)
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
        try:
            # Utiliser le use case pour la logique métier
            from ..usecases.job_ready import JobReadyUseCase
            use_case = JobReadyUseCase()
            result = use_case.execute(job_ids)
            
            return Response({
                'success': True,
                'message': result['message'],
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

class PendingJobsReferencesView(ListAPIView):
    """
    Vue pour lister les jobs en attente avec pagination et filtres.
    """
    serializer_class = PendingJobReferenceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PendingJobFilter
    search_fields = ['reference', 'inventory__reference', 'inventory__label', 'warehouse__reference', 'warehouse__warehouse_name']
    ordering_fields = ['created_at', 'reference', 'inventory__reference', 'warehouse__warehouse_name']
    ordering = '-created_at'  # Tri par défaut par date de création (plus récent en premier)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Récupère les jobs en attente pour le warehouse spécifié avec relations préchargées.
        """
        warehouse_id = self.kwargs.get('warehouse_id')
        return Job.objects.filter(
            warehouse_id=warehouse_id,
            status='EN ATTENTE'
        ).select_related(
            'inventory',
            'warehouse'
        ).prefetch_related(
            'jobdetail_set',
            'assigment_set'
        ).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        """
        Récupère les jobs en attente avec filtres et pagination.
        """
        try:
            # Utiliser la méthode parent pour le filtrage et la pagination
            response = super().get(request, *args, **kwargs)
            
            # Ajouter un message de succès
            response.data['message'] = "Liste des jobs en attente récupérée avec succès"
            return response

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des jobs en attente: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JobListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class JobListWithLocationsView(ListAPIView):
    queryset = Job.objects.all().order_by('-created_at')
    serializer_class = JobListWithLocationsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['reference']
    ordering_fields = ['created_at', 'status', 'reference']
    pagination_class = JobListPagination

class WarehouseJobsView(ListAPIView):
    """
    Récupère tous les jobs d'un warehouse spécifique pour un inventaire donné
    """
    serializer_class = JobListWithLocationsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['reference']
    ordering_fields = ['created_at', 'status', 'reference']
    pagination_class = JobListPagination

    def get_queryset(self):
        inventory_id = self.kwargs.get('inventory_id')
        warehouse_id = self.kwargs.get('warehouse_id')
        return Job.objects.filter(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        ).prefetch_related(
            'jobdetail_set__location__sous_zone__zone'
        ).order_by('-created_at')

class JobFullDetailPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class JobFullDetailListView(ListAPIView):
    serializer_class = JobFullDetailSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFullDetailFilter
    search_fields = ['reference']
    ordering_fields = ['created_at', 'status', 'reference']
    pagination_class = JobFullDetailPagination

    def get_queryset(self):
        queryset = Job.objects.filter(status__in=['VALIDE', 'AFFECTE']).order_by('-created_at')
        warehouse_id = self.kwargs.get('warehouse_id')
        inventory_id = self.kwargs.get('inventory_id')
        if warehouse_id is not None:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if inventory_id is not None:
            queryset = queryset.filter(inventory_id=inventory_id)
        return queryset
class JobPendingListView(ListAPIView):
    """
    Liste tous les jobs en attente avec leurs détails
    """
    queryset = Job.objects.filter(status='EN ATTENTE').order_by('-created_at')
    serializer_class = JobPendingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFullDetailFilter
    search_fields = ['reference']
    ordering_fields = ['created_at', 'reference']
    pagination_class = JobFullDetailPagination

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
        counting_order = serializer.validated_data['counting_order']
        
        try:
            job_service = JobService()
            result = job_service.transfer_jobs_by_counting_order(job_ids, counting_order)
            return Response({
                'success': True,
                'message': f'{result["total_transferred"]} jobs transférés avec succès pour le comptage d\'ordre {counting_order}',
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