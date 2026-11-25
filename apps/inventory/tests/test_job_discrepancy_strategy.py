"""Strategy du nombre d'écarts par job : historique inchangé, en vrac par emplacement."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.inventory.usecases.job_discrepancy_strategy import (
    EnVracJobDiscrepancyStrategy,
    LegacyJobDiscrepancyStrategy,
)


def _detail(qty):
    return SimpleNamespace(quantity_inventoried=qty)


class EnVracStrategyTests(SimpleTestCase):
    def _job(self, by_order):
        return SimpleNamespace(_counting_details_by_order=by_order)

    def test_ecart_par_emplacement_compare_au_comptage_precedent(self):
        job = self._job({
            1: {(1, 9): _detail(5), (2, 9): _detail(3)},
            2: {(1, 9): _detail(5), (2, 9): _detail(4)},
            3: {(2, 9): _detail(4)},
        })
        result = EnVracJobDiscrepancyStrategy().compute(job, 3)
        self.assertEqual(result['discrepancy_count'], 1)
        self.assertEqual(result['discrepancy_rate'], 50.0)
        self.assertEqual(result['counts'], {3: 0})

    def test_emplacement_saisi_seulement_au_comptage_suivant_est_un_ecart(self):
        job = self._job({1: {(1, 9): _detail(5)}, 2: {(1, 9): _detail(5), (2, 9): _detail(2)}})
        self.assertEqual(EnVracJobDiscrepancyStrategy().compute(job, 2)['discrepancy_count'], 1)

    def test_emplacement_pas_encore_saisi_nest_pas_un_ecart(self):
        job = self._job({1: {(1, 9): _detail(5), (2, 9): _detail(1)}, 2: {(1, 9): _detail(5)}})
        self.assertEqual(EnVracJobDiscrepancyStrategy().compute(job, 2)['discrepancy_count'], 0)

    def test_comptage_vide_donne_none(self):
        job = self._job({1: {(1, 9): _detail(5)}})
        self.assertEqual(EnVracJobDiscrepancyStrategy().compute(job, 3)['counts'], {3: None})


class LegacyStrategyTests(SimpleTestCase):
    """GENERAL : écart par article + emplacement, comptage n comparé au comptage n-1."""

    def _strategy(self, lines):
        strategy = LegacyJobDiscrepancyStrategy()
        strategy._lines = {1: lines}
        return strategy

    def test_2e_vs_1er_par_article_et_emplacement(self):
        # Même emplacement (10), deux articles : un seul article diffère
        strategy = self._strategy({
            1: {(10, 100): 5, (10, 200): 3},
            2: {(10, 100): 5, (10, 200): 4},
        })
        result = strategy.compute(SimpleNamespace(id=1), 2)
        self.assertEqual(result['discrepancy_count'], 1)
        self.assertEqual(result['discrepancy_rate'], 50.0)

    def test_article_absent_dun_comptage_vaut_zero(self):
        strategy = self._strategy({1: {(10, 100): 5}, 2: {(10, 100): 5, (10, 200): 2}})
        self.assertEqual(strategy.compute(SimpleNamespace(id=1), 2)['discrepancy_count'], 1)

    def test_3e_compare_au_2e_et_4e_au_3e(self):
        strategy = self._strategy({
            1: {(10, 100): 5, (10, 200): 3},
            2: {(10, 100): 6, (10, 200): 4},
            3: {(10, 100): 6, (10, 200): 3},
            4: {(10, 200): 3},
        })
        counts = strategy.compute(SimpleNamespace(id=1), 4)['counts']
        self.assertEqual(counts, {3: 1, 4: 0})

    def test_comptage_non_saisi_donne_none(self):
        strategy = self._strategy({1: {(10, 100): 5}, 2: {(10, 100): 6}})
        self.assertEqual(strategy.compute(SimpleNamespace(id=1), 3)['counts'], {3: None})
