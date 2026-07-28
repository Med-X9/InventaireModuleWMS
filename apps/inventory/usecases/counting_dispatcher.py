"""
Use case pour le dispatcher de comptages (pattern Strategy + Registry).
"""
from typing import Any, Dict, List, Optional, Type

from ..constants import CountMode
from ..exceptions import CountingValidationError
from ..interfaces.counting_strategy_interface import ICountingStrategy
from ..models import Counting, Inventory
from .counting_by_article import CountingByArticle
from .counting_by_in_bulk import CountingByInBulk
from .counting_by_stockimage import CountingByStockimage


class CountingDispatcher:
    """
    Dispatcher Strategy pour diriger les comptages vers le bon use case.

    Les stratégies sont enregistrées dans un registre (Open/Closed) :
    ajouter un mode = enregistrer une classe, sans modifier les if/elif.
    """

    _registry: Dict[str, Type[ICountingStrategy]] = {
        CountMode.IN_BULK: CountingByInBulk,
        CountMode.BY_ARTICLE: CountingByArticle,
        CountMode.STOCK_IMAGE: CountingByStockimage,
    }

    def __init__(
        self,
        inventory_getter=None,
        counting_queryset_getter=None,
    ):
        """
        Args:
            inventory_getter: Callable optionnel (inventory_id) -> Inventory.
            counting_queryset_getter: Callable optionnel (inventory) -> QuerySet[Counting].
        """
        self._inventory_getter = inventory_getter or (
            lambda inventory_id: Inventory.objects.get(id=inventory_id)
        )
        self._counting_queryset_getter = counting_queryset_getter or (
            lambda inventory: Counting.objects.filter(inventory=inventory)
        )

    @classmethod
    def register_strategy(
        cls,
        count_mode: str,
        strategy_class: Type[ICountingStrategy],
    ) -> None:
        """
        Enregistre (ou remplace) une stratégie pour un mode de comptage.

        Args:
            count_mode: Identifiant du mode (ex. CountMode.IN_BULK).
            strategy_class: Classe implémentant ICountingStrategy.
        """
        if not issubclass(strategy_class, ICountingStrategy):
            raise TypeError(
                f"{strategy_class!r} doit implémenter ICountingStrategy"
            )
        cls._registry[count_mode] = strategy_class

    @classmethod
    def get_supported_counting_modes(cls) -> List[str]:
        """Retourne la liste des modes de comptage supportés."""
        return list(cls._registry.keys())

    def get_strategy_for_mode(self, count_mode: str) -> ICountingStrategy:
        """
        Instancie la stratégie correspondant au mode.

        Raises:
            CountingValidationError: Si le mode n'est pas enregistré.
        """
        strategy_class = self._registry.get(count_mode)
        if strategy_class is None:
            raise CountingValidationError(
                f"Mode de comptage non supporté: {count_mode}"
            )
        return strategy_class()

    def get_use_case_for_counting(self, counting: Counting) -> ICountingStrategy:
        """
        Retourne la stratégie appropriée selon le mode du comptage.
        """
        return self.get_strategy_for_mode(counting.count_mode)

    def get_use_cases_for_inventory(self, inventory_id: int) -> Dict[str, Any]:
        """
        Récupère tous les use cases nécessaires pour un inventaire.
        """
        try:
            inventory = self._inventory_getter(inventory_id)
        except Inventory.DoesNotExist as exc:
            raise CountingValidationError(
                f"Inventaire avec l'ID {inventory_id} non trouvé"
            ) from exc

        countings = self._counting_queryset_getter(inventory)

        if not countings.exists():
            raise CountingValidationError(
                "Aucun comptage trouvé pour cet inventaire"
            )

        counting_use_cases = {}
        for counting in countings:
            use_case = self.get_use_case_for_counting(counting)
            counting_use_cases[counting.id] = {
                "counting": counting,
                "use_case": use_case,
                "count_mode": counting.count_mode,
            }

        return {
            "inventory": inventory,
            "counting_use_cases": counting_use_cases,
            "total_countings": len(counting_use_cases),
        }

    def validate_counting_mode(self, count_mode: str) -> bool:
        """Valide si un mode de comptage est supporté."""
        return count_mode in self._registry

    def validate_counting_data(self, counting_data: Dict[str, Any]) -> None:
        """
        Valide les données d'un comptage via la stratégie appropriée.
        """
        count_mode = counting_data.get("count_mode")
        strategy = self.get_strategy_for_mode(count_mode)
        strategy.validate_counting_data(counting_data)

    def create_counting(self, counting_data: Dict[str, Any]) -> Counting:
        """
        Crée un comptage via la stratégie correspondant au mode.
        """
        count_mode = counting_data.get("count_mode")
        strategy = self.get_strategy_for_mode(count_mode)
        return strategy.create_counting(counting_data)
