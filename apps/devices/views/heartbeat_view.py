import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.inventory.utils.response_utils import error_response, success_response
from apps.devices.serializers import HeartbeatSerializer
from apps.devices.services import DevicePresenceService

logger = logging.getLogger(__name__)


class DeviceHeartbeatView(APIView):
    """
    POST /mobile/api/devices/heartbeat/

    Enregistre le signal du PDA Flutter (JWT utilisateur Mobile).
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Heartbeat PDA",
        operation_description="Upsert du terminal et mise à jour de last_seen_at (horloge serveur).",
        request_body=HeartbeatSerializer,
        responses={200: "Heartbeat enregistré"},
        tags=["PDA / Mobile"],
        security=[{"Bearer": []}],
    )
    def post(self, request):
        user = request.user
        if getattr(user, "type", None) != "Mobile":
            return error_response(
                message="Accès réservé aux utilisateurs mobile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = HeartbeatSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Données heartbeat invalides.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = DevicePresenceService().upsert_heartbeat(
                user, serializer.validated_data, request
            )
            return success_response(
                data=data,
                message="Heartbeat enregistré",
            )
        except Exception:
            logger.exception("Erreur heartbeat PDA")
            return error_response(
                message="Erreur lors de l'enregistrement du heartbeat.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
