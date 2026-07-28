"""
Use case : final_result EcartComptage selon inventory_type (Strategy).

Point d'entrée métier pour POST /mobile/api/job/<id>/counting-detail/.
"""
from __future__ import annotations

from typing import List, Optional

from apps.inventory.constants import InventoryType
from apps.inventory.models import EcartComptage, Job
from apps.inventory.usecases.ecart_final_result_dispatcher import (
    EcartFinalResultDispatcher,
)


class CountingDetailEcartFinalResultUseCase:
    """
    Applique la bonne stratégie de final_result après insertion CountingDetail.

    - MAGASIN / TOURNANT : quantité comptée immédiate (mono-comptage)
    - GENERAL : consensus à partir de 2 séquences minimum
    """

    STRATEGY_SINGLE = "single_counting"
    STRATEGY_GENERAL = "general_consensus"

    def __init__(
        self,
        dispatcher: Optional[EcartFinalResultDispatcher] = None,
    ) -> None:
        self.dispatcher = dispatcher or EcartFinalResultDispatcher()

    @classmethod
    def strategy_key_for_type(cls, inventory_type: str) -> str:
        """Identifiant de stratégie exposé à l'API mobile."""
        if inventory_type in InventoryType.SINGLE_COUNTING:
            return cls.STRATEGY_SINGLE
        return cls.STRATEGY_GENERAL

    def get_context_for_job(self, job_id: int) -> dict:
        """
        Contexte inventaire pour un job (type + stratégie).

        Raises:
            Job.DoesNotExist: job introuvable.
        """
        job = Job.objects.select_related("inventory").get(id=job_id)
        inventory_type = job.inventory.inventory_type
        return {
            "inventory_id": job.inventory_id,
            "inventory_type": inventory_type,
            "final_result_strategy": self.strategy_key_for_type(inventory_type),
        }

    def resolve_final_result(
        self,
        inventory_type: str,
        quantities: List[int],
        current_result: Optional[int],
    ) -> Optional[int]:
        """Calcule final_result sans modifier l'écart."""
        return self.dispatcher.resolve_final_result(
            inventory_type,
            quantities,
            current_result,
        )

    def apply_to_ecart(
        self,
        inventory_type: str,
        ecart: EcartComptage,
        quantities: List[int],
    ) -> Optional[int]:
        """
        Calcule et assigne final_result sur l'instance EcartComptage.

        Returns:
            Valeur de final_result appliquée (peut être None pour GENERAL).
        """
        final_result = self.resolve_final_result(
            inventory_type,
            quantities,
            ecart.final_result,
        )
        ecart.final_result = final_result
        return final_result
