"""
Tests workflow MAGASIN : TERMINEE / ANALYSER / CLOTURE + stock-gaps persistés.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.constants import SettingStatus
from apps.inventory.exceptions import InventoryStatusError
from apps.inventory.models import EcartStockTheorique, Inventory, Job, Setting
from apps.inventory.services.setting_service import SettingService
from apps.inventory.services.stock_gap_service import StockGapService
from apps.masterdata.models import Account, Warehouse

User = get_user_model()


class MagasinWorkflowServiceTests(TestCase):
    """Transitions Setting MAGASIN via SettingService."""

    def setUp(self) -> None:
        self.account = Account.objects.create(
            reference="ACC-WF-01",
            account_name="Compte WF",
            account_statuts="ACTIVE",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-WF-01",
            warehouse_name="Magasin WF",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.warehouse2 = Warehouse.objects.create(
            reference="WH-WF-02",
            warehouse_name="Magasin WF 2",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.inventory = Inventory.objects.create(
            reference="INV-WF-01",
            label="Inv WF MAGASIN",
            status="EN REALISATION",
            inventory_type="MAGASIN",
            date=timezone.now(),
        )
        self.setting = Setting.objects.create(
            reference="SET-WF-01",
            account=self.account,
            warehouse=self.warehouse,
            inventory=self.inventory,
            status=SettingStatus.LANCEE,
            status_date_lancement=timezone.now(),
        )
        self.setting2 = Setting.objects.create(
            reference="SET-WF-02",
            account=self.account,
            warehouse=self.warehouse2,
            inventory=self.inventory,
            status=SettingStatus.LANCEE,
            status_date_lancement=timezone.now(),
        )
        self.service = SettingService()

    def _create_job(self, warehouse, job_status: str = "TERMINE") -> Job:
        return Job.objects.create(
            inventory=self.inventory,
            warehouse=warehouse,
            status=job_status,
        )

    def test_complete_warehouse_refuses_incomplete_jobs(self):
        self._create_job(self.warehouse, "ENTAME")
        result = self.service.complete_warehouse(
            self.inventory.id, self.warehouse.id
        )
        self.assertFalse(result["success"])
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.status, SettingStatus.LANCEE)

    def test_complete_warehouse_ok(self):
        self._create_job(self.warehouse, "TERMINE")
        result = self.service.complete_warehouse(
            self.inventory.id, self.warehouse.id
        )
        self.assertTrue(result["success"])
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.status, SettingStatus.TERMINEE)
        self.assertIsNotNone(self.setting.status_date_termine)

    def test_complete_warehouses_partial(self):
        self._create_job(self.warehouse, "TERMINE")
        self._create_job(self.warehouse2, "PRET")
        result = self.service.complete_warehouses(
            self.inventory.id,
            [self.warehouse.id, self.warehouse2.id],
        )
        self.assertEqual(result["completed_count"], 1)
        self.assertEqual(result["failed_count"], 1)
        self.assertFalse(result["success"])
        self.setting.refresh_from_db()
        self.setting2.refresh_from_db()
        self.assertEqual(self.setting.status, SettingStatus.TERMINEE)
        self.assertEqual(self.setting2.status, SettingStatus.LANCEE)

    def test_analyse_requires_terminee(self):
        with self.assertRaises(InventoryStatusError):
            self.service.analyse_warehouse(self.inventory.id, self.warehouse.id)

    def test_analyse_sync_and_status(self):
        self._create_job(self.warehouse, "TERMINE")
        self.service.complete_warehouse(self.inventory.id, self.warehouse.id)

        result = self.service.analyse_warehouse(
            self.inventory.id, self.warehouse.id
        )
        self.assertTrue(result["success"])
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.status, SettingStatus.ANALYSER)
        self.assertIsNotNone(self.setting.status_date_analyse)
        self.assertIn("sync", result)

    def test_close_magasin_refuses_lancee(self):
        with self.assertRaises(InventoryStatusError):
            self.service.close_warehouse(self.inventory.id, self.warehouse.id)

    def test_close_magasin_refuses_non_validated_ecarts(self):
        from apps.inventory.models import EcartStockTheorique

        self.setting.status = SettingStatus.ANALYSER
        self.setting.status_date_analyse = timezone.now()
        self.setting.save()
        EcartStockTheorique.objects.create(
            reference="EST-CLOSE-NV",
            inventory=self.inventory,
            warehouse=self.warehouse,
            article_cle="BC-NV",
            mode_groupement="barcode",
            designation="Non valide",
            qte_theorique=10,
            qte_pratique=8,
            ecart=2,
            resultat_final=8,
            valide=False,
        )
        result = self.service.close_warehouse(
            self.inventory.id, self.warehouse.id
        )
        self.assertFalse(result["success"])
        self.assertGreater(result["ecarts_non_valides_count"], 0)
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.status, SettingStatus.ANALYSER)

    def test_close_magasin_from_analyser(self):
        self.setting.status = SettingStatus.ANALYSER
        self.setting.status_date_analyse = timezone.now()
        self.setting.save()

        result = self.service.close_warehouse(
            self.inventory.id, self.warehouse.id
        )
        self.assertTrue(result["success"])
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.status, SettingStatus.CLOTURE)


class MagasinWorkflowApiTests(TestCase):
    """Endpoints termine / analyser / stock-gaps persistés."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="wf_api",
            password="pass12345",
            type="ADMIN",
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            reference="ACC-WF-API",
            account_name="Compte WF API",
            account_statuts="ACTIVE",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-WF-API",
            warehouse_name="Magasin WF API",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.inventory = Inventory.objects.create(
            reference="INV-WF-API",
            label="Inv WF API",
            status="EN REALISATION",
            inventory_type="MAGASIN",
            date=timezone.now(),
        )
        self.setting = Setting.objects.create(
            reference="SET-WF-API",
            account=self.account,
            warehouse=self.warehouse,
            inventory=self.inventory,
            status=SettingStatus.LANCEE,
            status_date_lancement=timezone.now(),
        )
        Job.objects.create(
            inventory=self.inventory,
            warehouse=self.warehouse,
            status="TERMINE",
        )

    def test_termine_endpoint(self):
        url = reverse(
            "setting-termine",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.status, SettingStatus.TERMINEE)

    def test_analyser_endpoint_creates_table_rows_readable_via_stock_gaps(self):
        self.setting.status = SettingStatus.TERMINEE
        self.setting.status_date_termine = timezone.now()
        self.setting.save()

        # Pré-insérer une ligne comme le ferait sync (évite dépendance stock Excel)
        EcartStockTheorique.objects.create(
            reference="EST-WF-API-1",
            inventory=self.inventory,
            warehouse=self.warehouse,
            article_cle="BC-WF",
            mode_groupement="barcode",
            designation="Art WF",
            qte_theorique=10,
            qte_pratique=7,
            ecart=3,
            resultat_final=None,
            valide=False,
        )

        analyse_url = reverse(
            "setting-analyser",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )
        response = self.client.post(analyse_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.status, SettingStatus.ANALYSER)

        gaps_url = reverse(
            "stock-gaps",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )
        gaps = self.client.get(gaps_url, {"page": 1, "pageSize": 20, "only_nonzero": "true"})
        self.assertEqual(gaps.status_code, status.HTTP_200_OK)
        self.assertEqual(gaps.data.get("source"), "ecart_stock_theorique")
        # Au moins une ligne écart non nulle depuis la table
        self.assertGreaterEqual(gaps.data.get("total", 0), 1)
        self.assertNotIn("mode_groupement", gaps.data)

    def test_list_persisted_stock_gaps_service(self):
        EcartStockTheorique.objects.create(
            reference="EST-EQ-1",
            inventory=self.inventory,
            warehouse=self.warehouse,
            article_cle="BC-EQ",
            mode_groupement="barcode",
            designation="Equal",
            qte_theorique=5,
            qte_pratique=5,
            ecart=0,
            resultat_final=5,
            valide=False,
        )
        EcartStockTheorique.objects.create(
            reference="EST-GAP-1",
            inventory=self.inventory,
            warehouse=self.warehouse,
            article_cle="BC-GAP",
            mode_groupement="barcode",
            designation="Gap",
            qte_theorique=8,
            qte_pratique=3,
            ecart=5,
            resultat_final=None,
            valide=False,
        )
        service = StockGapService()
        only_gap = service.list_persisted_stock_gaps(
            self.inventory.id, self.warehouse.id, only_nonzero=True
        )
        self.assertEqual(only_gap["totaux"]["nombre_lignes"], 1)
        self.assertEqual(only_gap["lignes"][0]["cle"], "BC-GAP")
        self.assertEqual(only_gap["lignes"][0]["qte_inventoriee"], 3)
        self.assertIn("resultat_final", only_gap["lignes"][0])
        self.assertIn("valide", only_gap["lignes"][0])
        self.assertNotIn("mode_groupement", only_gap["lignes"][0])

        all_rows = service.list_persisted_stock_gaps(
            self.inventory.id, self.warehouse.id, only_nonzero=False
        )
        self.assertEqual(all_rows["totaux"]["nombre_lignes"], 2)
