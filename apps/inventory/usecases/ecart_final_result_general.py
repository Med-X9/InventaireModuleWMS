"""
Stratégie final_result pour inventaires multi-comptages (GENERAL).
"""
from typing import List, Optional

from apps.inventory.interfaces.ecart_final_result_strategy_interface import (
    IEcartFinalResultStrategy,
)
from apps.inventory.utils.ecart_consensus import calculate_ecart_consensus_result


class EcartFinalResultGeneralStrategy(IEcartFinalResultStrategy):
    """
    Conserve la logique historique : consensus uniquement à partir de 2 comptages.
    """

    def resolve_final_result(
        self,
        quantities: List[int],
        current_result: Optional[int],
    ) -> Optional[int]:
        return calculate_ecart_consensus_result(quantities, current_result)
