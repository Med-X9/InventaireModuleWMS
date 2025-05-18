from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.warehouse_service import WarehouseService
from ..serializers.warehouse_serializer import WarehouseSerializer
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