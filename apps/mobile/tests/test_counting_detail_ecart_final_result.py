"""
Tests use case final_result pour API counting-detail mobile.
"""
from django.test import SimpleTestCase

from apps.inventory.constants import InventoryType
from apps.mobile.usecases.counting_detail_ecart_final_result import (
    CountingDetailEcartFinalResultUseCase,
)


class CountingDetailEcartFinalResultUseCaseTests(SimpleTestCase):
    """Strategy key + résolution sans DB."""

    def setUp(self) -> None:
        self.use_case = CountingDetailEcartFinalResultUseCase()

    def test_strategy_key_magasin_tournant(self):
        for inv_type in InventoryType.SINGLE_COUNTING:
            self.assertEqual(
                self.use_case.strategy_key_for_type(inv_type),
                CountingDetailEcartFinalResultUseCase.STRATEGY_SINGLE,
            )

    def test_strategy_key_general(self):
        self.assertEqual(
            self.use_case.strategy_key_for_type(InventoryType.GENERAL),
            CountingDetailEcartFinalResultUseCase.STRATEGY_GENERAL,
        )

    def test_resolve_magasin_first_count(self):
        result = self.use_case.resolve_final_result(
            InventoryType.MAGASIN, [15], None
        )
        self.assertEqual(result, 15)

    def test_resolve_general_first_count_none(self):
        result = self.use_case.resolve_final_result(
            InventoryType.GENERAL, [15], None
        )
        self.assertIsNone(result)
