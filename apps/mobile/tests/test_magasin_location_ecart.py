"""
Tests : MAGASIN à 3 comptages (écart par emplacement) et non-régression GENERAL.

1er / 3e comptage : saisie quantité par article (product_id requis)
2e comptage       : saisie quantité par emplacement (sans produit)
"""
from django.test import TestCase
from django.utils import timezone

from apps.inventory.models import (
    Assigment, Counting, CountingDetail, EcartComptage, Inventory, Job, JobDetail,
)
from apps.inventory.usecases.inventory_management import InventoryManagementUseCase
from apps.inventory.repositories.counting_repository import CountingRepository
from apps.inventory.repositories.excel_export_repository import ExcelExportRepository
from apps.inventory.repositories.stock_gap_repository import StockGapRepository
from apps.inventory.utils.counting_layout import counting_count_type, uses_location_ecart
from apps.inventory.utils.location_ecart_results import location_ecart_results
from apps.masterdata.models import (
    Account, Family, Location, LocationType, Product, SousZone, Warehouse, Zone, ZoneType,
)
from apps.mobile.services.assignment_service import AssignmentService
from apps.mobile.services.counting_detail_service import CountingDetailService
from apps.users.models import UserApp


def in_bulk_config(order):
    return {
        'count_mode': 'en vrac', 'order': order,
        'unit_scanned': False, 'entry_quantity': True,
        'n_lot': False, 'n_serie': False, 'dlc': False,
        'show_product': False, 'quantity_show': False,
        'is_variant': False, 'stock_situation': False,
    }


class MagasinLocationEcartTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserApp.objects.create_user(username='pda_test', type='Mobile', password='x')
        account = Account.objects.create(reference='ACC-T', account_name='Compte', account_statuts='ACTIVE')
        cls.warehouse = Warehouse.objects.create(
            reference='WH-T', warehouse_name='Magasin', warehouse_type='MAGASIN', status='ACTIVE')
        zone_type = ZoneType.objects.create(reference='ZT-T', type_name='Zone type', status='ACTIVE')
        zone = Zone.objects.create(
            reference='ZN-T', warehouse=cls.warehouse, zone_name='Zone', zone_type=zone_type, zone_status='ACTIVE')
        sous_zone = SousZone.objects.create(
            reference='SZ-T', sous_zone_name='Sous zone', zone=zone, sous_zone_status='ACTIVE')
        location_type = LocationType.objects.create(reference='LT-T', name='Type')
        cls.location = Location.objects.create(
            reference='LOC-T', location_reference='A-01', sous_zone=sous_zone, location_type=location_type)
        family = Family.objects.create(
            reference='FAM-T', family_name='Famille', compte=account, family_status='ACTIVE')
        cls.p1 = Product.objects.create(
            reference='PRD-1', Internal_Product_Code='P1', Stock_Unit='U', Product_Family=family)
        cls.p2 = Product.objects.create(
            reference='PRD-2', Internal_Product_Code='P2', Stock_Unit='U', Product_Family=family)

    # ------------------------------------------------------------------ helpers
    def _setup_inventory(self, inventory_type='MAGASIN', countings=3, third_counting_started=True):
        self.inventory = Inventory.objects.create(
            label='T', date=timezone.now(), status='EN CONFIGURATION',
            inventory_type=inventory_type, reference=f'INV-{inventory_type}')
        if inventory_type == 'MAGASIN':
            InventoryManagementUseCase().configure_magasin_counting(
                self.inventory.id,
                {'comptages': [in_bulk_config(i) for i in range(1, countings + 1)]},
            )
        else:  # GENERAL : 3 comptages en vrac, saisie quantité
            for order in (1, 2, 3):
                counting = Counting(
                    inventory=self.inventory, order=order, count_mode='en vrac', entry_quantity=True)
                counting.reference = counting.generate_reference(Counting.REFERENCE_PREFIX)
                counting.save()
        self.countings = {c.order: c for c in self.inventory.countings.order_by('order')}
        self.job = Job.objects.create(
            status='EN ATTENTE', warehouse=self.warehouse, inventory=self.inventory, reference='JOB-T')
        self.assignments = {}
        for order, counting in self.countings.items():
            if order >= 3 and not third_counting_started:
                continue  # le 3e comptage n'existe sur le job qu'à son lancement
            jd = JobDetail(location=self.location, job=self.job, counting=counting, status='EN ATTENTE')
            jd.reference = jd.generate_reference(JobDetail.REFERENCE_PREFIX)
            jd.save()
            asg = Assigment(job=self.job, counting=counting, session=self.user, status='ENTAME')
            asg.reference = asg.generate_reference(Assigment.REFERENCE_PREFIX)
            asg.save()
            self.assignments[order] = asg

    def _post(self, order, lines):
        """lines : liste de (product | None, quantité)"""
        data = [
            dict(
                counting_id=self.countings[order].id,
                location_id=self.location.id,
                assignment_id=self.assignments[order].id,
                quantity_inventoried=qty,
                **({'product_id': product.id} if product else {}),
            )
            for product, qty in lines
        ]
        return CountingDetailService().create_counting_details_batch(data, self.job.id)

    def _ecart(self):
        return EcartComptage.objects.get(inventory=self.inventory)

    def _sequences(self):
        return list(
            self._ecart().counting_sequences.order_by('sequence_number')
            .values_list('sequence_number', 'quantity', 'counting_detail__counting__order')
        )

    # ------------------------------------------------------------------ tests
    def test_configuration_creates_three_in_bulk_countings(self):
        self._setup_inventory()
        self.assertEqual(sorted(self.countings), [1, 2, 3])
        self.assertTrue(uses_location_ecart(self.inventory))
        self.assertEqual(
            [counting_count_type(self.countings[i]) for i in (1, 2, 3)],
            ['QTE_ARTICLE', 'QTE_EMPLACEMENT', 'QTE_ARTICLE'],
        )

    def test_equal_totals_resolve_final_result(self):
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 7)])
        self.assertEqual(self._sequences(), [(1, 7, 1), (2, 7, 2)])
        self.assertEqual(self._ecart().final_result, 7)
        self.assertEqual(EcartComptage.objects.filter(inventory=self.inventory).count(), 1)

    def test_difference_waits_for_third_counting(self):
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 9)])
        self.assertIsNone(self._ecart().final_result)
        self._post(3, [(self.p1, 5), (self.p2, 4)])
        self.assertEqual(self._sequences(), [(1, 7, 1), (2, 9, 2), (3, 9, 3)])
        self.assertEqual(self._ecart().final_result, 9)

    def test_third_counting_different_from_both_stays_unresolved(self):
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 9)])
        self._post(3, [(self.p1, 4), (self.p2, 4)])
        self.assertIsNone(self._ecart().final_result)

    def test_resend_updates_sequence_without_duplicate(self):
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(1, [(self.p1, 13), (self.p2, 4)])
        self.assertEqual(self._sequences(), [(1, 17, 1)])
        self.assertEqual(CountingDetail.objects.filter(counting=self.countings[1]).count(), 2)

    def test_quantity_by_article_requires_product(self):
        self._setup_inventory()
        result = self._post(1, [(None, 5)])
        self.assertTrue(result.get('errors'))
        self.assertFalse(CountingDetail.objects.filter(counting=self.countings[1]).exists())

    def test_quantity_by_location_accepts_missing_product(self):
        self._setup_inventory()
        result = self._post(2, [(None, 7)])
        self.assertFalse(result.get('errors'))
        self.assertEqual(self._sequences(), [(1, 7, 2)])

    def test_close_does_not_create_zero_lines_between_countings(self):
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 7)])
        for asg in self.assignments.values():
            asg.status = 'TERMINE'
            asg.save()
        before = CountingDetail.objects.count()
        result = AssignmentService()._synchronize_counting_details_if_needed(
            self.job, self.assignments[2])
        self.assertFalse(result['synchronized'])
        self.assertEqual(CountingDetail.objects.count(), before)

    # ------------------------------------------------- résultat final par article
    def test_final_quantities_by_article_from_first_matching_counting(self):
        """Totaux égaux (7 = 7) : quantités par article = lignes du 1er comptage."""
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 7)])
        info = location_ecart_results(self.inventory)[self.location.id]
        self.assertEqual(info['chosen_counting_id'], self.countings[1].id)
        self.assertEqual(info['product_quantities'], {self.p1.id: 3, self.p2.id: 4})

    def test_final_quantities_by_article_from_third_counting(self):
        """Différence puis 3e = 2e : quantités par article = lignes du 3e comptage."""
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 9)])
        self._post(3, [(self.p1, 5), (self.p2, 4)])
        info = location_ecart_results(self.inventory)[self.location.id]
        self.assertEqual(info['chosen_counting_id'], self.countings[3].id)
        self.assertEqual(info['product_quantities'], {self.p1.id: 5, self.p2.id: 4})
        self.assertTrue(info['matches_final_result'])

    def test_stock_gap_uses_final_quantities_by_article(self):
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 9)])
        self._post(3, [(self.p1, 5), (self.p2, 4)])
        quantities = StockGapRepository().get_inventoried_quantities_by_product(
            self.inventory.id, self.warehouse.id)
        self.assertEqual(quantities, {self.p1.id: 5, self.p2.id: 4})

    def test_unresolved_location_is_ignored_until_third_counting(self):
        """Écart 7 ≠ 9 sans 3e comptage : résultat final vide, rien dans l'analyse stock."""
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 9)])
        self.assertIsNone(self._ecart().final_result)
        repository = StockGapRepository()
        self.assertEqual(
            repository.get_inventoried_quantities_by_product(self.inventory.id, self.warehouse.id), {})
        # après le 3e comptage (= 2e), l'emplacement est pris en compte
        self._post(3, [(self.p1, 5), (self.p2, 4)])
        self.assertEqual(
            repository.get_inventoried_quantities_by_product(self.inventory.id, self.warehouse.id),
            {self.p1.id: 5, self.p2.id: 4})

    def test_excel_consolidation_uses_resolved_final_quantities(self):
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 7)])
        EcartComptage.objects.filter(inventory=self.inventory).update(resolved=True)
        rows = ExcelExportRepository().get_consolidated_data_by_inventory_and_warehouse(
            self.inventory.id, self.warehouse.id)
        self.assertEqual({r['product_id']: r['total_quantity'] for r in rows},
                         {self.p1.id: 3, self.p2.id: 4})

    def test_inventory_results_rows_carry_final_result_per_article(self):
        self._setup_inventory()
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 7)])
        rows = CountingRepository().get_inventory_results_by_warehouse(
            self.inventory.id, self.warehouse.id)
        by_key = {(r['counting_order_alias'], r['product_id']): r['final_result_agg'] for r in rows}
        self.assertEqual(by_key[(1, self.p1.id)], 3)
        self.assertEqual(by_key[(1, self.p2.id)], 4)
        self.assertEqual(by_key[(2, None)], 7)

    def test_result_service_rows_emplacement_and_article(self):
        """Page résultat : 1 ligne EMPLACEMENT (totaux 1/2/3 + résultat) + 1 ligne ARTICLE par produit."""
        from apps.inventory.models import Setting
        from apps.inventory.services.inventory_result_service import InventoryResultService
        self._setup_inventory()
        Setting.objects.create(
            reference='SET-T', account=Account.objects.first(), warehouse=self.warehouse,
            inventory=self.inventory)
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 9)])
        self._post(3, [(self.p1, 5), (self.p2, 4)])
        rows = InventoryResultService().get_inventory_results_for_warehouse(
            self.inventory.id, self.warehouse.id, view='all')
        by_type = {}
        for row in rows:
            by_type.setdefault(row['row_type'], []).append(row)
        self.assertEqual(len(by_type['EMPLACEMENT']), 1)
        location_row = by_type['EMPLACEMENT'][0]
        self.assertEqual(
            (location_row['1er comptage'], location_row['2e comptage'], location_row['3e comptage']),
            (7, 9, 9))
        self.assertEqual(location_row['final_result'], 9)
        self.assertIsNotNone(location_row['result_id'])
        article_rows = by_type['ARTICLE']
        self.assertEqual(len(article_rows), 2)
        self.assertEqual(sorted(r['final_result'] for r in article_rows), [4, 5])
        for row in article_rows:
            self.assertIsNone(row['result_id'])  # lecture seule
            self.assertIn('product', row)

    def _results_setup(self):
        from apps.inventory.models import Setting
        self._setup_inventory()
        Setting.objects.create(
            reference='SET-V', account=Account.objects.first(), warehouse=self.warehouse,
            inventory=self.inventory)
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 7)])

    def test_results_default_view_is_by_location_only(self):
        from apps.inventory.services.inventory_result_service import InventoryResultService
        self._results_setup()
        rows = InventoryResultService().get_inventory_results_for_warehouse(
            self.inventory.id, self.warehouse.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['row_type'], 'EMPLACEMENT')
        self.assertEqual((rows[0]['1er comptage'], rows[0]['2e comptage']), (7, 7))

    def test_results_detail_view_lists_articles(self):
        from apps.inventory.services.inventory_result_service import InventoryResultService
        self._results_setup()
        rows = InventoryResultService().get_inventory_results_for_warehouse(
            self.inventory.id, self.warehouse.id, view='detail')
        self.assertEqual({r['row_type'] for r in rows}, {'ARTICLE'})
        self.assertEqual(sorted(r['final_result'] for r in rows), [3, 4])

    def test_results_api_view_parameter(self):
        from rest_framework.test import APIClient
        self._results_setup()
        client = APIClient(HTTP_HOST='localhost')
        client.force_authenticate(user=self.user)
        base = f'/web/api/inventory/{self.inventory.id}/warehouses/{self.warehouse.id}/results/'
        by_location = client.get(base)
        detail = client.get(base + '?view=detail')
        invalid = client.get(base + '?view=nimporte')
        def rows_of(response):
            body = response.data
            for key in ('rows', 'data', 'results'):
                if isinstance(body.get(key), list):
                    return body[key]
            raise AssertionError(f'format de réponse inattendu: {list(body)}')

        self.assertEqual(by_location.status_code, 200)
        self.assertEqual(len(rows_of(by_location)), 1)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(rows_of(detail)), 2)
        self.assertGreaterEqual(invalid.status_code, 400)

    # ------------------------------------------------- lancement du 3e comptage (stratégie)
    def test_dispatcher_selects_strategy_by_inventory(self):
        from apps.inventory.services.counting_launch_service import CountingLaunchService
        from apps.inventory.services.magasin_counting_launch_service import MagasinCountingLaunchService
        from apps.inventory.usecases.counting_launch_dispatcher import CountingLaunchDispatcher
        dispatcher = CountingLaunchDispatcher()
        self._setup_inventory()
        self.assertIsInstance(dispatcher.get_service_for_job(self.job.id), MagasinCountingLaunchService)
        self.assertIs(type(dispatcher.get_service_for_job(0)), CountingLaunchService)

    def test_general_keeps_base_launch_service(self):
        from apps.inventory.services.counting_launch_service import CountingLaunchService
        from apps.inventory.usecases.counting_launch_dispatcher import CountingLaunchDispatcher
        self._setup_inventory(inventory_type='GENERAL')
        service = CountingLaunchDispatcher().get_service_for_job(self.job.id)
        self.assertIs(type(service), CountingLaunchService)

    def test_magasin_launch_third_counting_on_unresolved_locations(self):
        from apps.inventory.models import JobDetail
        from apps.inventory.usecases.counting_launch_dispatcher import CountingLaunchDispatcher
        self._setup_inventory(third_counting_started=False)
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 9)])           # 7 ≠ 9 : résultat final vide
        JobDetail.objects.filter(job=self.job, counting__order__in=(1, 2)).update(status='TERMINE')
        service = CountingLaunchDispatcher().get_service_for_job(self.job.id)
        self.assertEqual(service.get_locations_with_discrepancy_for_job(self.job.id), [self.location.id])
        result = service.launch_counting(self.job.id, self.location.id, self.user.id)
        self.assertEqual(result['counting']['order'], 3)
        self.assertEqual(result['counting']['id'], self.countings[3].id)
        self.assertEqual(result['assignment']['status'], 'TRANSFERT')

    def test_magasin_launch_refused_when_location_already_resolved(self):
        from apps.inventory.exceptions.counting_exceptions import CountingValidationError
        from apps.inventory.models import JobDetail
        from apps.inventory.usecases.counting_launch_dispatcher import CountingLaunchDispatcher
        self._setup_inventory(third_counting_started=False)
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 7)])           # 7 = 7 : résolu
        JobDetail.objects.filter(job=self.job, counting__order__in=(1, 2)).update(status='TERMINE')
        service = CountingLaunchDispatcher().get_service_for_job(self.job.id)
        self.assertEqual(service.get_locations_with_discrepancy_for_job(self.job.id), [])
        with self.assertRaises(CountingValidationError):
            service.launch_counting(self.job.id, self.location.id, self.user.id)

    def test_discrepancies_by_counting_api_announces_third_counting(self):
        """La fenêtre « Lancer comptage » du front lit cette API : elle doit annoncer le comptage 3."""
        from rest_framework.test import APIClient
        from apps.inventory.models import JobDetail, Setting
        self._setup_inventory(third_counting_started=False)
        Setting.objects.create(
            reference='SET-D', account=Account.objects.first(), warehouse=self.warehouse,
            inventory=self.inventory)
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(None, 9)])           # écart : résultat final vide
        JobDetail.objects.filter(job=self.job, counting__order__in=(1, 2)).update(status='TERMINE')
        Assigment.objects.filter(job=self.job).update(status='TERMINE')
        Job.objects.filter(id=self.job.id).update(status='ENTAME')
        client = APIClient(HTTP_HOST='localhost')
        client.force_authenticate(user=self.user)
        response = client.get(
            f'/web/api/inventory/{self.inventory.id}/warehouse/{self.warehouse.id}/jobs/discrepancies-by-counting/')
        self.assertEqual(response.status_code, 200, response.data)
        data = response.data['data']
        groups = data if isinstance(data, list) else [data]
        self.assertEqual([g['next_counting_order'] for g in groups], [3])
        self.assertEqual([j['job_id'] for j in groups[0]['jobs']], [self.job.id])
        self.assertEqual(groups[0]['jobs'][0]['discrepancies_locations_count'], 1)

    def test_general_without_product_is_still_rejected(self):
        """Non-régression : GENERAL garde un écart par produit (produit obligatoire pour l'écart)."""
        self._setup_inventory(inventory_type='GENERAL')
        self.assertFalse(uses_location_ecart(self.inventory))
        result = self._post(1, [(None, 5)])
        self.assertTrue(result.get('errors'))
        self.assertFalse(EcartComptage.objects.filter(inventory=self.inventory).exists())

    def test_general_with_product_keeps_product_level_ecart(self):
        self._setup_inventory(inventory_type='GENERAL')
        self._post(1, [(self.p1, 3), (self.p2, 4)])
        self._post(2, [(self.p1, 3), (self.p2, 5)])
        # un écart par produit (2), pas un écart par emplacement
        self.assertEqual(EcartComptage.objects.filter(inventory=self.inventory).count(), 2)
