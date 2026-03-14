"""
Service pour la duplication d'inventaires.
"""
from typing import Dict, Any, Optional
import logging

from ..usecases.inventory_duplication import InventoryDuplicationUseCase
from ..exceptions import InventoryValidationError, InventoryNotFoundError


logger = logging.getLogger(__name__)


class InventoryDuplicationService:
    """
    Service orchestrant la duplication d'inventaires via le use case dédié.
    """

    def __init__(self, use_case: Optional[InventoryDuplicationUseCase] = None) -> None:
        self.use_case = use_case or InventoryDuplicationUseCase()

    def duplicate_inventory(self, source_inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Duplique un inventaire existant et renvoie le résultat.
        """
        try:
            return self.use_case.duplicate(source_inventory_id, data)
        except (InventoryNotFoundError, InventoryValidationError):
            # Laisser les exceptions métier remonter pour la vue
            raise
        except Exception as exc:
            logger.error(
                "Erreur inattendue dans InventoryDuplicationService lors de la duplication %s: %s",
                source_inventory_id,
                exc,
                exc_info=True
            )
            raise InventoryValidationError(
                "Une erreur est survenue lors de la duplication de l'inventaire."
            ) from exc


