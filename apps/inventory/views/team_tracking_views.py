import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ..services.team_tracking_service import TeamTrackingService
from ..utils.response_utils import success_response, error_response

logger = logging.getLogger(__name__)


class TeamTrackingView(APIView):
    """
    Suivi par équipe : jobs de chaque équipe (statuts EN ATTENTE, ENTAME, TERMINE, BLOQUE).

    URL: /api/inventory/{inventory_id}/warehouse/{warehouse_id}/teams-tracking/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, inventory_id: int, warehouse_id: int):
        try:
            data = TeamTrackingService().get_team_tracking(inventory_id, warehouse_id)
            return success_response(data=data, message="Suivi par équipe récupéré")
        except Exception as exc:
            logger.error("Erreur suivi par équipe: %s", exc, exc_info=True)
            return error_response(
                message=f"Erreur lors du suivi par équipe: {exc}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
