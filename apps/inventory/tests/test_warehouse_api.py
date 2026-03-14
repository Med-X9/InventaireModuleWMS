"""
Tests pour l'API de récupération des entrepôts d'un compte.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.masterdata.models import (
    Account,
    Warehouse,
    ZoneType,
    Zone,
    SousZone,
    LocationType,
    Location,
    RegroupementEmplacement,
)


class AccountWarehousesAPITestCase(APITestCase):
    """Tests pour l'API de récupération des entrepôts d'un compte."""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="tester",
            type="Web",
            password="password123",
            email="tester@example.com",
            nom="Test",
            prenom="Utilisateur",
        )
        self.client.force_authenticate(self.user)

        self.account = Account.objects.create(
            reference="ACC-001",
            account_name="Compte Test",
            account_statuts="ACTIVE",
        )

        self.warehouse_primary = Warehouse.objects.create(
            reference="WH-001",
            warehouse_name="Entrepôt Principal",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )

        self.warehouse_secondary = Warehouse.objects.create(
            reference="WH-002",
            warehouse_name="Entrepôt Secondaire",
            warehouse_type="RECEIVING",
            status="ACTIVE",
        )

        zone_type = ZoneType.objects.create(
            reference="ZT-001",
            type_name="Zone Type Test",
            description="Type de zone de test",
            status="ACTIVE",
        )

        location_type = LocationType.objects.create(
            reference="LT-001",
            name="Type Emplacement Test",
            description="Type d'emplacement",
        )

        regroupement = RegroupementEmplacement.objects.create(
            account=self.account,
            nom="Regroupement Test",
        )

        # Premier entrepôt avec deux emplacements pour tester la déduplication
        zone_primary = Zone.objects.create(
            reference="Z-001",
            warehouse=self.warehouse_primary,
            zone_name="Zone Principale",
            zone_type=zone_type,
            description="Zone pour tests",
            zone_status="ACTIVE",
        )
        sous_zone_primary = SousZone.objects.create(
            reference="SZ-001",
            sous_zone_name="Sous Zone Principale",
            zone=zone_primary,
            description="Sous zone pour tests",
            sous_zone_status="ACTIVE",
        )
        Location.objects.create(
            reference="LOC-001",
            location_reference="LOC-001",
            sous_zone=sous_zone_primary,
            location_type=location_type,
            is_active=True,
            regroupement=regroupement,
        )
        Location.objects.create(
            reference="LOC-002",
            location_reference="LOC-002",
            sous_zone=sous_zone_primary,
            location_type=location_type,
            is_active=True,
            regroupement=regroupement,
        )

        # Second entrepôt avec un emplacement
        zone_secondary = Zone.objects.create(
            reference="Z-002",
            warehouse=self.warehouse_secondary,
            zone_name="Zone Secondaire",
            zone_type=zone_type,
            description="Zone secondaire pour tests",
            zone_status="ACTIVE",
        )
        sous_zone_secondary = SousZone.objects.create(
            reference="SZ-002",
            sous_zone_name="Sous Zone Secondaire",
            zone=zone_secondary,
            description="Sous zone secondaire",
            sous_zone_status="ACTIVE",
        )
        Location.objects.create(
            reference="LOC-003",
            location_reference="LOC-003",
            sous_zone=sous_zone_secondary,
            location_type=location_type,
            is_active=True,
            regroupement=regroupement,
        )

    def test_get_warehouses_by_account_success(self) -> None:
        """Vérifie la récupération des entrepôts liés à un compte."""
        url = reverse("account-warehouses", kwargs={"account_id": self.account.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(len(response.data["data"]), 2)

        returned_references = {warehouse["reference"] for warehouse in response.data["data"]}
        self.assertSetEqual(
            returned_references,
            {self.warehouse_primary.reference, self.warehouse_secondary.reference},
        )

    def test_get_warehouses_by_account_not_found(self) -> None:
        """Vérifie la réponse lorsqu'aucun entrepôt n'est lié au compte."""
        empty_account = Account.objects.create(
            reference="ACC-002",
            account_name="Compte Sans Entrepôt",
            account_statuts="ACTIVE",
        )
        RegroupementEmplacement.objects.create(
            account=empty_account,
            nom="Regroupement Vide",
        )

        url = reverse("account-warehouses", kwargs={"account_id": empty_account.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("Aucun entrepôt", response.data["message"])

    def test_get_warehouses_by_account_invalid_account(self) -> None:
        """Vérifie la réponse pour un identifiant de compte inexistant."""
        url = reverse("account-warehouses", kwargs={"account_id": 999999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("Le compte demandé n'existe pas", response.data["message"])

