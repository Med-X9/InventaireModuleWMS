"""Strategy de consolidation : choix de la stratégie et non-régression de la logique par article."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.inventory.usecases.consolidation_strategy import (
    ConsolidationDispatcher,
    GeneralConsolidationStrategy,
    MagasinLocationConsolidationStrategy,
)

LAYOUT = 'apps.inventory.usecases.consolidation_strategy.uses_location_ecart'


class ConsolidationDispatcherTests(SimpleTestCase):
    def test_magasin_multi_comptages_utilise_la_strategie_emplacement(self):
        with patch(LAYOUT, return_value=True):
            strategy = ConsolidationDispatcher().get_strategy(MagicMock())
        self.assertIsInstance(strategy, MagasinLocationConsolidationStrategy)

    def test_autres_inventaires_gardent_la_logique_par_article(self):
        with patch(LAYOUT, return_value=False):
            strategy = ConsolidationDispatcher().get_strategy(MagicMock())
        self.assertIsInstance(strategy, GeneralConsolidationStrategy)

    def test_inventaire_absent_garde_la_logique_par_article(self):
        self.assertIsInstance(ConsolidationDispatcher().get_strategy(None), GeneralConsolidationStrategy)

    def test_strategie_generale_delegue_au_repository_sans_modifier_le_resultat(self):
        repository = MagicMock()
        repository.get_consolidated_data_general.return_value = [{'product_id': 1, 'total_quantity': 7}]
        inventory = MagicMock(id=5)
        rows = GeneralConsolidationStrategy().consolidated_rows(repository, inventory, 9)
        repository.get_consolidated_data_general.assert_called_once_with(5, 9)
        self.assertEqual(rows, [{'product_id': 1, 'total_quantity': 7}])
