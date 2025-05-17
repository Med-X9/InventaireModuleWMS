from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.pda_service import PDAService
from ..serializers.pda_serializer import PDASerializer
from ..exceptions import PdaNotFoundError
import logging

logger = logging.getLogger(__name__)

class InventoryPDAListView(APIView):
    def get(self, request, inventory_id):
        """
        Récupère la liste des PDAs d'un inventaire
        
        Args:
            request: La requête HTTP
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Response: La réponse HTTP avec la liste des PDAs
        """
        try:
            logger.info(f"Récupération des PDAs pour l'inventaire {inventory_id}")
            
            # Récupérer les PDAs
            pdas = PDAService.get_inventory_pdas(inventory_id)
            
            # Sérialiser les données
            serializer = PDASerializer(pdas, many=True)
            
            logger.info(f"{len(serializer.data)} PDAs trouvés pour l'inventaire {inventory_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except PdaNotFoundError as e:
            logger.error(f"Erreur lors de la récupération des PDAs: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des PDAs: {str(e)}")
            return Response(
                {'error': "Une erreur inattendue s'est produite lors de la récupération des PDAs"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 