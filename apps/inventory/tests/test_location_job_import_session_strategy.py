"""
Tests Strategy sessions import InventoryLocationJob selon inventory_type.
"""
from django.test import SimpleTestCase

from apps.inventory.constants import InventoryType
from apps.inventory.usecases.location_job_import_session_dispatcher import (
    LocationJobImportSessionDispatcher,
)
from apps.inventory.usecases.location_job_import_session_general import (
    LocationJobImportSessionGeneralStrategy,
)
from apps.inventory.usecases.location_job_import_session_single import (
    LocationJobImportSessionSingleStrategy,
)


class LocationJobImportSessionStrategyTests(SimpleTestCase):
    def setUp(self) -> None:
        self.dispatcher = LocationJobImportSessionDispatcher()

    def test_general_requires_session_2_column(self):
        strategy = self.dispatcher.get_strategy(InventoryType.GENERAL)
        self.assertIsInstance(strategy, LocationJobImportSessionGeneralStrategy)
        self.assertTrue(strategy.session_2_required())
        self.assertIn("session_2", strategy.required_columns())

    def test_magasin_session_2_optional(self):
        strategy = self.dispatcher.get_strategy(InventoryType.MAGASIN)
        self.assertIsInstance(strategy, LocationJobImportSessionSingleStrategy)
        self.assertFalse(strategy.session_2_required())
        self.assertNotIn("session_2", strategy.required_columns())
        self.assertIn("session_1", strategy.required_columns())

    def test_tournant_same_as_magasin(self):
        strategy = self.dispatcher.get_strategy(InventoryType.TOURNANT)
        self.assertFalse(strategy.session_2_required())
        self.assertEqual(strategy.strategy_key(), "single_session")

    def test_general_cross_rules_same_team(self):
        strategy = LocationJobImportSessionGeneralStrategy()
        data = [
            {
                "job": "JOB-0001",
                "is_active": True,
                "session_1": "equipe-1001",
                "session_2": "equipe-2002",
                "row_number": 2,
            }
        ]
        errors = strategy.validate_cross_job_rules(data)
        self.assertTrue(errors)

    def test_single_cross_rules_only_session_1(self):
        strategy = LocationJobImportSessionSingleStrategy()
        data = [
            {
                "job": "JOB-0001",
                "is_active": True,
                "session_1": "equipe-1001",
                "session_2": None,
                "row_number": 2,
            },
            {
                "job": "JOB-0001",
                "is_active": True,
                "session_1": "equipe-1001",
                "session_2": None,
                "row_number": 3,
            },
        ]
        self.assertEqual(strategy.validate_cross_job_rules(data), [])
