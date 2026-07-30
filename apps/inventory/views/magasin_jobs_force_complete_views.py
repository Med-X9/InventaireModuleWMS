"""
Vue : clôture forcée jobs MAGASIN (article technique + qté 0).
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.inventory.exceptions.job_exceptions import JobCreationError
from apps.inventory.serializers.job_serializer import MagasinJobsForceCompleteSerializer
from apps.inventory.services.magasin_jobs_force_complete_service import (
    MagasinJobsForceCompleteService,
)
from apps.inventory.utils.response_utils import (
    error_response,
    success_response,
    validation_error_response,
)

logger = logging.getLogger(__name__)


class MagasinJobsForceCompleteView(APIView):
    """
    Termine des jobs sélectionnés pour inventaire MAGASIN uniquement.

    Pour chaque job :
    - crée CountingDetail (barcode technique, qté 0) par emplacement
    - JobDetail / Assignment / Job → TERMINE

    POST /web/api/jobs/magasin/force-complete/
    Body: { "job_ids": [621, 622], "barcode": "11111111111", "quantity": 0 }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MagasinJobsForceCompleteSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        job_ids = serializer.validated_data["job_ids"]
        barcode = serializer.validated_data.get("barcode")
        quantity = serializer.validated_data.get("quantity", 0)

        try:
            result = MagasinJobsForceCompleteService().force_complete(
                job_ids=job_ids,
                barcode=barcode,
                quantity=quantity,
            )
            return success_response(
                data=result,
                message=(
                    f"Clôture MAGASIN : {result['jobs_closed']}/"
                    f"{result['jobs_requested']} job(s) terminé(s)"
                ),
                status_code=status.HTTP_200_OK,
            )
        except JobCreationError as exc:
            return error_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.error(
                "Erreur force-complete MAGASIN: %s", exc, exc_info=True
            )
            return error_response(
                message="Erreur lors de la clôture forcée des jobs MAGASIN",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
