from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import logging

from ..models import Inventory
from ..serializers.counting_tracking_serializer import InventoryCountingTrackingSerializer

logger = logging.getLogger(__name__)


class InventoryCountingTrackingView(APIView):
    """
    API pour le suivi d'un inventaire regroupé par comptages avec leurs jobs et emplacements
    """
    
    def get(self, request, inventory_id):
        """
        Récupère le suivi d'un inventaire avec tous ses comptages, jobs et emplacements
        
        Args:
            inventory_id: ID de l'inventaire à suivre
            
        Returns:
            Response avec les données de l'inventaire regroupées par comptages
        """
        try:
            # Récupérer l'inventaire avec tous ses comptages, jobs et emplacements
            inventory = get_object_or_404(
                Inventory.objects.prefetch_related(
                    'countings',
                    'job_set__warehouse',
                    'job_set__jobdetail_set__location__sous_zone__zone',
                    'job_set__jobdetail_set__location__sous_zone'
                ),
                id=inventory_id
            )
            
            serializer = InventoryCountingTrackingSerializer(inventory)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du suivi de l'inventaire {inventory_id}: {str(e)}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )