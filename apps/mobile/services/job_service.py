"""
Service pour la récupération des jobs dans l'application mobile.
"""
from apps.inventory.models import Inventory
from apps.masterdata.models import Warehouse
from apps.mobile.repositories.job_repository import JobRepository
from apps.mobile.exceptions import (
    JobFilterValidationException,
    InventoryNotFoundException,
    WarehouseNotFoundException,
)


class JobService:
    """Service pour les jobs (contexte mobile)."""

    def __init__(self):
        self.repository = JobRepository()

    def get_jobs_with_both_countings_terminated(
        self,
        inventory_id=None,
        warehouse_id=None,
    ):
        """
        Récupère les jobs dont le 1er et le 2ème comptage sont terminés.

        Valide les paramètres optionnels (inventory_id, warehouse_id) et l'existence
        des ressources associées avant d'appeler le repository.

        Args:
            inventory_id: ID d'inventaire (optionnel). Si fourni, doit être un entier > 0.
            warehouse_id: ID d'entrepôt (optionnel). Si fourni, doit être un entier > 0.

        Returns:
            dict: {
                "jobs": [
                    {
                        "id", "reference", "status",
                        "inventory": {"id", "reference", "label"},
                        "warehouse": {"id", "reference", "warehouse_name"},
                    },
                    ...
                ],
                "count": int
            }

        Raises:
            JobFilterValidationException: Paramètres de filtrage invalides.
            InventoryNotFoundException: inventory_id fourni et inventaire inexistant.
            WarehouseNotFoundException: warehouse_id fourni et entrepôt inexistant.
        """
        self._validate_filter_params(inventory_id, warehouse_id)

        if inventory_id is not None:
            if not Inventory.objects.filter(pk=inventory_id).exists():
                raise InventoryNotFoundException(
                    f"Inventaire avec l'ID {inventory_id} non trouvé."
                )
        if warehouse_id is not None:
            if not Warehouse.objects.filter(pk=warehouse_id).exists():
                raise WarehouseNotFoundException(
                    f"Entrepôt avec l'ID {warehouse_id} non trouvé."
                )

        queryset = self.repository.get_jobs_with_both_countings_terminated(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
        )

        jobs_list = []
        for job in queryset:
            jobs_list.append({
                'id': job.id,
                'reference': job.reference,
                'status': job.status,
            })

        return {
            'jobs': jobs_list,
            'count': len(jobs_list),
        }

    def _validate_filter_params(self, inventory_id, warehouse_id):
        """
        Valide le format des paramètres de filtrage.

        Raises:
            JobFilterValidationException: Si un paramètre est fourni et invalide.
        """
        if inventory_id is not None:
            try:
                vid = int(inventory_id)
                if vid <= 0:
                    raise JobFilterValidationException(
                        "inventory_id doit être un entier strictement positif."
                    )
            except (TypeError, ValueError):
                raise JobFilterValidationException(
                    "inventory_id doit être un entier valide."
                )
        if warehouse_id is not None:
            try:
                wid = int(warehouse_id)
                if wid <= 0:
                    raise JobFilterValidationException(
                        "warehouse_id doit être un entier strictement positif."
                    )
            except (TypeError, ValueError):
                raise JobFilterValidationException(
                    "warehouse_id doit être un entier valide."
                )
