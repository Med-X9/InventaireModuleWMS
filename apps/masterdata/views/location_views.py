from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.location_service import LocationService
from ..serializers.location_serializer import LocationSerializer, UnassignedLocationSerializer
from rest_framework.permissions import IsAuthenticated
from ..models import Location, SousZone
import logging
from ..exceptions import LocationError
from ..repositories.location_repository import LocationRepository

logger = logging.getLogger(__name__)

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

class UnassignedLocationsView(APIView):
    def get(self, request, warehouse_id=None):
        """
        Récupère les emplacements qui ne sont pas affectés à des jobs
        avec les informations complètes de zone et sous-zone
        """
        try:
            unassigned_locations = LocationService.get_unassigned_locations(warehouse_id)
            
            # Sérialiser les données
            serializer = UnassignedLocationSerializer(unassigned_locations, many=True)
            
            return Response({
                'success': True,
                'message': 'Emplacements non affectés récupérés avec succès',
                'data': serializer.data,
                'count': len(unassigned_locations)
            }, status=status.HTTP_200_OK)
            
        except LocationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des emplacements non affectés : {str(e)}")
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