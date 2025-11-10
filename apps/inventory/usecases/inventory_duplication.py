"""
Use case pour la duplication d'un inventaire.
"""
from typing import Dict, Any, Iterable, List, Optional
import logging

from ..repositories.inventory_repository import InventoryRepository
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from ..models import Counting
from .inventory_management import InventoryManagementUseCase


logger = logging.getLogger(__name__)


class InventoryDuplicationUseCase:
    """
    Use case responsable de la duplication d'un inventaire existant
    en créant un nouvel inventaire avec la même configuration de comptages.
    """

    def __init__(
        self,
        inventory_repository: Optional[InventoryRepository] = None,
        management_use_case: Optional[InventoryManagementUseCase] = None,
    ) -> None:
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.management_use_case = management_use_case or InventoryManagementUseCase(
            inventory_repository=self.inventory_repository
        )

    def duplicate(self, source_inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Duplique l'inventaire source en créant un nouvel inventaire avec les
        mêmes comptages.

        Args:
            source_inventory_id: identifiant de l'inventaire à dupliquer
            data: données générales du nouvel inventaire

        Returns:
            Dict[str, Any]: résultat de l'opération

        Raises:
            InventoryNotFoundError: si l'inventaire source n'existe pas
            InventoryValidationError: si la duplication échoue
        """
        try:
            source_inventory = self.inventory_repository.get_by_id(source_inventory_id)
            source_countings = self.inventory_repository.get_countings_by_inventory_id(source_inventory.id)

            if not source_countings.exists():
                raise InventoryValidationError(
                    "L'inventaire source ne contient aucun comptage à dupliquer."
                )

            countings_payload = self._build_countings_payload(source_countings)
            data_with_countings = dict(data)
            data_with_countings['comptages'] = countings_payload

            logger.info(
                "Duplication de l'inventaire %s vers un nouvel inventaire avec %d comptages",
                source_inventory.reference,
                len(countings_payload),
            )

            return self.management_use_case.create(data_with_countings)

        except (InventoryNotFoundError, InventoryValidationError):
            # Propager les exceptions métier telles quelles
            raise
        except Exception as exc:
            logger.error(
                "Erreur inattendue lors de la duplication de l'inventaire %s: %s",
                source_inventory_id,
                exc,
                exc_info=True
            )
            raise InventoryValidationError(
                "Une erreur est survenue lors de la duplication de l'inventaire."
            ) from exc

    def _build_countings_payload(self, countings: Iterable[Counting]) -> List[Dict[str, Any]]:
        """
        Construit la charge utile des comptages à partir de la configuration source.
        """
        payload: List[Dict[str, Any]] = []
        for counting in countings:
            payload.append({
                'order': counting.order,
                'count_mode': counting.count_mode,
                'unit_scanned': counting.unit_scanned,
                'entry_quantity': counting.entry_quantity,
                'is_variant': counting.is_variant,
                'n_lot': counting.n_lot,
                'n_serie': counting.n_serie,
                'dlc': counting.dlc,
                'show_product': counting.show_product,
                'stock_situation': counting.stock_situation,
                'quantity_show': counting.quantity_show,
            })
        return payload


