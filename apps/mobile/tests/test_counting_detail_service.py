from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.inventory.utils.ecart_consensus import calculate_ecart_consensus_result


class CountingDetailServiceConsensusTests(SimpleTestCase):
    """Tests de la règle de consensus partagée (ecart_consensus)."""

    def test_consensus_first_two_identical(self):
        quantities = [10, 10]
        result = calculate_ecart_consensus_result(quantities, current_result=None)
        self.assertEqual(result, 10)

    def test_consensus_third_matches_first(self):
        quantities = [10, 12, 10]
        result = calculate_ecart_consensus_result(quantities, current_result=None)
        self.assertEqual(result, 10)

    def test_consensus_fourth_matches_third(self):
        quantities = [10, 12, 14, 14]
        result = calculate_ecart_consensus_result(quantities, current_result=None)
        self.assertEqual(result, 14)

    def test_consensus_keeps_existing_valid_result(self):
        quantities = [10, 10, 12]
        result = calculate_ecart_consensus_result(quantities, current_result=10)
        self.assertEqual(result, 10)

    def test_consensus_none_when_no_match(self):
        quantities = [10, 12, 14]
        result = calculate_ecart_consensus_result(quantities, current_result=None)
        self.assertIsNone(result)
