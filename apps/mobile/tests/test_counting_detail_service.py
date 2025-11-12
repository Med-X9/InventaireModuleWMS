from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.mobile.services.counting_detail_service import CountingDetailService


class CountingDetailServiceConsensusTests(SimpleTestCase):
    def setUp(self) -> None:
        self.service = CountingDetailService()

    def test_consensus_first_two_identical(self):
        sequences = [
            SimpleNamespace(quantity=10),
            SimpleNamespace(quantity=10),
        ]

        result = self.service._calculate_consensus_result(sequences, current_result=None)

        self.assertEqual(result, 10)

    def test_consensus_third_matches_first(self):
        sequences = [
            SimpleNamespace(quantity=10),
            SimpleNamespace(quantity=12),
            SimpleNamespace(quantity=10),
        ]

        result = self.service._calculate_consensus_result(sequences, current_result=None)

        self.assertEqual(result, 10)

    def test_consensus_fourth_matches_third(self):
        sequences = [
            SimpleNamespace(quantity=10),
            SimpleNamespace(quantity=12),
            SimpleNamespace(quantity=14),
            SimpleNamespace(quantity=14),
        ]

        result = self.service._calculate_consensus_result(sequences, current_result=None)

        self.assertEqual(result, 14)

    def test_consensus_keeps_existing_valid_result(self):
        sequences = [
            SimpleNamespace(quantity=10),
            SimpleNamespace(quantity=10),
            SimpleNamespace(quantity=12),
        ]

        result = self.service._calculate_consensus_result(sequences, current_result=10)

        self.assertEqual(result, 10)

    def test_consensus_none_when_no_match(self):
        sequences = [
            SimpleNamespace(quantity=10),
            SimpleNamespace(quantity=12),
            SimpleNamespace(quantity=14),
        ]

        result = self.service._calculate_consensus_result(sequences, current_result=None)

        self.assertIsNone(result)
