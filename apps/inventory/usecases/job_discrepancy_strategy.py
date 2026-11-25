"""
Strategy : calcul du nombre d'écarts par job (page « Suivi des jobs »).

- LegacyJobDiscrepancyStrategy (GENERAL, TOURNANT…) : écart par ARTICLE + EMPLACEMENT.
  Chaque comptage n est comparé au comptage précédent (2e vs 1er, 3e vs 2e, 4e vs 3e, …).
- EnVracJobDiscrepancyStrategy : inventaire contenant un comptage « en vrac ». Les quantités sont
  agrégées par emplacement ; l'écart du comptage n compare chaque emplacement saisi au comptage
  précédent (n-1). Un emplacement saisi au comptage n mais absent du comptage n-1 compte pour
  un écart (quantité précédente = 0) ; un emplacement pas encore saisi au comptage n est en attente,
  pas un écart.
"""
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, Iterable, Optional

from django.db.models import Sum

from apps.inventory.models import CountingDetail, Inventory
from apps.inventory.utils.counting_layout import uses_location_ecart


class JobDiscrepancyStrategy(ABC):
    """Calcule les écarts d'un job : global (1er vs 2e) et par comptage à partir du 3e."""

    def prepare(self, job_ids: Iterable[int]) -> None:
        """Précharge les données en une fois pour tous les jobs (optionnel)."""

    @abstractmethod
    def compute(self, job, max_counting_order: int) -> Dict[str, Any]:
        """
        Returns:
            {'discrepancy_count': int, 'discrepancy_rate': float,
             'counts': {order: Optional[int]}}  (ordres >= 3)
        """


class LegacyJobDiscrepancyStrategy(JobDiscrepancyStrategy):
    """
    Écart par article + emplacement, chaque comptage comparé au précédent.

    - 2e vs 1er : toutes les lignes (article, emplacement) des deux comptages ; une ligne absente
      d'un comptage vaut 0.
    - 3e vs 2e, 4e vs 3e, … : lignes saisies au comptage n comparées au comptage n-1
      (absente du comptage n-1 = 0). Comptage n pas encore saisi : None.
    """

    def __init__(self, service=None):
        self.service = service
        self._lines: Dict[int, Dict[int, Dict[tuple, int]]] = {}

    def prepare(self, job_ids: Iterable[int]) -> None:
        rows = (
            CountingDetail.objects.filter(job_id__in=list(job_ids))
            .values('job_id', 'counting__order', 'location_id', 'product_id')
            .annotate(quantity=Sum('quantity_inventoried'))
        )
        lines: Dict[int, Dict[int, Dict[tuple, int]]] = defaultdict(lambda: defaultdict(dict))
        for r in rows:
            lines[r['job_id']][r['counting__order']][(r['location_id'], r['product_id'])] = r['quantity'] or 0
        self._lines = lines

    @staticmethod
    def count_between(previous: Dict[tuple, int], current: Dict[tuple, int]) -> Optional[int]:
        """Lignes du comptage `current` dont la quantité diffère du comptage précédent."""
        if not current:
            return None
        return sum(1 for key, qty in current.items() if qty != previous.get(key, 0))

    def compute(self, job, max_counting_order: int) -> Dict[str, Any]:
        by_order = self._lines.get(job.id, {})
        first, second = by_order.get(1, {}), by_order.get(2, {})
        if first and second:
            keys = set(first) | set(second)
            global_count = sum(1 for k in keys if first.get(k, 0) != second.get(k, 0))
            rate = round(global_count / len(keys) * 100, 2)
        else:
            global_count, rate = 0, 0.0
        counts = {
            order: self.count_between(by_order.get(order - 1, {}), by_order.get(order, {}))
            for order in range(3, max_counting_order + 1)
        }
        return {'discrepancy_count': global_count, 'discrepancy_rate': rate, 'counts': counts}


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
    """Choisit la stratégie : en vrac (MAGASIN à plusieurs comptages) ou article + emplacement."""

    def get_strategy(self, inventory_id: int, service=None) -> JobDiscrepancyStrategy:
        inventory = Inventory.objects.filter(id=inventory_id).first()
        if uses_location_ecart(inventory):
            return EnVracJobDiscrepancyStrategy()
        return LegacyJobDiscrepancyStrategy(service)
