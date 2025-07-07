from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.warehouse_service import WarehouseService
from ..serializers.warehouse_serializer import WarehouseSerializer
from ..exceptions import WarehouseNotFoundError
import logging

logger = logging.getLogger(__name__)

class WarehouseListView(APIView):
    """
    API View pour gérer les entrepôts
    """
    def get(self, request, *args, **kwargs):
        """
        Récupère la liste de tous les entrepôts
        
        Args:
            request: La requête HTTP
            
        Returns:
            Response: La réponse HTTP avec la liste des entrepôts
        """
        try:
            # Récupérer les entrepôts via le service
            warehouses = WarehouseService.get_all_warehouses()
            
            # Sérialiser les données
            serializer = WarehouseSerializer(warehouses, many=True)
            
            return Response({
                'status': 'success',
                'message': f"{len(serializer.data)} entrepôts trouvés",
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des entrepôts: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération des entrepôts',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WarehouseDetailByReferenceView(APIView):
    """
    API View pour récupérer un entrepôt par sa référence
    """
    def get(self, request, reference, *args, **kwargs):
        """
        Récupère un entrepôt par sa référence
        
        Args:
            request: La requête HTTP
            reference: La référence de l'entrepôt
            
        Returns:
            Response: La réponse HTTP avec les détails de l'entrepôt
        """
        try:
            # Récupérer l'entrepôt via le service
            warehouse_service = WarehouseService()
            warehouse = warehouse_service.get_warehouse_by_reference(reference)
            
            # Sérialiser les données
            serializer = WarehouseSerializer(warehouse)
            
            return Response({
                'status': 'success',
                'message': f"Entrepôt '{reference}' trouvé avec succès",
                'data': serializer.data
            })
            
        except WarehouseNotFoundError as e:
            logger.warning(f"Entrepôt avec la référence '{reference}' non trouvé")
            return Response({
                'status': 'error',
                'message': str(e),
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération de l'entrepôt '{reference}': {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération de l\'entrepôt',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 