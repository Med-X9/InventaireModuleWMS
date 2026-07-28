"""
Tests EcartStockTheorique : règles résultat final + verrouillage validation.
"""
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.exceptions import InventoryValidationError
from apps.inventory.models import EcartStockTheorique, Inventory, Setting
from apps.inventory.services.ecart_stock_theorique_service import (
    EcartStockTheoriqueService,
)
from apps.masterdata.models import Account, Warehouse

User = get_user_model()


class DefaultResultatFinalUnitTests(SimpleTestCase):
    """Règle métier résultat final sans DB."""

    def test_equality_uses_pratique(self):
        self.assertEqual(
            EcartStockTheoriqueService.default_resultat_final(5, 5), 5
        )

    def test_gap_returns_null(self):
        self.assertIsNone(
            EcartStockTheoriqueService.default_resultat_final(10, 7)
        )


class EcartStockTheoriqueServiceTests(TestCase):
    """Tests service sync / update / valider."""

    def setUp(self) -> None:
        self.account = Account.objects.create(
            reference="ACC-EST-01",
            account_name="Compte EST",
            account_statuts="ACTIVE",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-EST-01",
            warehouse_name="Magasin EST",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.inventory = Inventory.objects.create(
            reference="INV-EST-01",
            label="Inv EST",
            status="EN REALISATION",
            inventory_type="MAGASIN",
            date=timezone.now(),
        )
        Setting.objects.create(
            account=self.account,
            warehouse=self.warehouse,
            inventory=self.inventory,
            status="LANCEE",
        )
        self.user = User.objects.create_user(
            username="est_user",
            password="pass12345",
            type="ADMIN",
        )
        self.service = EcartStockTheoriqueService()

    def _create_row(self, **kwargs) -> EcartStockTheorique:
        defaults = {
            "inventory": self.inventory,
            "warehouse": self.warehouse,
            "article_cle": "BC-001",
            "mode_groupement": "barcode",
            "designation": "Article test",
            "qte_theorique": 10,
            "qte_pratique": 8,
            "ecart": 2,
            "resultat_final": None,
            "valide": False,
        }
        defaults.update(kwargs)
        return EcartStockTheorique.objects.create(**defaults)

    def test_update_resultat_final_ok(self):
        row = self._create_row()
        updated = self.service.update_resultat_final(row.id, 9)
        self.assertEqual(updated.resultat_final, 9)
        self.assertFalse(updated.valide)

    def test_update_resultat_final_blocked_when_validated(self):
        row = self._create_row(resultat_final=8, valide=True)
        with self.assertRaises(InventoryValidationError):
            self.service.update_resultat_final(row.id, 99)

    def test_valider_requires_resultat_final(self):
        row = self._create_row(resultat_final=None)
        with self.assertRaises(InventoryValidationError):
            self.service.valider(row.id, user=self.user)

    def test_valider_success_locks_line(self):
        row = self._create_row(resultat_final=8)
        validated = self.service.valider(row.id, user=self.user)
        self.assertTrue(validated.valide)
        self.assertIsNotNone(validated.validated_at)
        self.assertEqual(validated.validated_by_id, self.user.id)
        with self.assertRaises(InventoryValidationError):
            self.service.update_resultat_final(row.id, 1)

    def test_sync_skips_validated_resultat_final(self):
        row = self._create_row(
            qte_theorique=10,
            qte_pratique=10,
            ecart=0,
            resultat_final=10,
            valide=True,
        )
        # Sync avec mock compute : on appelle sync qui recalcule ;
        # ligne validée ne doit pas perdre resultat_final / valide.
        # Si aucune donnée stock/gap, sync crée 0 lignes mais ne touche pas validées.
        result = self.service.sync_from_compute(
            self.inventory.id, self.warehouse.id, only_nonzero=False
        )
        row.refresh_from_db()
        self.assertTrue(row.valide)
        self.assertEqual(row.resultat_final, 10)
        self.assertIn("skipped_validated", result)


class EcartStockTheoriqueApiTests(TestCase):
    """Tests HTTP des endpoints ecarts-stock."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="est_api",
            password="pass12345",
            type="ADMIN",
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            reference="ACC-EST-API",
            account_name="Compte EST API",
            account_statuts="ACTIVE",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-EST-API",
            warehouse_name="Magasin EST API",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.inventory = Inventory.objects.create(
            reference="INV-EST-API",
            label="Inv EST API",
            status="EN REALISATION",
            inventory_type="MAGASIN",
            date=timezone.now(),
        )
        Setting.objects.create(
            account=self.account,
            warehouse=self.warehouse,
            inventory=self.inventory,
            status="LANCEE",
        )
        self.row = EcartStockTheorique.objects.create(
            inventory=self.inventory,
            warehouse=self.warehouse,
            article_cle="BC-API",
            mode_groupement="barcode",
            designation="API Art",
            qte_theorique=5,
            qte_pratique=3,
            ecart=2,
            resultat_final=None,
            valide=False,
        )

    def test_patch_resultat_final(self):
        url = reverse("ecarts-stock-update", kwargs={"ecart_id": self.row.id})
        response = self.client.patch(
            url, {"resultat_final": 4}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.row.refresh_from_db()
        self.assertEqual(self.row.resultat_final, 4)

    def test_valider_then_patch_fails(self):
        self.row.resultat_final = 3
        self.row.save()
        valider_url = reverse(
            "ecarts-stock-valider", kwargs={"ecart_id": self.row.id}
        )
        response = self.client.post(valider_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        patch_url = reverse(
            "ecarts-stock-update", kwargs={"ecart_id": self.row.id}
        )
        response = self.client.patch(
            patch_url, {"resultat_final": 99}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valider_selection_multi(self):
        row2 = EcartStockTheorique.objects.create(
            reference="EST-API-2",
            inventory=self.inventory,
            warehouse=self.warehouse,
            article_cle="BC-API-2",
            mode_groupement="barcode",
            designation="API Art 2",
            qte_theorique=4,
            qte_pratique=4,
            ecart=0,
            resultat_final=4,
            valide=False,
        )
        self.row.resultat_final = 3
        self.row.save()

        url = reverse("ecarts-stock-valider-selection")
        response = self.client.post(
            url, {"ecart_ids": [self.row.id, row2.id]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["validated_count"], 2)
        self.row.refresh_from_db()
        row2.refresh_from_db()
        self.assertTrue(self.row.valide)
        self.assertTrue(row2.valide)

    def test_list_endpoint(self):
        url = reverse(
            "ecarts-stock-list",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )
        response = self.client.get(url, {"page": 1, "pageSize": 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sync_endpoint(self):
        url = reverse(
            "ecarts-stock-sync",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("success"))
