from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from ..services.location_service import LocationService
from ..serializers.location_serializer import LocationSerializer, UnassignedLocationSerializer
from rest_framework.permissions import IsAuthenticated
from ..models import Location, SousZone
import logging
from ..exceptions import LocationError
from ..repositories.location_repository import LocationRepository
from rest_framework.generics import ListAPIView
from ..filters.location_filters import UnassignedLocationFilter
from apps.inventory.models import Setting

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AllWarehouseLocationListView(APIView):
    def get(self, request, warehouse_id):
        """
        Récupère toutes les locations d'un warehouse directement
        
        Args:
            request: La requête HTTP
            warehouse_id: L'ID du warehouse
            
        Returns:
            Response: La réponse HTTP avec la liste des locations
        """
        try:
            result = LocationService.get_all_warehouse_locations(warehouse_id)
            
            if result['status'] == 'error':
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            # Sérialiser les données
            serializer = LocationSerializer(result['data'], many=True)
            
            return Response({
                'status': 'success',
                'message': result['message'],
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des locations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération des locations',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WarehouseJobLocationsView(APIView):
    def get(self, request, warehouse_id):
        """
        Récupère toutes les locations groupées par job pour un warehouse
        
        Args:
            request: La requête HTTP
            warehouse_id: L'ID du warehouse
            
        Returns:
            Response: La réponse HTTP avec la liste des jobs et leurs locations
        """
        try:
            result = LocationService.get_warehouse_job_locations(warehouse_id)
            
            if result['status'] == 'error':
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            # Sérialiser les locations pour chaque job
            for job_data in result['data']:
                location_serializer = LocationSerializer(job_data['locations'], many=True)
                job_data['locations'] = location_serializer.data
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des locations par job: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération des locations par job',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SousZoneLocationsView(APIView):
    """
    Vue pour récupérer toutes les locations d'une sous-zone spécifique.
    """
    permission_classes = [IsAuthenticated]
    location_repo = LocationRepository()
    
    def get(self, request, sous_zone_id):
        """
        Récupère toutes les locations d'une sous-zone spécifique.
        
        Args:
            sous_zone_id: ID de la sous-zone dont on veut récupérer les locations
        """
        try:
            SousZone.objects.get(pk=sous_zone_id)
            locations = self.location_repo.get_all().filter(
                sous_zone_id=sous_zone_id,
                is_active=True
            ).order_by('location_reference')
            serializer = LocationSerializer(locations, many=True)
            return Response(serializer.data)
        except SousZone.DoesNotExist:
            return Response(
                {"error": "Sous-zone non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UnassignedLocationsView(ListAPIView):
    """
    Vue pour lister les emplacements non affectés avec pagination et filtres.
    """
    serializer_class = UnassignedLocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UnassignedLocationFilter
    search_fields = [
        'reference', 'location_reference', 'description',
        'sous_zone__reference', 'sous_zone__sous_zone_name',
        'sous_zone__zone__reference', 'sous_zone__zone__zone_name',
        'sous_zone__zone__warehouse__reference', 'sous_zone__zone__warehouse__warehouse_name'
    ]
    ordering_fields = [
        'reference', 'location_reference', 'created_at', 'updated_at',
        'sous_zone__sous_zone_name', 'sous_zone__zone__zone_name',
        'sous_zone__zone__warehouse__warehouse_name'
    ]
    ordering = 'location_reference'  # Tri par défaut par référence d'emplacement
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Récupère les emplacements non affectés pour le warehouse et l'account spécifiés avec relations préchargées.
        """
        warehouse_id = self.kwargs.get('warehouse_id')
        account_id = self.kwargs.get('account_id')
        if not account_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'account_id': 'Ce paramètre est obligatoire dans l\'URL.'})
        if not warehouse_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'warehouse_id': 'Ce paramètre est obligatoire dans l\'URL.'})

        queryset = Location.objects.filter(is_active=True)
        # Filtrer par warehouse si spécifié
        if warehouse_id:
            queryset = queryset.filter(sous_zone__zone__warehouse_id=warehouse_id)

        # Filtrer par regroupement.account lié à l'account_id
        queryset = queryset.filter(regroupement__account_id=account_id)

        # Exclure les emplacements qui sont déjà affectés à des jobs
        from apps.inventory.models import JobDetail
        assigned_location_ids = JobDetail.objects.values_list('location_id', flat=True)
        queryset = queryset.exclude(id__in=assigned_location_ids)

        # Précharger les relations pour optimiser les performances
        queryset = queryset.select_related(
            'sous_zone',
            'sous_zone__zone',
            'sous_zone__zone__warehouse',
            'location_type',
            'regroupement',
            'regroupement__account',
        ).prefetch_related(
            'stock_set__product__Product_Family'
        ).order_by('location_reference')

        return queryset

    def get(self, request, *args, **kwargs):
        """
        Récupère les emplacements non affectés avec filtres et pagination.
        """
        try:
            # Utiliser la méthode parent pour le filtrage et la pagination
            response = super().get(request, *args, **kwargs)
            
            # Ajouter un message de succès
            response.data['message'] = "Liste des emplacements non affectés récupérée avec succès"
            return response

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des emplacements non affectés: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LocationDetailView(APIView):
    permission_classes = [IsAuthenticated]
    location_repo = LocationRepository()
    def get(self, request, pk):
        try:
            location = self.location_repo.get_by_id(pk)
            serializer = LocationSerializer(location)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            ) 