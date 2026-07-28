"""
Dispatcher Strategy : choix de la règle final_result selon inventory_type.
"""
from typing import Dict, Type

from apps.inventory.constants import InventoryType
from apps.inventory.interfaces.ecart_final_result_strategy_interface import (
    IEcartFinalResultStrategy,
)
from apps.inventory.usecases.ecart_final_result_general import (
    EcartFinalResultGeneralStrategy,
)
from apps.inventory.usecases.ecart_final_result_single import (
    EcartFinalResultSingleCountingStrategy,
)


class EcartFinalResultDispatcher:
    """
    Sélectionne la stratégie de final_result (Open/Closed).

    - MAGASIN / TOURNANT → stockage direct de la quantité comptée
    - GENERAL (défaut) → consensus multi-comptages
    """

    _single_strategy_class: Type[IEcartFinalResultStrategy] = (
        EcartFinalResultSingleCountingStrategy
    )
    _general_strategy_class: Type[IEcartFinalResultStrategy] = (
        EcartFinalResultGeneralStrategy
    )

    # Cache d'instances (stateless)
    _instances: Dict[str, IEcartFinalResultStrategy] = {}

    def get_strategy(self, inventory_type: str) -> IEcartFinalResultStrategy:
        """
        Retourne la stratégie adaptée au type d'inventaire.

        Args:
            inventory_type: Inventory.inventory_type (GENERAL, MAGASIN, TOURNANT).
        """
        if inventory_type in InventoryType.SINGLE_COUNTING:
            key = "single"
            strategy_class = self._single_strategy_class
        else:
            key = "general"
            strategy_class = self._general_strategy_class

        if key not in self._instances:
            self._instances[key] = strategy_class()
        return self._instances[key]

    def resolve_final_result(
        self,
        inventory_type: str,
        quantities: list,
        current_result=None,
    ):
        """Raccourci : sélection + résolution."""
        strategy = self.get_strategy(inventory_type)
        return strategy.resolve_final_result(quantities, current_result)
