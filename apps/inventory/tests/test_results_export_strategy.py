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


class BuildFlatTableTests(TestCase):
    """Tableau d'agrégation : une ligne par combinaison emplacement × article."""

    def setUp(self):
        from django.utils import timezone

        from apps.inventory.models import CountingDetail, Job
        from apps.masterdata.models import (
            Location, LocationType, SousZone, Warehouse, Zone, ZoneType,
        )

        account = Account.objects.create(reference='ACC-F', account_name='A', account_statuts='ACTIVE')
        family = Family.objects.create(
            reference='F-F', family_name='Famille F', compte=account, family_status='ACTIVE'
        )
        self.product = Product.objects.create(
            reference='PF1', Internal_Product_Code='CODE1', Short_Description='Produit F1',
            Product_Family=family,
        )
        warehouse = Warehouse.objects.create(reference='WH-F', warehouse_name='WH')
        zone_type = ZoneType.objects.create(reference='ZT-F', type_name='T', status='ACTIVE')
        zone = Zone.objects.create(reference='Z-F', zone_name='Z', zone_type=zone_type, warehouse=warehouse)
        sous_zone = SousZone.objects.create(reference='SZ-F', sous_zone_name='SZ', zone=zone)
        location_type = LocationType.objects.create(reference='LT-F', name='LT')
        self.location = Location.objects.create(
            reference='LOC-F', location_reference='LOC-F-REF', location_type=location_type,
            sous_zone=sous_zone,
        )
        self.warehouse = warehouse
        self.inventory = Inventory.objects.create(
            reference='INV-F', label='F', date=timezone.now(), status='EN PREPARATION',
            inventory_type='MAGASIN',
        )
        c1 = Counting.objects.create(reference='C-F1', inventory=self.inventory, order=1, count_mode='en vrac')
        c2 = Counting.objects.create(reference='C-F2', inventory=self.inventory, order=2, count_mode='en vrac')
        job = Job.objects.create(reference='JOB-F', inventory=self.inventory, warehouse=warehouse)
        CountingDetail.objects.create(
            reference='CD-F1', quantity_inventoried=4, product=self.product,
            location=self.location, counting=c1, job=job,
        )
        CountingDetail.objects.create(
            reference='CD-F2', quantity_inventoried=6, product=self.product,
            location=self.location, counting=c2, job=job,
        )

    def test_une_ligne_par_emplacement_et_article_avec_les_memes_colonnes(self):
        from apps.inventory.usecases.results_export_strategy import build_flat_table

        columns, rows = build_flat_table(
            self.inventory, self.warehouse.id, {(self.product.id, self.location.id): 5}
        )

        for expected in ['Référence Job', 'Statut Job', 'Emplacement', 'Code Barre', 'Code Interne',
                         'BarCode', 'Désignation', 'Famille', '1er Comptage', 'Statut Comptage 1',
                         '2e Comptage', 'Écart Comptage 1-2', 'Quantité Retenue', 'Résultat Final', 'Résolu']:
            self.assertIn(expected, columns)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['Emplacement'], 'LOC-F-REF')
        self.assertEqual(row['Code Interne'], 'CODE1')
        self.assertEqual(row['1er Comptage'], 4)
        self.assertEqual(row['2e Comptage'], 6)
        self.assertEqual(row['Écart Comptage 1-2'], 2)
        self.assertEqual(row['Quantité Retenue'], 5)
