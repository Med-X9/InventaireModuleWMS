"""
API REST : liste des appareils mobiles connectés (lecture Redis, pas de table SQL).
"""

import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.inventory.utils.response_utils import error_response, success_response
from apps.realtime.services.presence_api_service import PresenceApiService

logger = logging.getLogger(__name__)


class ConnectedDevicesListView(APIView):
    """
    GET /web/api/presence/connected-devices/

    Retourne les terminaux mobiles actuellement en ligne (présence Redis + heartbeat).
    Complète le WebSocket dashboard pour l'affichage initial du front.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Liste des appareils mobiles connectés",
        operation_description=(
            "Lit l'état de présence volatile dans Redis (sans base de données). "
            "Un appareil est « online » tant que sa clé Redis existe (heartbeat actif)."
        ),
        responses={
            200: openapi.Response(description="Liste des devices connectés"),
            503: openapi.Response(description="Redis indisponible"),
        },
        tags=["Présence mobile"],
        security=[{"Bearer": []}],
    )
    def get(self, request):
        user = request.user
        user_type = getattr(user, "type", None)
        if user_type != "Web" and not getattr(user, "is_staff", False):
            return error_response(
                message="Accès réservé aux utilisateurs web.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        try:
            data = PresenceApiService().get_connected_devices()
            return success_response(
                data=data,
                message="Appareils connectés récupérés avec succès",
            )
        except Exception as e:
            logger.exception("Erreur lecture présence Redis: %s", e)
            return error_response(
                message="Service de présence temporairement indisponible.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error_type="PRESENCE_UNAVAILABLE",
            )
