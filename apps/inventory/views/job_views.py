from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
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
    PendingJobReferenceSerializer
)
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
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        emplacements = serializer.validated_data['emplacements']
        try:
            job_service = JobService()
            jobs = job_service.create_jobs_for_inventory_warehouse(inventory_id, warehouse_id, emplacements)
            return Response({
                'success': True,
                'message': 'Jobs créés avec succès',
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
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
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
        serializer = JobReadyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
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
        serializer = JobRemoveEmplacementsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Erreur de validation', 
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        emplacement_id = serializer.validated_data['emplacement_id']
        try:
            job_service = JobService()
            result = job_service.remove_job_emplacements(job_id, emplacement_id)
            return Response({
                'success': True,
                'message': 'Emplacement supprimé avec succès',
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
            job_service = JobService()
            result = job_service.add_job_emplacements(job_id, emplacement_ids)
            return Response({
                'success': True,
                'message': 'Emplacements ajoutés avec succès',
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
        queryset = Job.objects.filter(status='VALIDE').order_by('-created_at')
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
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        job_ids = serializer.validated_data['job_ids']
        try:
            # Utiliser le use case pour la logique métier
            from ..usecases.job_reset_assignments import JobResetAssignmentsUseCase
            use_case = JobResetAssignmentsUseCase()
            result = use_case.execute(job_ids)
            
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