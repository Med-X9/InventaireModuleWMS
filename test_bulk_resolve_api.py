#!/usr/bin/env python3
"""
Script de test pour l'API de résolution en masse des écarts de comptage.
Démontre l'utilisation de l'endpoint PATCH /api/inventory/ecarts-comptage/bulk-resolve/<inventory_id>/
"""

import os
import sys
import django

# Configuration Django pour les tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

# Ajout de testserver aux ALLOWED_HOSTS pour les tests
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

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


def demo_bulk_resolve_api():
    """
    Démonstration de l'API de résolution en masse des écarts de comptage.
    """
    print("Demarrage du test de l'API de resolution en masse des ecarts")
    print("=" * 60)

    # Configuration du client de test
    client = APIClient()
    user = get_user_model().objects.create_user(
        username="demo_tester",
        email="demo@test.com",
        password="DemoPass123!",
        type="Web",
    )
    client.force_authenticate(user=user)

    # Création des données de test
    print("Creation des donnees de test...")

    # Entrepôt et structure
    warehouse = Warehouse.objects.create(
        reference="WH-DEMO",
        warehouse_name="Entrepôt Démo",
        warehouse_type="CENTRAL",
        status="ACTIVE",
    )

    zone_type = ZoneType.objects.create(
        reference="ZT-DEMO",
        type_name="Zone Démo",
        status="ACTIVE",
    )
    zone = Zone.objects.create(
        reference="Z-DEMO",
        zone_name="Zone Démo",
        zone_type=zone_type,
        warehouse=warehouse,
        zone_status="ACTIVE",
    )
    sous_zone = SousZone.objects.create(
        reference="SZ-DEMO",
        sous_zone_name="Sous-zone Démo",
        zone=zone,
        sous_zone_status="ACTIVE",
    )
    location_type = LocationType.objects.create(
        reference="LT-DEMO",
        name="Type Démo",
    )
    location = Location.objects.create(
        reference="LOC-DEMO",
        location_reference="LOC-DEMO-01",
        sous_zone=sous_zone,
        location_type=location_type,
    )

    # Inventaire
    inventory = Inventory.objects.create(
        label="Inventaire Démo - Résolution en masse",
        date=timezone.now(),
        status="EN PREPARATION",
        inventory_type="GENERAL",
    )

    # Job
    job = Job.objects.create(
        reference="JOB-DEMO",
        status="EN ATTENTE",
        warehouse=warehouse,
        inventory=inventory,
    )

    # Deux comptages
    counting1 = Counting.objects.create(
        reference="CNT-DEMO-1",
        inventory=inventory,
        order=1,
        count_mode="en vrac",
    )
    counting2 = Counting.objects.create(
        reference="CNT-DEMO-2",
        inventory=inventory,
        order=2,
        count_mode="en vrac",
    )

    print("OK - Donnees de base creees")

    # Création de plusieurs écarts de comptage avec différents états
    print("\nCreation d'ecarts de comptage...")

    # Écart 1: A un final_result → sera résolu
    ecart1 = EcartComptage.objects.create(
        reference="ECT-DEMO-1",
        inventory=inventory,
        total_sequences=2,
        resolved=False,
        final_result=150,  # A un résultat final
    )

    # Écart 2: A un final_result → sera résolu
    ecart2 = EcartComptage.objects.create(
        reference="ECT-DEMO-2",
        inventory=inventory,
        total_sequences=2,
        resolved=False,
        final_result=200,  # A un résultat final
    )

    # Écart 3: Pas de final_result → ne sera PAS résolu
    ecart3 = EcartComptage.objects.create(
        reference="ECT-DEMO-3",
        inventory=inventory,
        total_sequences=2,
        resolved=False,
        final_result=None,  # Pas de résultat final
    )

    # Écart 4: A un final_result → sera résolu
    ecart4 = EcartComptage.objects.create(
        reference="ECT-DEMO-4",
        inventory=inventory,
        total_sequences=2,
        resolved=False,
        final_result=75,  # A un résultat final
    )

    print("OK - 4 ecarts crees:")
    print(f"   - {ecart1.reference}: final_result={ecart1.final_result} -> SERA RESOLU")
    print(f"   - {ecart2.reference}: final_result={ecart2.final_result} -> SERA RESOLU")
    print(f"   - {ecart3.reference}: final_result={ecart3.final_result} -> NE SERA PAS RESOLU")
    print(f"   - {ecart4.reference}: final_result={ecart4.final_result} -> SERA RESOLU")

    # Test de l'API
    print("\nTest de l'API de resolution en masse...")
    bulk_resolve_url = reverse(
        "ecart-comptage-bulk-resolve",
        kwargs={"inventory_id": inventory.id},
    )

    response = client.patch(bulk_resolve_url, data={}, format="json")

    print(f"Requete: PATCH {bulk_resolve_url}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("OK - API appelee avec succes!")
        print(f"Nombre d'ecarts resolus: {response.data['data']['resolved_count']}")
        print(f"Message: {response.data['message']}")

        # Vérification des résultats
        print("\nVerification des resultats...")

        ecart1.refresh_from_db()
        ecart2.refresh_from_db()
        ecart3.refresh_from_db()
        ecart4.refresh_from_db()

        print(f"   - {ecart1.reference}: resolved={ecart1.resolved} (attendu: True) OK" if ecart1.resolved else f"   - {ecart1.reference}: resolved={ecart1.resolved} (attendu: True) ERREUR")
        print(f"   - {ecart2.reference}: resolved={ecart2.resolved} (attendu: True) OK" if ecart2.resolved else f"   - {ecart2.reference}: resolved={ecart2.resolved} (attendu: True) ERREUR")
        print(f"   - {ecart3.reference}: resolved={ecart3.resolved} (attendu: False) OK" if not ecart3.resolved else f"   - {ecart3.reference}: resolved={ecart3.resolved} (attendu: False) ERREUR")
        print(f"   - {ecart4.reference}: resolved={ecart4.resolved} (attendu: True) OK" if ecart4.resolved else f"   - {ecart4.reference}: resolved={ecart4.resolved} (attendu: True) ERREUR")

        # Vérification du nombre
        resolved_count = sum([ecart1.resolved, ecart2.resolved, ecart3.resolved, ecart4.resolved])
        expected_count = 3  # écarts 1, 2 et 4

        if resolved_count == expected_count:
            print(f"\nSUCCES: {resolved_count} ecarts ont ete correctement resolus sur {expected_count} attendus!")
        else:
            print(f"\nECHEC: {resolved_count} ecarts resolus, {expected_count} attendus.")

    else:
        print(f"Erreur API: {response.data}")

    print("\n" + "=" * 60)
    print("Test termine!")


if __name__ == "__main__":
    demo_bulk_resolve_api()
