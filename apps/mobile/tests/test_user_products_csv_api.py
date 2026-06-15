"""
Tests unitaires pour l'export CSV des produits du compte utilisateur.

Endpoint : GET /mobile/api/products/
Utilisateur : equipe-1001 / user1234
"""
import csv
import io

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.masterdata.models import Account, Family, Product

User = get_user_model()

USERNAME = "equipe-1001"
PASSWORD = "user1234"
LOGIN_URL = "/mobile/api/auth/login/"


class UserProductsCsvAPITestCase(TestCase):
    """Tests pour GET /mobile/api/products/ (export CSV filtré par compte)."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.products_url = reverse("mobile:mobile_user_products")

        self.account = Account.objects.create(
            reference="ACC-EQUIPE-1001",
            account_name="Compte Equipe 1001",
            account_statuts="ACTIVE",
        )

        self.other_account = Account.objects.create(
            reference="ACC-OTHER",
            account_name="Autre Compte",
            account_statuts="ACTIVE",
        )

        self.user = User.objects.create_user(
            username=USERNAME,
            password=PASSWORD,
            type="Mobile",
            compte=self.account,
        )

        self.family = Family.objects.create(
            reference="FAM-EQUIPE-1001",
            family_name="Famille Equipe",
            compte=self.account,
            family_status="ACTIVE",
        )

        other_family = Family.objects.create(
            reference="FAM-OTHER",
            family_name="Famille Autre",
            compte=self.other_account,
            family_status="ACTIVE",
        )

        # Statut en minuscule comme en production (active vs ACTIVE)
        self.user_product = Product.objects.create(
            reference="PRD-USER-001",
            Internal_Product_Code="INT-EQ-001",
            Short_Description="Produit equipe test",
            Barcode="0123456789012",
            Stock_Unit="UN",
            Product_Status="active",
            Product_Family=self.family,
        )

        Product.objects.create(
            reference="PRD-OTHER-001",
            Internal_Product_Code="INT-OTHER-001",
            Short_Description="Produit autre compte",
            Barcode="0999999999999",
            Stock_Unit="UN",
            Product_Status="active",
            Product_Family=other_family,
        )

    def _login_and_get_access_token(self) -> str:
        response = self.client.post(
            LOGIN_URL,
            {"username": USERNAME, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("success"))
        return response.data["data"]["access"]

    def _parse_csv_content(self, content: bytes) -> list[dict]:
        text = content.decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(text)))

    def test_login_and_export_products_csv_for_user_account(self):
        """Connexion equipe-1001 puis export CSV avec les produits du compte."""
        access_token = self._login_and_get_access_token()

        response = self.client.get(
            self.products_url,
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("attachment", response["Content-Disposition"])

        rows = self._parse_csv_content(response.content)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["product_name"], "Produit equipe test")
        self.assertEqual(rows[0]["internal_product_code"], "INT-EQ-001")
        self.assertEqual(rows[0]["family_name"], "Famille Equipe")

    def test_export_products_csv_without_auth_returns_401(self):
        response = self.client.get(self.products_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_products_csv_excludes_other_account_products(self):
        access_token = self._login_and_get_access_token()

        response = self.client.get(
            self.products_url,
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        rows = self._parse_csv_content(response.content)
        internal_codes = {row["internal_product_code"] for row in rows}
        self.assertIn("INT-EQ-001", internal_codes)
        self.assertNotIn("INT-OTHER-001", internal_codes)

    def test_export_products_csv_with_lowercase_active_status(self):
        """Les produits avec Product_Status='active' sont bien exportés."""
        access_token = self._login_and_get_access_token()
        response = self.client.get(
            self.products_url,
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(self._parse_csv_content(response.content)), 0)
