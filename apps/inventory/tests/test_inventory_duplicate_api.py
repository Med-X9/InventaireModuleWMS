"""
Tests pour l'API de duplication d'inventaire (/inventory/<pk>/duplicate/).
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.masterdata.models import Account, Warehouse
from apps.inventory.models import Inventory, Setting, Counting


User = get_user_model()


class InventoryDuplicateAPITestCase(TestCase):
    """Suite de tests pour l'API de duplication d'inventaire."""

    def setUp(self) -> None:
        """Initialise le client authentifié et les entités de base."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="inventory_duplication_tester",
            email="duplication@test.com",
            password="strong-pass-123",
            type="Web",
            nom="Duplication",
            prenom="Tester",
        )
        self.client.force_authenticate(user=self.user)

        self.account = Account.objects.create(
            reference="ACC-DUPLICATE",
            account_name="Compte Duplication",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-DUPLICATE",
            warehouse_name="Entrepôt Duplication",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )

        self.source_inventory = Inventory.objects.create(
            reference="INV-SOURCE-001",
            label="Inventaire Source",
            date=timezone.now(),
            status="EN PREPARATION",
            inventory_type="GENERAL",
            en_preparation_status_date=timezone.now(),
        )
        Setting.objects.create(
            reference="SET-SOURCE-001",
            inventory=self.source_inventory,
            account=self.account,
            warehouse=self.warehouse,
        )

        # Créer trois comptages pour l'inventaire source
        Counting.objects.create(
            reference="CNT-SOURCE-001",
            inventory=self.source_inventory,
            order=1,
            count_mode="image de stock",
            unit_scanned=False,
            entry_quantity=False,
            is_variant=False,
            n_lot=False,
            n_serie=False,
            dlc=False,
            show_product=False,
            stock_situation=True,
            quantity_show=False,
        )
        Counting.objects.create(
            reference="CNT-SOURCE-002",
            inventory=self.source_inventory,
            order=2,
            count_mode="par article",
            unit_scanned=False,
            entry_quantity=False,
            is_variant=False,
            n_lot=False,
            n_serie=False,
            dlc=False,
            show_product=False,
            stock_situation=False,
            quantity_show=False,
        )
        Counting.objects.create(
            reference="CNT-SOURCE-003",
            inventory=self.source_inventory,
            order=3,
            count_mode="par article",
            unit_scanned=False,
            entry_quantity=False,
            is_variant=False,
            n_lot=False,
            n_serie=False,
            dlc=False,
            show_product=False,
            stock_situation=False,
            quantity_show=False,
        )

        self.url = reverse("inventory-duplicate", kwargs={"pk": self.source_inventory.id})

    def _duplication_payload(self) -> dict:
        """Construit le payload requis pour dupliquer un inventaire."""
        return {
            "label": "Inventaire trimestriel Q3 2024",
            "date": "2026-12-12",
            "inventory_type": "GENERAL",
            "account_id": self.account.id,
            "warehouse": [
                {
                    "id": self.warehouse.id,
                    "date": "2025-12-15",
                }
            ],
        }

    def test_duplicate_inventory_success(self) -> None:
        """
        Vérifie la duplication complète :
        - nouveau record Inventory créé avec le label demandé
        - les comptages dupliqués conservent la configuration de l'inventaire source.
        """
        payload = self._duplication_payload()

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Inventory.objects.filter(label=payload["label"]).exists())
        duplicated_inventory = Inventory.objects.get(label=payload["label"])

        duplicated_countings = Counting.objects.filter(inventory=duplicated_inventory).order_by("order")
        self.assertEqual(duplicated_countings.count(), 3)

        source_countings = list(
            Counting.objects.filter(inventory=self.source_inventory).order_by("order").values(
                "order",
                "count_mode",
                "unit_scanned",
                "entry_quantity",
                "is_variant",
                "n_lot",
                "n_serie",
                "dlc",
                "show_product",
                "stock_situation",
                "quantity_show",
            )
        )
        duplicated_values = list(
            duplicated_countings.values(
                "order",
                "count_mode",
                "unit_scanned",
                "entry_quantity",
                "is_variant",
                "n_lot",
                "n_serie",
                "dlc",
                "show_product",
                "stock_situation",
                "quantity_show",
            )
        )
        self.assertEqual(source_countings, duplicated_values)

        self.assertTrue(
            Setting.objects.filter(
                inventory=duplicated_inventory,
                warehouse=self.warehouse,
                account=self.account,
            ).exists()
        )

    def test_duplicate_inventory_not_found(self) -> None:
        """Vérifie qu'une erreur 404 est retournée si l'inventaire source n'existe pas."""
        url = reverse("inventory-duplicate", kwargs={"pk": self.source_inventory.id + 999})

        response = self.client.post(url, data=self._duplication_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    def test_duplicate_inventory_without_countings_returns_error(self) -> None:
        """Vérifie que la duplication échoue si l'inventaire source n'a pas de comptages."""
        empty_inventory = Inventory.objects.create(
            reference="INV-EMPTY-001",
            label="Inventaire Sans Comptage",
            date=timezone.now(),
            status="EN PREPARATION",
            inventory_type="GENERAL",
            en_preparation_status_date=timezone.now(),
        )
        Setting.objects.create(
            reference="SET-EMPTY-001",
            inventory=empty_inventory,
            account=self.account,
            warehouse=self.warehouse,
        )
        url = reverse("inventory-duplicate", kwargs={"pk": empty_inventory.id})

        response = self.client.post(url, data=self._duplication_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("comptage", str(response.data).lower())


