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
    def test_delegue_au_service_existant(self):
        service = SimpleNamespace(
            _calculate_discrepancies=lambda job: {'discrepancy_count': 2, 'discrepancy_rate': 10.0},
            _calculate_discrepancy_count_with_first_counting=lambda by_order, order: order,
        )
        job = SimpleNamespace(_counting_details_by_order={})
        result = LegacyJobDiscrepancyStrategy(service).compute(job, 4)
        self.assertEqual(result['discrepancy_count'], 2)
        self.assertEqual(result['counts'], {3: 3, 4: 4})
