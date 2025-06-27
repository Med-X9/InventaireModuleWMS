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
    JobListWithLocationsSerializer
)
from ..exceptions import JobCreationError
import logging
from datetime import datetime
from ..models import Job, Warehouse
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from ..filters.job_filters import JobFilter

logger = logging.getLogger(__name__)

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
            jobs = JobService.create_jobs_for_inventory_warehouse(inventory_id, warehouse_id, emplacements)
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
            result = JobService.validate_jobs(job_ids)
            return Response({
                'success': True,
                'message': 'Jobs validés avec succès',
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
    def delete(self, request, job_id):
        try:
            result = JobService.delete_job(job_id)
            return Response({
                'success': True,
                'message': 'Job supprimé avec succès',
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

class JobRemoveEmplacementsView(APIView):
    def delete(self, request, job_id):
        serializer = JobRemoveEmplacementsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        emplacement_ids = serializer.validated_data['emplacement_ids']
        try:
            result = JobService.remove_job_emplacements(job_id, emplacement_ids)
            return Response({
                'success': True,
                'message': 'Emplacements supprimés avec succès',
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
            result = JobService.add_job_emplacements(job_id, emplacement_ids)
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

class PendingJobsReferencesView(APIView):
    def get(self, request, warehouse_id):
        try:
            pending_jobs = JobService.get_pending_jobs_references(warehouse_id)
            return Response({
                'success': True,
                'message': 'Jobs en attente récupérés avec succès',
                'data': pending_jobs
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
    Récupère tous les jobs d'un warehouse spécifique
    """
    serializer_class = JobListWithLocationsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['reference']
    ordering_fields = ['created_at', 'status', 'reference']
    pagination_class = JobListPagination

    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        return Job.objects.filter(warehouse_id=warehouse_id).order_by('-created_at') 