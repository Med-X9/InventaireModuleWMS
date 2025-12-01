from typing import Any, List

import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.job_discrepancy_service import JobDiscrepancyService
from ..serializers.job_discrepancy_serializer import (
    CountingJobsDiscrepancySerializer,
)
from ..utils.response_utils import success_response, error_response

logger = logging.getLogger(__name__)


class JobsWithUnresolvedDiscrepanciesByCountingView(APIView):
    """
    API pour récupérer les jobs ayant au moins un écart de comptage non résolu,
    regroupés par comptage (counting.order) pour un inventaire et un entrepôt.

    Exemple de réponse :
    [
        {
            "counting_order": 3,
            "jobs": [
                {"job_id": 1, "job_reference": "job-1"},
                {"job_id": 2, "job_reference": "job-2"},
            ],
        },
        {
            "counting_order": 4,
            "jobs": [
                {"job_id": 6, "job_reference": "job-6"},
                {"job_id": 4, "job_reference": "job-4"},
            ],
        },
    ]
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.service = JobDiscrepancyService()

    def get(
        self,
        request,
        inventory_id: int,
        warehouse_id: int,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """
        Retourne les jobs avec écarts non résolus groupés par comptage.
        """
        try:
            data: List[dict] = (
                self.service.get_jobs_with_unresolved_discrepancies_grouped_by_counting(
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id,
                )
            )
            serializer = CountingJobsDiscrepancySerializer(data, many=True)
            return success_response(
                message=(
                    "Jobs avec écarts non résolus regroupés par comptage "
                    "récupérés avec succès."
                ),
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return error_response(
                message=str(exc),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:  # pragma: no cover - log unexpected errors
            logger.error(
                "Erreur lors de la récupération des jobs avec écarts non "
                "résolus par comptage: %s",
                str(exc),
                exc_info=True,
            )
            return error_response(
                message="Une erreur inattendue est survenue",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


