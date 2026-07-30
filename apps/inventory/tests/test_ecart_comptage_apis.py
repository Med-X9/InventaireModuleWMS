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

    def test_update_final_result_works_with_less_than_two_sequences(self) -> None:
        """
        Vérifie que la mise à jour du résultat final fonctionne même avec moins de 2 séquences
        (la validation a été désactivée dans le service).
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        ecart2.refresh_from_db()
        self.assertEqual(ecart2.final_result, 50)

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

    def test_bulk_resolve_ecarts_only_with_final_result(self) -> None:
        """
        Vérifie que l'API de résolution en masse (par magasin) ne marque
        comme résolus que les écarts du magasin avec final_result et
        assez de séquences (GENERAL ≥ 2).
        """
        other_warehouse = Warehouse.objects.create(
            reference="WH-ECART-OTHER",
            warehouse_name="Autre magasin",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        other_job = Job.objects.create(
            reference="JOB-ECART-OTHER",
            status="EN ATTENTE",
            warehouse=other_warehouse,
            inventory=self.inventory,
        )

        # Écart magasin courant — 2 séquences + final_result → éligible
        ecart_with_result1 = EcartComptage.objects.create(
            reference="ECT-WITH-RESULT-1",
            inventory=self.inventory,
            total_sequences=2,
            resolved=False,
            final_result=100,
        )
        detail_a1 = CountingDetail.objects.create(
            reference="CD-BR-A1",
            counting=self.counting1,
            location=self.location,
            job=self.job,
            quantity_inventoried=10,
        )
        detail_a2 = CountingDetail.objects.create(
            reference="CD-BR-A2",
            counting=self.counting2,
            location=self.location,
            job=self.job,
            quantity_inventoried=12,
        )
        ComptageSequence.objects.create(
            reference="CS-BR-A1",
            ecart_comptage=ecart_with_result1,
            sequence_number=1,
            counting_detail=detail_a1,
            quantity=10,
        )
        ComptageSequence.objects.create(
            reference="CS-BR-A2",
            ecart_comptage=ecart_with_result1,
            sequence_number=2,
            counting_detail=detail_a2,
            quantity=12,
            ecart_with_previous=2,
        )

        # Écart magasin courant — final_result mais 1 seule séquence → NON résolu (GENERAL)
        ecart_one_seq = EcartComptage.objects.create(
            reference="ECT-ONE-SEQ",
            inventory=self.inventory,
            total_sequences=1,
            resolved=False,
            final_result=50,
        )
        detail_one = CountingDetail.objects.create(
            reference="CD-BR-ONE",
            counting=self.counting1,
            location=self.location,
            job=self.job,
            quantity_inventoried=5,
        )
        ComptageSequence.objects.create(
            reference="CS-BR-ONE",
            ecart_comptage=ecart_one_seq,
            sequence_number=1,
            counting_detail=detail_one,
            quantity=5,
        )

        # Écart magasin courant — 2 séquences sans final_result → NON résolu
        ecart_without_result = EcartComptage.objects.create(
            reference="ECT-WITHOUT-RESULT",
            inventory=self.inventory,
            total_sequences=2,
            resolved=False,
            final_result=None,
        )
        detail_b1 = CountingDetail.objects.create(
            reference="CD-BR-B1",
            counting=self.counting1,
            location=self.location,
            job=self.job,
            quantity_inventoried=8,
        )
        detail_b2 = CountingDetail.objects.create(
            reference="CD-BR-B2",
            counting=self.counting2,
            location=self.location,
            job=self.job,
            quantity_inventoried=9,
        )
        ComptageSequence.objects.create(
            reference="CS-BR-B1",
            ecart_comptage=ecart_without_result,
            sequence_number=1,
            counting_detail=detail_b1,
            quantity=8,
        )
        ComptageSequence.objects.create(
            reference="CS-BR-B2",
            ecart_comptage=ecart_without_result,
            sequence_number=2,
            counting_detail=detail_b2,
            quantity=9,
            ecart_with_previous=1,
        )

        # Écart autre magasin — éligible mais hors scope → NON touché
        ecart_other_wh = EcartComptage.objects.create(
            reference="ECT-OTHER-WH",
            inventory=self.inventory,
            total_sequences=2,
            resolved=False,
            final_result=300,
        )
        detail_o1 = CountingDetail.objects.create(
            reference="CD-BR-O1",
            counting=self.counting1,
            location=self.location,
            job=other_job,
            quantity_inventoried=3,
        )
        detail_o2 = CountingDetail.objects.create(
            reference="CD-BR-O2",
            counting=self.counting2,
            location=self.location,
            job=other_job,
            quantity_inventoried=3,
        )
        ComptageSequence.objects.create(
            reference="CS-BR-O1",
            ecart_comptage=ecart_other_wh,
            sequence_number=1,
            counting_detail=detail_o1,
            quantity=3,
        )
        ComptageSequence.objects.create(
            reference="CS-BR-O2",
            ecart_comptage=ecart_other_wh,
            sequence_number=2,
            counting_detail=detail_o2,
            quantity=3,
            ecart_with_previous=0,
        )

        bulk_resolve_url = reverse(
            "ecart-comptage-bulk-resolve",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )

        response = self.client.patch(
            bulk_resolve_url,
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["resolved_count"], 1)
        self.assertEqual(response.data["data"]["warehouse_id"], self.warehouse.id)
        self.assertEqual(response.data["data"]["min_sequences_required"], 2)
        self.assertEqual(response.data["data"]["inventory_type"], "GENERAL")

        ecart_with_result1.refresh_from_db()
        ecart_one_seq.refresh_from_db()
        ecart_without_result.refresh_from_db()
        ecart_other_wh.refresh_from_db()

        self.assertTrue(ecart_with_result1.resolved)
        self.assertEqual(ecart_with_result1.stopped_reason, "RESOLU_MANUEL")
        self.assertFalse(ecart_one_seq.resolved)
        self.assertFalse(ecart_without_result.resolved)
        self.assertFalse(ecart_other_wh.resolved)

    def test_bulk_resolve_ecarts_magasin_one_sequence(self) -> None:
        """
        MAGASIN : un seul comptage suffit pour bulk-resolve si final_result est renseigné.
        """
        self.inventory.inventory_type = "MAGASIN"
        self.inventory.save(update_fields=["inventory_type"])

        ecart = EcartComptage.objects.create(
            reference="ECT-MAG-1",
            inventory=self.inventory,
            total_sequences=1,
            resolved=False,
            final_result=15,
        )
        detail = CountingDetail.objects.create(
            reference="CD-MAG-1",
            counting=self.counting1,
            location=self.location,
            job=self.job,
            quantity_inventoried=15,
        )
        ComptageSequence.objects.create(
            reference="CS-MAG-1",
            ecart_comptage=ecart,
            sequence_number=1,
            counting_detail=detail,
            quantity=15,
        )

        bulk_resolve_url = reverse(
            "ecart-comptage-bulk-resolve",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )
        response = self.client.patch(bulk_resolve_url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["resolved_count"], 1)
        self.assertEqual(response.data["data"]["min_sequences_required"], 1)
        self.assertEqual(response.data["data"]["inventory_type"], "MAGASIN")
        ecart.refresh_from_db()
        self.assertTrue(ecart.resolved)

    def test_bulk_resolve_ecarts_inventory_not_found(self) -> None:
        """
        Vérifie que l'API retourne 404 si l'inventaire n'existe pas.
        """
        bulk_resolve_url = reverse(
            "ecart-comptage-bulk-resolve",
            kwargs={
                "inventory_id": 99999,
                "warehouse_id": self.warehouse.id,
            },
        )

        response = self.client.patch(
            bulk_resolve_url,
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])


