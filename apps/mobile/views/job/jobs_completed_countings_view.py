"""
Vue API pour récupérer les jobs dont le 1er et le 2ème comptage sont terminés.
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.inventory.models import Job
from apps.inventory.services.inventory_result_service import InventoryResultService
from apps.inventory.exceptions import InventoryNotFoundError, InventoryValidationError
from apps.mobile.services.job_service import JobService
from apps.mobile.utils import success_response, error_response
from apps.mobile.exceptions import (
    JobFilterValidationException,
    InventoryNotFoundException,
    WarehouseNotFoundException,
)

logger = logging.getLogger(__name__)


class JobsWithBothCountingsTerminatedView(APIView):
    """
    API pour récupérer les jobs dont le 1er et le 2ème comptage sont terminés.

    Les jobs retournés ont au moins un assignment TERMINE pour le comptage d'ordre 1
    et au moins un assignment TERMINE pour le comptage d'ordre 2.

    Paramètres de chemin (obligatoires) :
    - inventory_id : ID d'inventaire (entier > 0)
    - warehouse_id : ID d'entrepôt (entier > 0)

    URL: GET /mobile/api/inventory/<inventory_id>/warehouse/<warehouse_id>/jobs/both-countings-terminated/
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_service = JobService()

    def get(self, request, inventory_id: int, warehouse_id: int):
        """
        GET /mobile/api/inventory/<inventory_id>/warehouse/<warehouse_id>/jobs/both-countings-terminated/
        """
        try:
            result = self.job_service.get_jobs_with_both_countings_terminated(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
            )

            return success_response(
                data=result,
                message="Jobs récupérés avec succès",
            )
        except JobFilterValidationException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='VALIDATION_ERROR',
            )
        except InventoryNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='INVENTORY_NOT_FOUND',
            )
        except WarehouseNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='WAREHOUSE_NOT_FOUND',
            )
        except Exception as e:
            logger.exception(
                "JobsWithBothCountingsTerminatedView: erreur inattendue %s", e
            )
            return error_response(
                message="Une erreur inattendue s'est produite lors de la récupération des jobs.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type='INTERNAL_ERROR',
            )


class JobResultsView(APIView):
    """
    API pour récupérer les résultats d'inventaire pour un job donné.

    La structure des lignes de résultat est la même que pour
    InventoryResultByWarehouseView, mais sans le champ de statut du job.

    URL: GET /mobile/api/job/<job_id>/results/
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.result_service = InventoryResultService()

    def get(self, request, job_id: int):
        """
        GET /mobile/api/job/<job_id>/results/
        """
        try:
            job = Job.objects.select_related("inventory", "warehouse").get(pk=job_id)
        except Job.DoesNotExist:
            return error_response(
                message=f"Job avec l'ID {job_id} non trouvé.",
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="JOB_NOT_FOUND",
            )

        try:
            results = self.result_service.get_inventory_results_for_warehouse(
                inventory_id=job.inventory_id,
                warehouse_id=job.warehouse_id,
            )
        except InventoryNotFoundError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="INVENTORY_NOT_FOUND",
            )
        except InventoryValidationError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type="VALIDATION_ERROR",
            )
        except Exception as e:
            logger.exception("JobResultsView: erreur inattendue %s", e)
            return error_response(
                message=(
                    "Une erreur inattendue s'est produite lors de la "
                    "récupération des résultats du job."
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type="INTERNAL_ERROR",
            )

        # Filtrer uniquement les lignes correspondant à ce job
        job_results = []
        for row in results:
            if row.get("job_id") == job.id:
                cleaned = dict(row)
                # Supprimer le champ de statut du job pour la réponse mobile
                cleaned.pop("job_status", None)
                job_results.append(cleaned)

        return success_response(
            data=job_results,
            message="Résultats du job récupérés avec succès",
        )
