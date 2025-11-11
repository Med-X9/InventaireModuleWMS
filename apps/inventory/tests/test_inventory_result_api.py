"""
Tests pour l'API de résultats d'inventaire par entrepôt.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.inventory.models import (
    Inventory,
    Counting,
    CountingDetail,
    Job,
    Setting,
)
from apps.masterdata.models import (
    Account,
    Warehouse,
    ZoneType,
    Zone,
    SousZone,
    LocationType,
    Location,
)


class InventoryResultAPIViewTestCase(TestCase):
    """
    Suite de tests pour l'endpoint /inventory/<inventory_id>/warehouses/<warehouse_id>/results/.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="result_tester",
            email="result@test.com",
            password="StrongPass123!",
            type="Web",
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            reference="ACC-TEST",
            account_name="Compte Test",
            account_statuts="ACTIVE",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-TEST",
            warehouse_name="Entrepôt Test",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.inventory = Inventory.objects.create(
            label="Inventaire Test",
            date=timezone.now(),
            status="EN PREPARATION",
            inventory_type="GENERAL",
        )
        Setting.objects.create(
            reference="SET-RESULT-TEST",
            account=self.account,
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        # Création des structures d'emplacement minimales.
        zone_type = ZoneType.objects.create(
            reference="ZT-01",
            type_name="Zone test",
            status="ACTIVE",
        )
        zone = Zone.objects.create(
            reference="Z-01",
            zone_name="Zone 1",
            zone_type=zone_type,
            warehouse=self.warehouse,
            zone_status="ACTIVE",
        )
        sous_zone = SousZone.objects.create(
            reference="SZ-01",
            sous_zone_name="Sous-zone 1",
            zone=zone,
            sous_zone_status="ACTIVE",
        )
        location_type = LocationType.objects.create(
            reference="LT-01",
            name="Type emplacement",
        )
        self.location_a = Location.objects.create(
            reference="LOC-A",
            location_reference="A-01-01",
            sous_zone=sous_zone,
            location_type=location_type,
        )
        self.location_b = Location.objects.create(
            reference="LOC-B",
            location_reference="B-02-03",
            sous_zone=sous_zone,
            location_type=location_type,
        )

        # Comptages (mode unique en vrac).
        self.countings = {
            order: Counting.objects.create(
                reference=f"CNT-RESULT-{order}",
                inventory=self.inventory,
                order=order,
                count_mode="en vrac",
            )
            for order in range(1, 6)
        }

        # Jobs par emplacement.
        self.job_a = Job.objects.create(
            reference="JOB-RESULT-A",
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=self.inventory,
        )
        self.job_b = Job.objects.create(
            reference="JOB-RESULT-B",
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        # Détails de comptage : emplacement A (3 comptages), emplacement B (5 comptages).
        CountingDetail.objects.create(
            reference="CD-A-1",
            counting=self.countings[1],
            location=self.location_a,
            job=self.job_a,
            quantity_inventoried=120,
        )
        CountingDetail.objects.create(
            reference="CD-A-2",
            counting=self.countings[2],
            location=self.location_a,
            job=self.job_a,
            quantity_inventoried=118,
        )
        CountingDetail.objects.create(
            reference="CD-A-3",
            counting=self.countings[3],
            location=self.location_a,
            job=self.job_a,
            quantity_inventoried=121,
        )

        quantities_b = [80, 79, 78, 81, 81]
        for order, quantity in enumerate(quantities_b, start=1):
            CountingDetail.objects.create(
                reference=f"CD-B-{order}",
                counting=self.countings[order],
                location=self.location_b,
                job=self.job_b,
                quantity_inventoried=quantity,
            )

        self.url = reverse(
            "inventory-warehouse-results",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )

    def test_inventory_results_standardized_format_en_vrac(self) -> None:
        """
        Vérifie que le format standardisé est respecté en mode 'en vrac'
        avec complétion des comptages manquants à None.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 2)

        entry_a = next(
            item for item in response.data["data"] if item["location"] == "A-01-01"
        )
        self.assertNotIn("product", entry_a)
        self.assertEqual(entry_a["location_id"], self.location_a.id)
        self.assertEqual(entry_a["job_id"], self.job_a.id)
        self.assertEqual(entry_a["1er comptage"], 120)
        self.assertEqual(entry_a["2er comptage"], 118)
        self.assertEqual(entry_a["ecart_1_2"], -2)
        self.assertEqual(entry_a["3er comptage"], 121)
        self.assertEqual(entry_a["ecart_2_3"], 3)
        self.assertIsNone(entry_a["4er comptage"])
        self.assertIsNone(entry_a["ecart_3_4"])
        self.assertIsNone(entry_a["5er comptage"])
        self.assertIsNone(entry_a["ecart_4_5"])
        self.assertEqual(entry_a["final_result"], 121)

        entry_b = next(
            item for item in response.data["data"] if item["location"] == "B-02-03"
        )
        self.assertEqual(entry_b["location_id"], self.location_b.id)
        self.assertEqual(entry_b["job_id"], self.job_b.id)
        self.assertEqual(entry_b["1er comptage"], 80)
        self.assertEqual(entry_b["ecart_1_2"], -1)
        self.assertEqual(entry_b["4er comptage"], 81)
        self.assertEqual(entry_b["ecart_3_4"], 3)
        self.assertEqual(entry_b["5er comptage"], 81)
        self.assertEqual(entry_b["ecart_4_5"], 0)
        self.assertEqual(entry_b["final_result"], 81)

