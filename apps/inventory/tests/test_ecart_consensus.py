"""
Tests unitaires pour la règle de consensus partagée (apps.inventory.utils.ecart_consensus).
"""
from django.test import SimpleTestCase

from apps.inventory.utils.ecart_consensus import calculate_ecart_consensus_result


class EcartConsensusTests(SimpleTestCase):
    """Tests de calculate_ecart_consensus_result."""

    def test_less_than_two_quantities_returns_none(self):
        self.assertIsNone(calculate_ecart_consensus_result([10], None))
        self.assertIsNone(calculate_ecart_consensus_result([], None))

    def test_two_identical_returns_quantity(self):
        self.assertEqual(calculate_ecart_consensus_result([10, 10], None), 10)

    def test_two_different_returns_none(self):
        self.assertIsNone(calculate_ecart_consensus_result([10, 12], None))

    def test_third_matches_first_returns_quantity(self):
        self.assertEqual(calculate_ecart_consensus_result([10, 12, 10], None), 10)

    def test_third_different_preserves_current_result(self):
        self.assertEqual(
            calculate_ecart_consensus_result([10, 10, 14], current_result=10),
            10,
        )

    def test_third_different_no_current_returns_none(self):
        self.assertIsNone(calculate_ecart_consensus_result([10, 12, 14], None))

    def test_fourth_matches_previous_returns_quantity(self):
        self.assertEqual(
            calculate_ecart_consensus_result([10, 12, 14, 14], None),
            14,
        )
