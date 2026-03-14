"""
Tests pour l'API de résultats d'inventaire par entrepôt.
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
    Setting,
)
from apps.masterdata.models import (
    Account,
    Warehouse,
    ZoneType,
    Zone,
    SousZone,
    LocationType,
    Location,
)


class InventoryResultAPIViewTestCase(TestCase):
    """
    Suite de tests pour l'endpoint /inventory/<inventory_id>/warehouses/<warehouse_id>/results/.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="result_tester",
            email="result@test.com",
            password="StrongPass123!",
            type="Web",
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            reference="ACC-TEST",
            account_name="Compte Test",
            account_statuts="ACTIVE",
        )
        self.warehouse = Warehouse.objects.create(
            reference="WH-TEST",
            warehouse_name="Entrepôt Test",
            warehouse_type="CENTRAL",
            status="ACTIVE",
        )
        self.inventory = Inventory.objects.create(
            label="Inventaire Test",
            date=timezone.now(),
            status="EN PREPARATION",
            inventory_type="GENERAL",
        )
        Setting.objects.create(
            reference="SET-RESULT-TEST",
            account=self.account,
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        # Création des structures d'emplacement minimales.
        zone_type = ZoneType.objects.create(
            reference="ZT-01",
            type_name="Zone test",
            status="ACTIVE",
        )
        zone = Zone.objects.create(
            reference="Z-01",
            zone_name="Zone 1",
            zone_type=zone_type,
            warehouse=self.warehouse,
            zone_status="ACTIVE",
        )
        sous_zone = SousZone.objects.create(
            reference="SZ-01",
            sous_zone_name="Sous-zone 1",
            zone=zone,
            sous_zone_status="ACTIVE",
        )
        location_type = LocationType.objects.create(
            reference="LT-01",
            name="Type emplacement",
        )
        self.location_a = Location.objects.create(
            reference="LOC-A",
            location_reference="A-01-01",
            sous_zone=sous_zone,
            location_type=location_type,
        )
        self.location_b = Location.objects.create(
            reference="LOC-B",
            location_reference="B-02-03",
            sous_zone=sous_zone,
            location_type=location_type,
        )

        # Comptages (mode unique en vrac).
        self.countings = {
            order: Counting.objects.create(
                reference=f"CNT-RESULT-{order}",
                inventory=self.inventory,
                order=order,
                count_mode="en vrac",
            )
            for order in range(1, 6)
        }

        # Jobs par emplacement.
        self.job_a = Job.objects.create(
            reference="JOB-RESULT-A",
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=self.inventory,
        )
        self.job_b = Job.objects.create(
            reference="JOB-RESULT-B",
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        # Détails de comptage : emplacement A (3 comptages), emplacement B (5 comptages).
        CountingDetail.objects.create(
            reference="CD-A-1",
            counting=self.countings[1],
            location=self.location_a,
            job=self.job_a,
            quantity_inventoried=120,
        )
        CountingDetail.objects.create(
            reference="CD-A-2",
            counting=self.countings[2],
            location=self.location_a,
            job=self.job_a,
            quantity_inventoried=118,
        )
        CountingDetail.objects.create(
            reference="CD-A-3",
            counting=self.countings[3],
            location=self.location_a,
            job=self.job_a,
            quantity_inventoried=121,
        )

        quantities_b = [80, 79, 78, 81, 81]
        for order, quantity in enumerate(quantities_b, start=1):
            CountingDetail.objects.create(
                reference=f"CD-B-{order}",
                counting=self.countings[order],
                location=self.location_b,
                job=self.job_b,
                quantity_inventoried=quantity,
            )

        self.url = reverse(
            "inventory-warehouse-results",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )

    def test_inventory_results_standardized_format_en_vrac(self) -> None:
        """
        Vérifie que le format standardisé est respecté en mode 'en vrac'
        avec complétion des comptages manquants à None.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 2)

        entry_a = next(
            item for item in response.data["data"] if item["location"] == "A-01-01"
        )
        self.assertNotIn("product", entry_a)
        self.assertEqual(entry_a["location_id"], self.location_a.id)
        self.assertEqual(entry_a["job_id"], self.job_a.id)
        self.assertEqual(entry_a["1er comptage"], 120)
        self.assertEqual(entry_a["2er comptage"], 118)
        self.assertEqual(entry_a["ecart_1_2"], -2)
        self.assertEqual(entry_a["3er comptage"], 121)
        self.assertEqual(entry_a["ecart_2_3"], 3)
        self.assertIsNone(entry_a["4er comptage"])
        self.assertIsNone(entry_a["ecart_3_4"])
        self.assertIsNone(entry_a["5er comptage"])
        self.assertIsNone(entry_a["ecart_4_5"])
        self.assertEqual(entry_a["final_result"], 121)
        # EcartComptage est optionnel dans ce scénario de test (peut être absent)
        # donc on ne vérifie pas ecart_comptage_id et resolved ici.
        # Si resolved est présent, il doit être un booléen.
        if "resolved" in entry_a:
            self.assertIsInstance(entry_a["resolved"], bool)

        entry_b = next(
            item for item in response.data["data"] if item["location"] == "B-02-03"
        )
        self.assertEqual(entry_b["location_id"], self.location_b.id)
        self.assertEqual(entry_b["job_id"], self.job_b.id)
        self.assertEqual(entry_b["1er comptage"], 80)
        self.assertEqual(entry_b["ecart_1_2"], -1)
        self.assertEqual(entry_b["4er comptage"], 81)
        self.assertEqual(entry_b["ecart_3_4"], 3)
        self.assertEqual(entry_b["5er comptage"], 81)
        self.assertEqual(entry_b["ecart_4_5"], 0)
        self.assertEqual(entry_b["final_result"], 81)
        # Si resolved est présent, il doit être un booléen.
        if "resolved" in entry_b:
            self.assertIsInstance(entry_b["resolved"], bool)

    def test_pagination_with_startrow_endrow(self) -> None:
        """
        Test de pagination avec startRow=20 et endRow=40 (1-indexed).
        Vérifie que la pagination fonctionne correctement avec l'authentification par login.
        """
        # Créer l'utilisateur mohammed avec le mot de passe admin1234
        User = get_user_model()
        user_mohammed, created = User.objects.get_or_create(
            username="mohammed",
            defaults={
                "email": "mohammed@test.com",
                "password": "admin1234",
                "type": "Web",
            }
        )
        if not created:
            # Si l'utilisateur existe déjà, mettre à jour le mot de passe
            user_mohammed.set_password("admin1234")
            user_mohammed.save()
        
        # Authentifier avec l'utilisateur mohammed
        # Note: Pour APIClient de DRF, force_authenticate() est la méthode recommandée
        # car login() est conçu pour les sessions Django classiques, pas pour les APIs REST
        self.client.force_authenticate(user=user_mohammed)
        
        # Vérifier que l'utilisateur a bien le bon mot de passe
        self.assertTrue(user_mohammed.check_password("admin1234"), "Le mot de passe devrait être correct")
        
        # Créer plus de données pour tester la pagination (au moins 40 lignes)
        # On va créer 50 emplacements avec des CountingDetails
        zone_type = ZoneType.objects.first()
        zone = Zone.objects.first()
        sous_zone = SousZone.objects.first()
        location_type = LocationType.objects.first()
        
        # Créer 50 emplacements supplémentaires
        locations = []
        jobs = []
        for i in range(1, 51):  # 50 emplacements
            location = Location.objects.create(
                reference=f"LOC-PAG-{i:03d}",
                location_reference=f"PAG-{i:03d}",
                sous_zone=sous_zone,
                location_type=location_type,
            )
            locations.append(location)
            
            job = Job.objects.create(
                reference=f"JOB-PAG-{i:03d}",
                status="EN ATTENTE",
                warehouse=self.warehouse,
                inventory=self.inventory,
            )
            jobs.append(job)
            
            # Créer un CountingDetail pour chaque emplacement
            CountingDetail.objects.create(
                reference=f"CD-PAG-{i:03d}",
                counting=self.countings[1],
                location=location,
                job=job,
                quantity_inventoried=100 + i,  # Quantités différentes pour chaque ligne
            )
        
        # Test de pagination : startRow=20, endRow=40
        # Cela devrait retourner les lignes 21 à 40 (en 1-indexed)
        url = reverse(
            "inventory-warehouse-results",
            kwargs={
                "inventory_id": self.inventory.id,
                "warehouse_id": self.warehouse.id,
            },
        )
        
        response = self.client.get(
            url,
            {
                "inventory_id": self.inventory.id,
                "store_id": self.warehouse.id,
                "startRow": 20,
                "endRow": 40,
            }
        )
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le format de la réponse
        if "data" in response.data:
            # Format QueryModel/DataTable
            data = response.data.get("data", [])
            records_total = response.data.get("recordsTotal", 0)
            records_filtered = response.data.get("recordsFiltered", 0)
            
            # On devrait avoir 20 lignes (lignes 21-40)
            self.assertEqual(len(data), 20, f"Attendu 20 lignes, reçu {len(data)}")
            
            # Vérifier que le total est correct (au moins 50 lignes + les 2 existantes = 52)
            self.assertGreaterEqual(records_total, 52, "Le total devrait être au moins 52")
            self.assertGreaterEqual(records_filtered, 52, "Le total filtré devrait être au moins 52")
            
        elif "results" in response.data:
            # Format REST API
            results = response.data.get("results", [])
            count = response.data.get("count", 0)
            start_row = response.data.get("startRow", 0)
            end_row = response.data.get("endRow", 0)
            
            # On devrait avoir 20 lignes (lignes 21-40)
            self.assertEqual(len(results), 20, f"Attendu 20 lignes, reçu {len(results)}")
            
            # Vérifier les valeurs de pagination retournées
            self.assertEqual(start_row, 20, "startRow devrait être 20 (1-indexed)")
            self.assertEqual(end_row, 40, "endRow devrait être 40 (1-indexed)")
            
            # Vérifier que le total est correct
            self.assertGreaterEqual(count, 52, "Le total devrait être au moins 52")
        
        # Vérifier que les données retournées correspondent bien à la pagination
        # (les lignes 21-40 ne devraient pas inclure les premières lignes)
        if "data" in response.data:
            data = response.data.get("data", [])
        else:
            data = response.data.get("results", [])
        
        # Vérifier qu'on n'a pas les premières lignes (A-01-01 et B-02-03)
        location_refs = [item.get("location", "") for item in data]
        self.assertNotIn("A-01-01", location_refs, "La première ligne ne devrait pas être dans cette page")
        self.assertNotIn("B-02-03", location_refs, "La deuxième ligne ne devrait pas être dans cette page")
        
        # Vérifier qu'on a bien des lignes de pagination (PAG-021 à PAG-040)
        pag_locations = [ref for ref in location_refs if ref.startswith("PAG-")]
        self.assertGreater(len(pag_locations), 0, "On devrait avoir des lignes PAG- dans cette page")

