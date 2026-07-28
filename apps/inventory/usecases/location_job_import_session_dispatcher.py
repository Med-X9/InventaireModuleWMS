"""
Dispatcher Strategy : sessions import InventoryLocationJob selon inventory_type.
"""
from typing import Dict, Type

from apps.inventory.constants import InventoryType
from apps.inventory.interfaces.location_job_import_session_strategy_interface import (
    ILocationJobImportSessionStrategy,
)
from apps.inventory.usecases.location_job_import_session_general import (
    LocationJobImportSessionGeneralStrategy,
)
from apps.inventory.usecases.location_job_import_session_single import (
    LocationJobImportSessionSingleStrategy,
)


class LocationJobImportSessionDispatcher:
    """
    Sélectionne la stratégie de sessions Excel.

    - MAGASIN / TOURNANT → session_1 seule (session_2 optionnelle)
    - GENERAL (défaut) → session_1 + session_2 (logique historique)
    """

    _single_class: Type[ILocationJobImportSessionStrategy] = (
        LocationJobImportSessionSingleStrategy
    )
    _general_class: Type[ILocationJobImportSessionStrategy] = (
        LocationJobImportSessionGeneralStrategy
    )
    _instances: Dict[str, ILocationJobImportSessionStrategy] = {}

    def get_strategy(self, inventory_type: str) -> ILocationJobImportSessionStrategy:
        if inventory_type in InventoryType.SINGLE_COUNTING:
            key = "single"
            strategy_class = self._single_class
        else:
            key = "general"
            strategy_class = self._general_class

        if key not in self._instances:
            self._instances[key] = strategy_class()
        return self._instances[key]
