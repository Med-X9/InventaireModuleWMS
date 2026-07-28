"""
Stratégie final_result pour inventaires à comptage unique (MAGASIN, TOURNANT).
"""
from typing import List, Optional

from apps.inventory.interfaces.ecart_final_result_strategy_interface import (
    IEcartFinalResultStrategy,
)


class EcartFinalResultSingleCountingStrategy(IEcartFinalResultStrategy):
    """
    Stocke immédiatement final_result = dernière quantité inventoriée.

    Pas de consensus multi-séquences : un seul comptage suffit.
    """

    def resolve_final_result(
        self,
        quantities: List[int],
        current_result: Optional[int],
    ) -> Optional[int]:
        if not quantities:
            return None
        return int(quantities[-1])
