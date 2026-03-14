from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.masterdata.models import Warehouse
from apps.masterdata.serializers.warehouse_serializer import WarehouseSerializer
from ..serializers.warehouse_serializer import WarehouseListSerializer
from ..services.warehouse_service import WarehouseService
from ..exceptions import (
    WarehouseAccountValidationError,
    WarehouseAccountNotFoundError,
)
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


class AccountWarehousesView(APIView):
    """
    Vue pour récupérer les entrepôts associés à un compte.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self, warehouse_service: WarehouseService | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.warehouse_service = warehouse_service or WarehouseService()

    def get(self, request, account_id: int):
        """
        Récupère les entrepôts associés à un compte donné.
        """
        try:
            warehouses = self.warehouse_service.get_warehouses_by_account(account_id)
            serializer = WarehouseListSerializer(warehouses, many=True)
            return Response({
                'status': 'success',
                'message': 'Liste des entrepôts récupérée avec succès',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except WarehouseAccountValidationError as exc:
            logger.warning("Validation échouée pour la récupération des entrepôts: %s", exc)
            return Response({
                'status': 'error',
                'message': str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
        except WarehouseAccountNotFoundError as exc:
            logger.info("Aucun entrepôt trouvé pour le compte demandé: %s", exc)
            return Response({
                'status': 'error',
                'message': str(exc)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error("Erreur inattendue lors de la récupération des entrepôts pour le compte %s: %s", account_id, exc, exc_info=True)
            return Response({
                'status': 'error',
                'message': 'Erreur lors de la récupération des entrepôts',
                'error': str(exc)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)