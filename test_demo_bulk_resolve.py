#!/usr/bin/env python3
"""
Test de démonstration pour l'API de résolution en masse des écarts de comptage.
Utilise le framework de test Django pour éviter les problèmes de configuration.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

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


class BulkResolveDemoTestCase(TestCase):
    """
    Test de démonstration pour l'API de résolution en masse.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="demo_tester",
            email="demo@test.com",
            password="DemoPass123!",
            type="Web",
        )
        self.client.force_authenticate(user=self.user)

        # Création des données de base
        self.warehouse = Warehouse.objects.create(
            reference="WH-DEMO",
            warehouse_name="Entrepot Demo",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )

        zone_type = ZoneType.objects.create(
            reference="ZT-DEMO",
            type_name="Zone Demo",
            status="ACTIVE",
        )
        zone = Zone.objects.create(
            reference="Z-DEMO",
            zone_name="Zone Demo",
            zone_type=zone_type,
            warehouse=self.warehouse,
            zone_status="ACTIVE",
        )
        sous_zone = SousZone.objects.create(
            reference="SZ-DEMO",
            sous_zone_name="Sous-zone Demo",
            zone=zone,
            sous_zone_status="ACTIVE",
        )
        location_type = LocationType.objects.create(
            reference="LT-DEMO",
            name="Type Demo",
        )
        self.location = Location.objects.create(
            reference="LOC-DEMO",
            location_reference="LOC-DEMO-01",
            sous_zone=sous_zone,
            location_type=location_type,
        )

        self.inventory = Inventory.objects.create(
            label="Inventaire Demo - Resolution en masse",
            date=timezone.now(),
            status="EN PREPARATION",
            inventory_type="GENERAL",
        )

        self.job = Job.objects.create(
            reference="JOB-DEMO",
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        counting1 = Counting.objects.create(
            reference="CNT-DEMO-1",
            inventory=self.inventory,
            order=1,
            count_mode="en vrac",
        )
        counting2 = Counting.objects.create(
            reference="CNT-DEMO-2",
            inventory=self.inventory,
            order=2,
            count_mode="en vrac",
        )

        self.detail1 = CountingDetail.objects.create(
            reference="CD-DEMO-1",
            counting=counting1,
            location=self.location,
            job=self.job,
            quantity_inventoried=10,
        )
        self.detail2 = CountingDetail.objects.create(
            reference="CD-DEMO-2",
            counting=counting2,
            location=self.location,
            job=self.job,
            quantity_inventoried=12,
        )

    def test_bulk_resolve_demo(self) -> None:
        """
        Démonstration de l'API de résolution en masse.
        """
        print("\n" + "="*60)
        print("DEMONSTRATION DE L'API DE RESOLUTION EN MASSE")
        print("="*60)

        # Création de plusieurs écarts avec différents états
        print("\nCreation de 4 ecarts de test...")

        # Écart 1: A un final_result → sera résolu
        ecart1 = EcartComptage.objects.create(
            reference="ECT-DEMO-1",
            inventory=self.inventory,
            total_sequences=2,
            resolved=False,
            final_result=150,
        )

        # Écart 2: A un final_result → sera résolu
        ecart2 = EcartComptage.objects.create(
            reference="ECT-DEMO-2",
            inventory=self.inventory,
            total_sequences=2,
            resolved=False,
            final_result=200,
        )

        # Écart 3: Pas de final_result → ne sera PAS résolu
        ecart3 = EcartComptage.objects.create(
            reference="ECT-DEMO-3",
            inventory=self.inventory,
            total_sequences=2,
            resolved=False,
            final_result=None,
        )

        # Écart 4: A un final_result → sera résolu
        ecart4 = EcartComptage.objects.create(
            reference="ECT-DEMO-4",
            inventory=self.inventory,
            total_sequences=2,
            resolved=False,
            final_result=75,
        )

        print(f"  - {ecart1.reference}: final_result={ecart1.final_result} -> SERA RESOLU")
        print(f"  - {ecart2.reference}: final_result={ecart2.final_result} -> SERA RESOLU")
        print(f"  - {ecart3.reference}: final_result={ecart3.final_result} -> NE SERA PAS RESOLU")
        print(f"  - {ecart4.reference}: final_result={ecart4.final_result} -> SERA RESOLU")

        # Appel de l'API
        print(f"\nAppel de l'API: PATCH /api/inventory/ecarts-comptage/bulk-resolve/{self.inventory.id}/")

        bulk_resolve_url = reverse(
            "ecart-comptage-bulk-resolve",
            kwargs={"inventory_id": self.inventory.id},
        )

        response = self.client.patch(bulk_resolve_url, data={}, format="json")

        print(f"Status HTTP: {response.status_code}")

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["resolved_count"], 3)  # 3 écarts avec final_result

        print(f"Message: {response.data['message']}")
        print(f"Nombre d'ecarts resolus: {response.data['data']['resolved_count']}")

        # Vérification de l'état des écarts
        print("\nVerification de l'etat des ecarts apres l'appel:")

        ecart1.refresh_from_db()
        ecart2.refresh_from_db()
        ecart3.refresh_from_db()
        ecart4.refresh_from_db()

        # Écarts avec final_result doivent être résolus
        self.assertTrue(ecart1.resolved)
        self.assertTrue(ecart2.resolved)
        self.assertTrue(ecart4.resolved)

        # Écart sans final_result ne doit pas être résolu
        self.assertFalse(ecart3.resolved)

        print(f"  - {ecart1.reference}: resolved={ecart1.resolved} -> OK")
        print(f"  - {ecart2.reference}: resolved={ecart2.resolved} -> OK")
        print(f"  - {ecart3.reference}: resolved={ecart3.resolved} -> OK")
        print(f"  - {ecart4.reference}: resolved={ecart4.resolved} -> OK")

        print("\nSUCCES: L'API fonctionne correctement!")
        print("3 ecarts ont ete marques comme resolus, 1 a ete ignore (pas de final_result)")
        print("="*60)
