"""
Strategy : consolidation par article (export Excel).

- MAGASIN à plusieurs comptages (écart par emplacement) → MagasinLocationConsolidationStrategy
- Tous les autres (GENERAL, MAGASIN 1 comptage, TOURNANT, …) → GeneralConsolidationStrategy,
  qui délègue à la logique d'origine du repository (inchangée).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from apps.masterdata.models import Product

from ..utils.counting_layout import uses_location_ecart


class ConsolidationStrategy(ABC):
    """Calcule les quantités consolidées par article pour un inventaire et un magasin."""

    @abstractmethod
    def consolidated_rows(
        self, repository, inventory, warehouse_id: int
    ) -> List[Dict[str, Any]]:
        ...


class GeneralConsolidationStrategy(ConsolidationStrategy):
    """Logique par article : Σ(final_result) des écarts par produit, résolus ou non."""

    def consolidated_rows(self, repository, inventory, warehouse_id: int) -> List[Dict[str, Any]]:
        return repository.get_consolidated_data_general(inventory.id, warehouse_id)


class MagasinLocationConsolidationStrategy(ConsolidationStrategy):
    """
    MAGASIN multi-comptages : l'écart est calculé par emplacement. La quantité par article est
    reprise des lignes du comptage « par article » dont le total égale le résultat final
    de l'emplacement. Écarts résolus ou non (sans résultat final : dernier comptage par article).
    """

    def consolidated_rows(self, repository, inventory, warehouse_id: int) -> List[Dict[str, Any]]:
        from ..utils.location_ecart_results import location_ecart_results

        # Sans condition « résolu » : écart non résolu = dernier comptage par article
        location_results = location_ecart_results(
            inventory, warehouse_id=warehouse_id, only_resolved=False
        )
        excluded = Product.objects.filter(
            Internal_Product_Code='111111111111111'
        ).values_list('id', flat=True)
        sums: Dict[int, int] = {}
        for info in location_results.values():
            for product_id, qty in info['product_quantities'].items():
                sums[product_id] = sums.get(product_id, 0) + qty
        return repository._build_consolidated_rows(sums, excluded)


class ConsolidationDispatcher:
    """Sélectionne la stratégie de consolidation (Open/Closed)."""

    def get_strategy(self, inventory) -> ConsolidationStrategy:
        if inventory is not None and uses_location_ecart(inventory):
            return MagasinLocationConsolidationStrategy()
        return GeneralConsolidationStrategy()
