from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.masterdata.models import Warehouse
from apps.masterdata.serializers.warehouse_serializer import WarehouseSerializer
import logging

logger = logging.getLogger(__name__)

class InventoryWarehousesView(APIView):
    """
    Vue pour récupérer la liste des entrepôts associés à un inventaire.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, inventory_id):
        """
        Récupère la liste des entrepôts associés à un inventaire.
        
        Args:
            request: La requête HTTP
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Response: La réponse HTTP avec la liste des entrepôts
        """
        try:
            # Récupérer tous les entrepôts actifs
            warehouses = Warehouse.objects.filter(status='ACTIVE')
            
            # Sérialiser les données
            serializer = WarehouseSerializer(warehouses, many=True)
            
            return Response({
                'status': 'success',
                'message': 'Liste des entrepôts récupérée avec succès',
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des entrepôts: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Erreur lors de la récupération des entrepôts',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 