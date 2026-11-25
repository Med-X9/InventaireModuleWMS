"""Strategy d'export des résultats : feuille « Matrice » pour l'en vrac, export inchangé sinon."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from apps.inventory.models import Counting, Inventory
from apps.inventory.usecases.results_export_strategy import (
    EnVracMatrixStrategy,
    MagasinLocationMatrixStrategy,
    NoExtraSheetsStrategy,
    ResultsExportDispatcher,
    build_matrix_rows,
)
from apps.masterdata.models import Account, Family, Product

LAYOUT = 'apps.inventory.usecases.results_export_strategy.uses_location_ecart'


class DispatcherSimpleTests(SimpleTestCase):
    def test_inventaire_absent_export_inchange(self):
        self.assertIsInstance(ResultsExportDispatcher().get_strategy(None), NoExtraSheetsStrategy)

    def test_magasin_multi_comptages_utilise_la_matrice_par_emplacement(self):
        with patch(LAYOUT, return_value=True):
            strategy = ResultsExportDispatcher().get_strategy(MagicMock(id=1))
        self.assertIsInstance(strategy, MagasinLocationMatrixStrategy)

    def test_aucune_feuille_supplementaire_sans_strategie(self):
        self.assertEqual(NoExtraSheetsStrategy().extra_sheets(MagicMock(), 1), [])


class DispatcherDbTests(TestCase):
    def _inventory(self, inventory_type, count_mode):
        inventory = Inventory.objects.create(
            reference=f'INV-{inventory_type}-{count_mode}',
            label='x',
            date='2026-01-01T00:00:00Z',
            status='EN PREPARATION',
            inventory_type=inventory_type,
        )
        Counting.objects.create(
            reference=f'CNT-{inventory.id}', inventory=inventory, order=1, count_mode=count_mode
        )
        return inventory

    def test_general_par_article_export_inchange(self):
        inventory = self._inventory('GENERAL', 'par article')
        self.assertIsInstance(ResultsExportDispatcher().get_strategy(inventory), NoExtraSheetsStrategy)

    def test_en_vrac_mono_comptage_utilise_la_matrice_en_vrac(self):
        inventory = self._inventory('MAGASIN', 'en vrac')
        self.assertIsInstance(ResultsExportDispatcher().get_strategy(inventory), EnVracMatrixStrategy)


class BuildMatrixTests(TestCase):
    def setUp(self):
        account = Account.objects.create(reference='ACC-M', account_name='A', account_statuts='ACTIVE')
        family = Family.objects.create(
            reference='F-M', family_name='Famille M', compte=account, family_status='ACTIVE'
        )
        self.p1 = Product.objects.create(
            reference='P1', Internal_Product_Code='AAA', Short_Description='Produit A', Product_Family=family
        )
        self.p2 = Product.objects.create(
            reference='P2', Internal_Product_Code='BBB', Barcode='123', Short_Description='Produit B',
            Product_Family=family,
        )

    def test_matrice_articles_en_lignes_emplacements_en_colonnes(self):
        quantities = {(self.p1.id, 10): 3, (self.p1.id, 11): 2, (self.p2.id, 11): 5}
        columns, rows = build_matrix_rows(quantities, {10: 'LOC-A', 11: 'LOC-B'})

        self.assertEqual(
            columns,
            ['Code Barre', 'Code Interne', 'BarCode', 'Désignation', 'Famille',
             'LOC-A', 'LOC-B', 'Total', 'Nb emplacements'],
        )
        by_code = {r['Code Interne']: r for r in rows}
        self.assertEqual(by_code['AAA']['LOC-A'], 3)
        self.assertEqual(by_code['AAA']['LOC-B'], 2)
        self.assertEqual(by_code['AAA']['Total'], 5)
        self.assertEqual(by_code['AAA']['Nb emplacements'], 2)
        self.assertEqual(by_code['BBB']['LOC-A'], '')
        self.assertEqual(by_code['BBB']['Total'], 5)
        self.assertEqual(by_code['BBB']['Code Barre'], '123')
        self.assertEqual(by_code['BBB']['Famille'], 'Famille M')

    def test_libelles_emplacement_en_double_restent_uniques(self):
        columns, _ = build_matrix_rows({(self.p1.id, 1): 1, (self.p1.id, 2): 1}, {1: 'DUP', 2: 'DUP'})
        self.assertEqual(columns[5:7], ['DUP', 'DUP (2)'])
