"""
Tests de création d'inventaire (GENERAL / TOURNANT / MAGASIN) — sans configuration de comptage.
+ test de configuration GENERAL (exactement 3 comptages).
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.masterdata.models import Account, Warehouse
from apps.inventory.models import Inventory, Counting, Setting
from apps.inventory.constants import InventoryType, InventoryStatus, CountMode


User = get_user_model()


class InventoryCreateByTypeAPITestCase(TestCase):
    """Création inventaire par type — sans étape de configuration comptage."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="inv_create_types",
            type="Web",
            email="inv_create_types@test.com",
            password="strong-pass-123",
            nom="Test",
            prenom="Create",
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            reference="ACC-CREATE-TYPES",
            account_name="Compte Create Types",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-CREATE-TYPES",
            warehouse_name="Entrepôt Create Types",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.url = reverse("inventory-create")
        self.today = timezone.now().date().isoformat()

    def _create_payload(self, label: str, inventory_type: str) -> dict:
        return {
            "label": label,
            "inventory_type": inventory_type,
            "date": self.today,
            "account_id": self.account.id,
            "warehouse": [{"id": self.warehouse.id, "date": self.today}],
        }

    def _general_comptages(self) -> list:
        return [
            {
                "order": 1,
                "count_mode": CountMode.STOCK_IMAGE,
                "stock_situation": True,
            },
            {
                "order": 2,
                "count_mode": CountMode.BY_ARTICLE,
                "n_lot": False,
                "dlc": False,
                "n_serie": False,
            },
            {
                "order": 3,
                "count_mode": CountMode.BY_ARTICLE,
                "n_lot": False,
                "dlc": False,
                "n_serie": False,
            },
        ]

    def test_create_inventory_general_without_countings(self) -> None:
        """GENERAL : création sans comptages."""
        payload = self._create_payload("Inventaire GENERAL test", InventoryType.GENERAL)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        inventory = Inventory.objects.filter(label="Inventaire GENERAL test").first()
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory.inventory_type, InventoryType.GENERAL)
        self.assertEqual(inventory.status, InventoryStatus.EN_CONFIGURATION)
        self.assertIsNotNone(inventory.en_configuration_status_date)
        self.assertEqual(Counting.objects.filter(inventory=inventory).count(), 0)
        self.assertEqual(Setting.objects.filter(inventory=inventory).count(), 1)

    def test_create_inventory_magasin_without_countings(self) -> None:
        """MAGASIN : création sans comptages."""
        payload = self._create_payload("Inventaire MAGASIN test", InventoryType.MAGASIN)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        inventory = Inventory.objects.filter(label="Inventaire MAGASIN test").first()
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory.inventory_type, InventoryType.MAGASIN)
        self.assertEqual(inventory.status, InventoryStatus.EN_CONFIGURATION)
        self.assertEqual(Counting.objects.filter(inventory=inventory).count(), 0)

    def test_create_inventory_tournant_without_countings(self) -> None:
        """TOURNANT : création sans comptages."""
        payload = self._create_payload("Inventaire TOURNANT test", InventoryType.TOURNANT)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        inventory = Inventory.objects.filter(label="Inventaire TOURNANT test").first()
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory.inventory_type, InventoryType.TOURNANT)
        self.assertEqual(inventory.status, InventoryStatus.EN_CONFIGURATION)
        self.assertEqual(Counting.objects.filter(inventory=inventory).count(), 0)

    def test_create_rejects_comptages_in_payload(self) -> None:
        """Tous types : refus si comptages fournis à la création."""
        payload = self._create_payload("Inventaire GENERAL invalide", InventoryType.GENERAL)
        payload["comptages"] = self._general_comptages()
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_requires_warehouse_date(self) -> None:
        """Date magasin obligatoire à la création."""
        payload = {
            "label": "Inventaire sans date magasin",
            "inventory_type": InventoryType.GENERAL,
            "date": self.today,
            "account_id": self.account.id,
            "warehouse": [{"id": self.warehouse.id}],
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_configure_general_exactly_three_countings(self) -> None:
        """GENERAL : configuration = exactement 3 comptages."""
        create_resp = self.client.post(
            self.url,
            self._create_payload("Inventaire GENERAL config", InventoryType.GENERAL),
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED, create_resp.data)
        inventory = Inventory.objects.get(label="Inventaire GENERAL config")

        config_url = reverse("inventory-countings", kwargs={"pk": inventory.id})
        response = self.client.post(
            config_url,
            {"comptages": self._general_comptages()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Counting.objects.filter(inventory=inventory).count(), 3)
        orders = list(
            Counting.objects.filter(inventory=inventory)
            .order_by("order")
            .values_list("order", flat=True)
        )
        self.assertEqual(orders, [1, 2, 3])
        inventory.refresh_from_db()
        self.assertEqual(inventory.status, InventoryStatus.EN_PREPARATION)
        self.assertIsNotNone(inventory.en_preparation_status_date)

    def test_configure_general_rejects_not_exactly_three(self) -> None:
        """GENERAL : refus si pas exactement 3 comptages à la config."""
        create_resp = self.client.post(
            self.url,
            self._create_payload("Inventaire GENERAL bad config", InventoryType.GENERAL),
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED, create_resp.data)
        inventory = Inventory.objects.get(label="Inventaire GENERAL bad config")

        config_url = reverse("inventory-countings", kwargs={"pk": inventory.id})
        response = self.client.post(
            config_url,
            {"comptages": self._general_comptages()[:2]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
