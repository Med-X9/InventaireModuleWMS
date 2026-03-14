"""
Tests pour l'API de création d'inventaire (/inventory/create/).
Ces tests couvrent les règles métiers sur les modes de comptage et leurs paramètres.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.masterdata.models import Account, Warehouse
from apps.inventory.models import Inventory


User = get_user_model()


class InventoryCreateAPITestCase(TestCase):
    """Suite de tests pour l'API de création d'inventaire."""

    def setUp(self) -> None:
        """Initialise le client et les données de base (account, warehouse)."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="inventory_tester",
            type="Web",
            email="inventory@test.com",
            password="strong-pass-123",
            nom="Test",
            prenom="Inventory",
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            reference="ACC-TEST",
            account_name="Compte Test",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-TEST",
            warehouse_name="Entrepôt Test",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.url = reverse("inventory-create")

    def _base_payload(self) -> dict:
        """Construit le payload minimal valide pour créer un inventaire."""
        return {
            "label": "Inventaire Validation Comptages",
            "date": timezone.now().date().isoformat(),
            "account_id": self.account.id,
            "warehouse": [
                {"id": self.warehouse.id},
            ],
            "comptages": [
                {
                    "order": 1,
                    "count_mode": "image de stock",
                    "unit_scanned": False,
                    "entry_quantity": False,
                    "n_lot": False,
                    "dlc": False,
                    "n_serie": False,
                    "is_variant": False,
                    "show_product": False,
                    "stock_situation": True,
                    "quantity_show": False,
                },
                {
                    "order": 2,
                    "count_mode": "par article",
                    "unit_scanned": False,
                    "entry_quantity": False,
                    "n_lot": False,
                    "dlc": False,
                    "n_serie": False,
                    "is_variant": True,
                    "show_product": False,
                    "stock_situation": False,
                    "quantity_show": True,
                },
                {
                    "order": 3,
                    "count_mode": "par article",
                    "unit_scanned": False,
                    "entry_quantity": False,
                    "n_lot": False,
                    "dlc": False,
                    "n_serie": False,
                    "is_variant": True,
                    "show_product": False,
                    "stock_situation": False,
                    "quantity_show": True,
                },
            ],
        }

    def test_create_inventory_success_image_stock_followed_by_par_article(self) -> None:
        """
        Vérifie qu'un inventaire est créé avec succès quand :
        - le 1er comptage est 'image de stock'
        - les 2e et 3e comptages sont 'par article' avec les mêmes paramètres.
        """
        payload = self._base_payload()

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Inventory.objects.filter(label=payload["label"]).exists())

    def test_create_inventory_error_on_mismatched_par_article_parameters(self) -> None:
        """
        Vérifie qu'une erreur est renvoyée si les paramètres 'par article'
        ne sont pas identiques entre les comptages lorsque le 1er comptage est 'image de stock'.
        """
        payload = self._base_payload()
        payload["comptages"][2]["is_variant"] = False  # Paramètre différent du 1er comptage 'par article'

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Variante", str(response.data))
        self.assertFalse(Inventory.objects.filter(label=payload["label"]).exists())

    def test_create_inventory_error_on_par_article_inconsistent_modes(self) -> None:
        """
        Vérifie qu'une erreur est renvoyée lorsque le 1er comptage est 'par article'
        mais que les comptages 2 et 3 ne reprennent pas le même mode.
        """
        payload = self._base_payload()
        payload["comptages"][0]["count_mode"] = "par article"
        payload["comptages"][0]["stock_situation"] = False
        payload["comptages"][0]["is_variant"] = True
        payload["comptages"][0]["quantity_show"] = True
        payload["comptages"][1]["count_mode"] = "par article"
        payload["comptages"][2]["count_mode"] = "en vrac"
        payload["comptages"][2]["unit_scanned"] = True
        payload["comptages"][2]["n_lot"] = False
        payload["comptages"][2]["dlc"] = False
        payload["comptages"][2]["n_serie"] = False
        payload["comptages"][2]["is_variant"] = False

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Si le premier comptage est 'par article'", str(response.data))
        self.assertFalse(Inventory.objects.filter(label=payload["label"]).exists())

    def test_create_inventory_error_on_par_article_variant_mismatch(self) -> None:
        """
        Vérifie qu'une erreur est renvoyée lorsque le 1er comptage est 'par article'
        avec une configuration variante qui n'est pas reprise par les comptages suivants.
        """
        payload = self._base_payload()
        payload["comptages"][0].update(
            {
                "count_mode": "par article",
                "stock_situation": False,
                "is_variant": True,
                "quantity_show": True,
            }
        )
        payload["comptages"][1]["count_mode"] = "par article"
        payload["comptages"][1]["is_variant"] = True
        payload["comptages"][2]["count_mode"] = "par article"
        payload["comptages"][2]["is_variant"] = False  # divergence

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Variante", str(response.data))
        self.assertFalse(Inventory.objects.filter(label=payload["label"]).exists())

