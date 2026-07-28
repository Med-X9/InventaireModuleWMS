"""
Tests Strategy final_result selon inventory_type.
"""
from django.test import SimpleTestCase

from apps.inventory.constants import InventoryType
from apps.inventory.usecases.ecart_final_result_dispatcher import (
    EcartFinalResultDispatcher,
)
from apps.inventory.usecases.ecart_final_result_general import (
    EcartFinalResultGeneralStrategy,
)
from apps.inventory.usecases.ecart_final_result_single import (
    EcartFinalResultSingleCountingStrategy,
)


class EcartFinalResultStrategyTests(SimpleTestCase):
    """Règles MAGASIN/TOURNANT vs GENERAL sans DB."""

    def setUp(self) -> None:
        self.dispatcher = EcartFinalResultDispatcher()

    def test_dispatcher_single_for_magasin_tournant(self):
        for inv_type in InventoryType.SINGLE_COUNTING:
            strategy = self.dispatcher.get_strategy(inv_type)
            self.assertIsInstance(strategy, EcartFinalResultSingleCountingStrategy)

    def test_dispatcher_general_default(self):
        strategy = self.dispatcher.get_strategy(InventoryType.GENERAL)
        self.assertIsInstance(strategy, EcartFinalResultGeneralStrategy)

    def test_single_sets_final_result_on_first_count(self):
        strategy = EcartFinalResultSingleCountingStrategy()
        self.assertEqual(strategy.resolve_final_result([7], None), 7)
        self.assertEqual(strategy.resolve_final_result([7, 9], None), 9)

    def test_general_needs_two_counts(self):
        strategy = EcartFinalResultGeneralStrategy()
        self.assertIsNone(strategy.resolve_final_result([7], None))
        self.assertEqual(strategy.resolve_final_result([7, 7], None), 7)
        self.assertIsNone(strategy.resolve_final_result([7, 9], None))

    def test_dispatcher_resolve_shortcut(self):
        self.assertEqual(
            self.dispatcher.resolve_final_result(InventoryType.MAGASIN, [12], None),
            12,
        )
        self.assertIsNone(
            self.dispatcher.resolve_final_result(InventoryType.GENERAL, [12], None),
        )
