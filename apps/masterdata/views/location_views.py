from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.location_service import LocationService
from ..serializers.location_serializer import LocationSerializer
import logging

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