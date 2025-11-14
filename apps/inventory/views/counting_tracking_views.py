from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

from ..services.counting_tracking_service import CountingTrackingService
from ..serializers.counting_tracking_serializer import InventoryCountingTrackingSerializer
from ..exceptions.inventory_exceptions import InventoryNotFoundError

logger = logging.getLogger(__name__)


class InventoryCountingTrackingView(APIView):
    """
    API pour le suivi d'un inventaire regroupé par comptages avec leurs jobs et emplacements.
    
    Cette vue respecte l'architecture Repository/Service/View :
    - La vue appelle le service (pas le repository directement)
    - Le service gère la logique métier
    - Le repository gère l'accès aux données
    """
    
    def get(self, request, inventory_id):
        """
        Récupère le suivi d'un inventaire avec tous ses comptages, jobs et emplacements.
        
        Paramètres de requête:
            counting_order (requis): Ordre du comptage à filtrer (ex: ?counting_order=1)
        
        Args:
            inventory_id: ID de l'inventaire à suivre
            
        Returns:
            Response avec les données de l'inventaire regroupées par comptages
        """
        try:
            # Extraire le paramètre de filtre par ordre de comptage (obligatoire)
            counting_order = request.query_params.get('counting_order')
            if counting_order is None:
                return Response(
                    {'error': 'Le paramètre counting_order est requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                counting_order = int(counting_order)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Le paramètre counting_order doit être un nombre entier'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialiser le service et récupérer l'inventaire avec toutes ses relations
            counting_tracking_service = CountingTrackingService()
            inventory = counting_tracking_service.get_inventory_counting_tracking(inventory_id, counting_order)
            
            # Sérialiser les données
            serializer = InventoryCountingTrackingSerializer(inventory)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire {inventory_id} non trouvé: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du suivi de l'inventaire {inventory_id}: {str(e)}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )