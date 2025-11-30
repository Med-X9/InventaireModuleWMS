"""
Vues pour le monitoring par zone
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.monitoring_service import MonitoringService
from ..serializers.monitoring_serializer import MonitoringResponseSerializer
from ..exceptions.job_exceptions import JobCreationError
from ..utils.response_utils import success_response, error_response

logger = logging.getLogger(__name__)


class ZoneMonitoringByInventoryAndWarehouseView(APIView):
    """
    Vue pour récupérer le monitoring par zone pour un inventaire et un entrepôt.
    
    GET /inventory/<inventory_id>/warehouse/<warehouse_id>/monitoring/
    
    Retourne pour chaque zone :
    - nombre_equipes : nombre d'équipes distinctes
    - nombre_jobs : nombre de jobs
    - countings : pour chaque comptage, les statistiques des jobs (en attente, en cours, terminés)
    """
    
    def get(self, request, inventory_id: int, warehouse_id: int):
        """
        Récupère le monitoring par zone.
        
        Args:
            request: Requête HTTP
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            
        Returns:
            Response avec le monitoring par zone
        """
        try:
            service = MonitoringService()
            zone_stats = service.get_zone_monitoring_by_inventory_and_warehouse(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id
            )
            
            # Formater la réponse
            response_data = {
                'zones': zone_stats
            }
            
            # Valider avec le serializer
            serializer = MonitoringResponseSerializer(data=response_data)
            if serializer.is_valid():
                return success_response(
                    data=serializer.validated_data,
                    message="Monitoring par zone récupéré avec succès"
                )
            else:
                logger.warning(f"Erreur de validation du serializer: {serializer.errors}")
                return success_response(
                    data=response_data,
                    message="Monitoring par zone récupéré avec succès"
                )
                
        except JobCreationError as e:
            logger.error(f"Erreur métier lors de la récupération du monitoring: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération du monitoring: {str(e)}")
            return error_response(
                message=f"Une erreur est survenue lors de la récupération du monitoring: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

