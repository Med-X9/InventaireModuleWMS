"""
Vues pour le monitoring par zone
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.monitoring_service import MonitoringService
from ..serializers.monitoring_serializer import (
    MonitoringResponseSerializer,
    GlobalMonitoringSerializer,
)
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
    - nombre_emplacements : nombre d'emplacements distincts
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


class GlobalMonitoringByInventoryAndWarehouseView(APIView):
    """
    Vue pour récupérer le monitoring global (toutes zones confondues)
    pour un inventaire et un entrepôt.

    GET /inventory/<inventory_id>/warehouses/<warehouse_id>/global-monitoring/

    Retourne :
    - total_equipes : nombre d'équipes distinctes affectées
    - total_jobs : nombre de jobs affectés
    - countings : pour les comptages d'ordre 1, 2 et 3 :
        - jobs_termines
        - jobs_termines_percent
    """

    def get(self, request, inventory_id: int, warehouse_id: int):
        """
        Récupère le monitoring global.

        Args:
            request: Requête HTTP
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt

        Returns:
            Response avec les statistiques globales
        """
        try:
            service = MonitoringService()
            stats = service.get_global_monitoring_by_inventory_and_warehouse(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
            )

            serializer = GlobalMonitoringSerializer(data=stats)
            serializer.is_valid(raise_exception=True)

            return success_response(
                data=serializer.validated_data,
                message="Monitoring global récupéré avec succès",
            )

        except JobCreationError as e:
            logger.error(
                f"Erreur métier lors de la récupération du monitoring global: {str(e)}"
            )
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de la récupération du monitoring global: {str(e)}"
            )
            return error_response(
                message=(
                    "Une erreur est survenue lors de la récupération du "
                    f"monitoring global: {str(e)}"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

