"""
Tests pour les APIs de gestion d'EcartComptage :
- Mise à jour du résultat final
- Résolution de l'écart (resolved = True)
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
    EcartComptage,
    ComptageSequence,
)
from apps.masterdata.models import (
    Warehouse,
    ZoneType,
    Zone,
    SousZone,
    LocationType,
    Location,
)


class EcartComptageAPITestCase(TestCase):
    """
    Suite de tests pour :
    - /ecarts-comptage/<ecart_id>/final-result/
    - /ecarts-comptage/<ecart_id>/resolve/
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="ecart_tester",
            email="ecart@test.com",
            password="StrongPass123!",
            type="Web",
        )
        self.client.force_authenticate(user=self.user)

        self.warehouse = Warehouse.objects.create(
            reference="WH-ECART",
            warehouse_name="Entrepôt Ecart",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )

        # Création d'une structure d'emplacement minimale
        zone_type = ZoneType.objects.create(
            reference="ZT-ECART",
            type_name="Zone test",
            status="ACTIVE",
        )
        zone = Zone.objects.create(
            reference="Z-ECART",
            zone_name="Zone Ecart",
            zone_type=zone_type,
            warehouse=self.warehouse,
            zone_status="ACTIVE",
        )
        sous_zone = SousZone.objects.create(
            reference="SZ-ECART",
            sous_zone_name="Sous-zone Ecart",
            zone=zone,
            sous_zone_status="ACTIVE",
        )
        location_type = LocationType.objects.create(
            reference="LT-ECART",
            name="Type Ecart",
        )
        self.location = Location.objects.create(
            reference="LOC-ECART",
            location_reference="LOC-ECART-01",
            sous_zone=sous_zone,
            location_type=location_type,
        )

        self.inventory = Inventory.objects.create(
            label="Inventaire Ecart",
            date=timezone.now(),
            status="EN PREPARATION",
            inventory_type="GENERAL",
        )

        self.job = Job.objects.create(
            reference="JOB-ECART",
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        # Deux comptages pour l'inventaire
        self.counting1 = Counting.objects.create(
            reference="CNT-ECART-1",
            inventory=self.inventory,
            order=1,
            count_mode="en vrac",
        )
        self.counting2 = Counting.objects.create(
            reference="CNT-ECART-2",
            inventory=self.inventory,
            order=2,
            count_mode="en vrac",
        )

        # On crée un CountingDetail minimal et un EcartComptage lié via
        # ComptageSequence pour simuler les séquences.
        self.ecart = EcartComptage.objects.create(
            reference="ECT-TEST",
            inventory=self.inventory,
            total_sequences=0,
            resolved=False,
        )

        self.detail1 = CountingDetail.objects.create(
            reference="CD-ECART-1",
            counting=self.counting1,
            location=self.location,
            job=self.job,
            quantity_inventoried=10,
        )
        self.detail2 = CountingDetail.objects.create(
            reference="CD-ECART-2",
            counting=self.counting2,
            location=self.location,
            job=self.job,
            quantity_inventoried=12,
        )

        # Deux séquences rattachées à l'écart
        ComptageSequence.objects.create(
            reference="CS-1",
            ecart_comptage=self.ecart,
            sequence_number=1,
            counting_detail=self.detail1,
            quantity=self.detail1.quantity_inventoried,
            ecart_with_previous=None,
        )
        ComptageSequence.objects.create(
            reference="CS-2",
            ecart_comptage=self.ecart,
            sequence_number=2,
            counting_detail=self.detail2,
            quantity=self.detail2.quantity_inventoried,
            ecart_with_previous=2,
        )

        # Mettre à jour total_sequences pour refléter la réalité
        self.ecart.total_sequences = 2
        self.ecart.save()

        self.update_final_result_url = reverse(
            "ecart-comptage-update-final-result",
            kwargs={"ecart_id": self.ecart.id},
        )
        self.resolve_url = reverse(
            "ecart-comptage-resolve",
            kwargs={"ecart_id": self.ecart.id},
        )

    def test_update_final_result_with_two_sequences(self) -> None:
        """
        Vérifie que l'on peut mettre à jour final_result quand il y a au moins 2 séquences.
        """
        payload = {"final_result": 120}

        response = self.client.patch(
            self.update_final_result_url,
            data=payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.ecart.refresh_from_db()
        self.assertEqual(self.ecart.final_result, 120)

    def test_update_final_result_fails_with_less_than_two_sequences(self) -> None:
        """
        Vérifie que la mise à jour du résultat final échoue si moins de 2 séquences.
        """
        # On force un autre écart avec 0 séquence
        ecart2 = EcartComptage.objects.create(
            reference="ECT-NO-SEQ",
            inventory=self.inventory,
            total_sequences=0,
            resolved=False,
        )
        url = reverse(
            "ecart-comptage-update-final-result",
            kwargs={"ecart_id": ecart2.id},
        )

        response = self.client.patch(
            url,
            data={"final_result": 50},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Il faut au moins deux comptages", response.data["message"])

    def test_resolve_ecart_requires_final_result(self) -> None:
        """
        Vérifie que la résolution échoue tant que final_result est None.
        """
        # final_result est None au départ
        response = self.client.patch(
            self.resolve_url,
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Le résultat final doit être renseigné", response.data["message"])

    def test_resolve_ecart_success(self) -> None:
        """
        Vérifie qu'on peut résoudre l'écart si 2 séquences et final_result non nul.
        """
        # D'abord on met à jour le résultat final
        self.ecart.final_result = 100
        self.ecart.save()

        response = self.client.patch(
            self.resolve_url,
            data={"justification": "Résolution test"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.ecart.refresh_from_db()
        self.assertTrue(self.ecart.resolved)
        self.assertEqual(self.ecart.justification, "Résolution test")


