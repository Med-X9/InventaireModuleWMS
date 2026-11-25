"""
Strategy : calcul du nombre d'écarts par job (page « Suivi des jobs »).

- LegacyJobDiscrepancyStrategy : calcul historique (inchangé), délégué au service.
- EnVracJobDiscrepancyStrategy : inventaire contenant un comptage « en vrac ». Les quantités sont
  agrégées par emplacement ; l'écart du comptage n compare chaque emplacement saisi au comptage
  précédent (n-1). Un emplacement saisi au comptage n mais absent du comptage n-1 compte pour
  un écart (quantité précédente = 0) ; un emplacement pas encore saisi au comptage n est en attente,
  pas un écart.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from apps.inventory.models import Counting


class JobDiscrepancyStrategy(ABC):
    """Calcule les écarts d'un job : global (1er vs 2e) et par comptage à partir du 3e."""

    @abstractmethod
    def compute(self, job, max_counting_order: int) -> Dict[str, Any]:
        """
        Returns:
            {'discrepancy_count': int, 'discrepancy_rate': float,
             'counts': {order: Optional[int]}}  (ordres >= 3)
        """


class LegacyJobDiscrepancyStrategy(JobDiscrepancyStrategy):
    """Calcul existant : lignes communes comparées au 1er comptage."""

    def __init__(self, service):
        self.service = service

    def compute(self, job, max_counting_order: int) -> Dict[str, Any]:
        info = self.service._calculate_discrepancies(job)
        by_order = getattr(job, '_counting_details_by_order', {})
        counts = {
            order: self.service._calculate_discrepancy_count_with_first_counting(by_order, order)
            for order in range(3, max_counting_order + 1)
        }
        return {
            'discrepancy_count': info['discrepancy_count'],
            'discrepancy_rate': info['discrepancy_rate'],
            'counts': counts,
        }


class EnVracJobDiscrepancyStrategy(JobDiscrepancyStrategy):
    """Écart par emplacement : comptage n comparé au comptage n-1."""

    @staticmethod
    def count_between(
        previous: Dict[Any, Any], current: Dict[Any, Any]
    ) -> Optional[int]:
        """Écarts du comptage `current` vs `previous` ; None si `current` est vide."""
        if not current:
            return None
        count = 0
        for key, detail in current.items():
            prev = previous.get(key)
            prev_qty = prev.quantity_inventoried if prev is not None else 0
            if detail.quantity_inventoried != prev_qty:
                count += 1
        return count

    def compute(self, job, max_counting_order: int) -> Dict[str, Any]:
        by_order = getattr(job, '_counting_details_by_order', {})
        second = by_order.get(2, {})
        global_count = self.count_between(by_order.get(1, {}), second) or 0
        rate = round(global_count / len(second) * 100, 2) if second else 0.0
        counts = {
            order: self.count_between(by_order.get(order - 1, {}), by_order.get(order, {}))
            for order in range(3, max_counting_order + 1)
        }
        return {
            'discrepancy_count': global_count,
            'discrepancy_rate': rate,
            'counts': counts,
        }


class JobDiscrepancyDispatcher:
    """Choisit la stratégie : en vrac si l'inventaire a un comptage en vrac, sinon historique."""

    def get_strategy(self, inventory_id: int, service) -> JobDiscrepancyStrategy:
        if Counting.objects.filter(inventory_id=inventory_id, count_mode='en vrac').exists():
            return EnVracJobDiscrepancyStrategy()
        return LegacyJobDiscrepancyStrategy(service)
