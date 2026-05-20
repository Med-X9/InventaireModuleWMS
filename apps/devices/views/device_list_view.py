import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.inventory.utils.response_utils import error_response, success_response
from apps.devices.services import DevicePresenceService

logger = logging.getLogger(__name__)


class DeviceStatusListView(APIView):
    """
    GET /web/api/devices/status/

    Liste des PDA avec statut online/offline calculé (seuil 120 s).
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Statut connectivité des PDA",
        manual_parameters=[
            openapi.Parameter(
                "warehouse_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False
            ),
            openapi.Parameter(
                "inventory_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False
            ),
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=["online", "offline", "all"],
                required=False,
            ),
        ],
        tags=["PDA / Supervision"],
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

        warehouse_id = request.query_params.get("warehouse_id")
        inventory_id = request.query_params.get("inventory_id")
        status_filter = (request.query_params.get("status") or "all").lower()

        if status_filter not in ("online", "offline", "all"):
            return error_response(
                message="Paramètre status invalide (online, offline, all).",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            wh_id = int(warehouse_id) if warehouse_id else None
        except ValueError:
            return error_response(
                message="warehouse_id doit être un entier.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            inv_id = int(inventory_id) if inventory_id else None
        except ValueError:
            return error_response(
                message="inventory_id doit être un entier.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = DevicePresenceService().list_with_status(
                warehouse_id=wh_id,
                inventory_id=inv_id,
                status_filter=status_filter,
            )
            return success_response(
                data=result["data"],
                message="Liste des PDA récupérée",
                meta=result["meta"],
            )
        except Exception:
            logger.exception("Erreur liste PDA")
            return error_response(
                message="Erreur lors de la récupération des PDA.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
