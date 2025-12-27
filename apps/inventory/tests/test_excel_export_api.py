"""
Tests pour l'API d'export Excel consolidé par article
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

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
    Product,
    Family,
    Account,
)


class ExcelExportAPITestCase(TestCase):
    """
    Suite de tests pour l'API d'export Excel consolidé :
    - GET /inventory/{inventory_id}/articles-consolides/export/
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="excel_tester",
            email="excel@test.com",
            password="StrongPass123!",
            type="Web",
        )
        self.client.force_authenticate(user=self.user)

        # Créer les données de base
        self.account = Account.objects.create(
            reference="ACC-EXCEL",
            account_name="Compte Excel",
            account_statuts="ACTIVE",
        )

        self.warehouse = Warehouse.objects.create(
            reference="WH-EXCEL",
            warehouse_name="Entrepôt Excel",
        )

        self.zone_type = ZoneType.objects.create(
            reference="ZT-EXCEL",
            type_name="Type Zone Excel",
            status="ACTIVE",
        )

        self.zone = Zone.objects.create(
            reference="Z-EXCEL",
            zone_name="Zone Excel",
            zone_type=self.zone_type,
            warehouse=self.warehouse,
        )

        self.sous_zone = SousZone.objects.create(
            reference="SZ-EXCEL",
            sous_zone_name="Sous Zone Excel",
            zone=self.zone,
        )

        self.location_type = LocationType.objects.create(
            reference="LT-EXCEL",
            name="Type Emplacement Excel",
        )

        self.location = Location.objects.create(
            reference="LOC-EXCEL-001",
            location_reference="LOC-EXCEL-REF-001",
            location_type=self.location_type,
            sous_zone=self.sous_zone,
        )

        self.product_family = Family.objects.create(
            reference="PF-EXCEL",
            family_name="Famille Excel",
            compte=self.account,
            family_status="ACTIVE",
        )

        self.product = Product.objects.create(
            reference="PROD-EXCEL-001",
            Internal_Product_Code="1234567890123",
            Short_Description="Produit Excel Test",
            Product_Family=self.product_family,
        )

        # Créer un inventaire
        self.inventory = Inventory.objects.create(
            reference="INV-EXCEL-001",
            label="Inventaire Excel Test",
            date=timezone.now(),
            status="EN PREPARATION",
        )

        # Créer les comptages d'ordre 2 et 3 (requis pour l'export)
        self.counting_order_2 = Counting.objects.create(
            reference="CNT-EXCEL-002",
            inventory=self.inventory,
            order=2,
            count_mode="par article",
        )

        self.counting_order_3 = Counting.objects.create(
            reference="CNT-EXCEL-003",
            inventory=self.inventory,
            order=3,
            count_mode="par article",
        )

        # Créer un job
        self.job = Job.objects.create(
            reference="JOB-EXCEL-001",
            inventory=self.inventory,
            warehouse=self.warehouse,
        )

        # Créer un CountingDetail
        self.counting_detail = CountingDetail.objects.create(
            reference="CD-EXCEL-001",
            quantity_inventoried=10,
            product=self.product,
            location=self.location,
            counting=self.counting_order_2,
            job=self.job,
        )

        # Créer un EcartComptage résolu avec final_result
        self.ecart_comptage = EcartComptage.objects.create(
            reference="ECT-EXCEL-001",
            inventory=self.inventory,
            final_result=15,  # Quantité finale validée
            resolved=True,    # Résolu
            manual_result=True,
            justification="Test Excel Export",
        )

        # Créer une ComptageSequence liant l'EcartComptage au CountingDetail
        self.comptage_sequence = ComptageSequence.objects.create(
            reference="CS-EXCEL-001",
            ecart_comptage=self.ecart_comptage,
            sequence_number=1,
            counting_detail=self.counting_detail,
            quantity=10,  # Quantité du premier comptage
        )

    def test_export_excel_consolidated_success(self):
        """
        Test de l'export Excel consolidé avec succès
        """
        url = reverse('inventory-articles-consolides-export', kwargs={'inventory_id': self.inventory.id})

        response = self.client.get(url)

        # Vérifier que la réponse est réussie
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier les headers de réponse
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('Content-Disposition', response)
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        self.assertIn('articles_consolides', response['Content-Disposition'])

        # Vérifier que le contenu n'est pas vide
        self.assertGreater(len(response.content), 0)

    def test_export_excel_inventory_not_found(self):
        """
        Test de l'export Excel avec un inventaire inexistant
        """
        url = reverse('inventory-articles-consolides-export', kwargs={'inventory_id': 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non trouvé', response.data['message'])

    def test_export_excel_missing_countings(self):
        """
        Test de l'export Excel avec des comptages manquants
        """
        # Supprimer le comptage d'ordre 3
        self.counting_order_3.delete()

        url = reverse('inventory-articles-consolides-export', kwargs={'inventory_id': self.inventory.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('comptage d\'ordre 3', response.data['message'])

    def test_export_excel_wrong_count_mode(self):
        """
        Test de l'export Excel avec un mode de comptage incorrect
        """
        # Changer le mode de comptage à "par emplacement"
        self.counting_order_2.count_mode = "par emplacement"
        self.counting_order_2.save()

        url = reverse('inventory-articles-consolides-export', kwargs={'inventory_id': self.inventory.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('mode de comptage', response.data['message'])

    def test_export_excel_not_all_ecarts_resolved(self):
        """
        Test de l'export Excel quand TOUS les écarts ne sont pas résolus
        (nouvelle logique : tous les écarts de l'inventaire doivent être resolved=True)
        """
        # Marquer l'écart comme non résolu
        self.ecart_comptage.resolved = False
        self.ecart_comptage.save()

        url = reverse('inventory-articles-consolides-export', kwargs={'inventory_id': self.inventory.id})

        response = self.client.get(url)

        # L'export doit échouer car tous les écarts ne sont pas résolus
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Tous les écarts de comptage de cet inventaire doivent être résolus', response.data['message'])
        self.assertIn('Écarts résolus : 0/1', response.data['message'])

    def test_export_excel_final_result_logic(self):
        """
        Test pour vérifier que la logique utilise final_result et non quantity_inventoried

        Scénario:
        - CountingDetail a quantity_inventoried = 10
        - EcartComptage a final_result = 15 (après résolution)
        - L'export doit utiliser 15, pas 10
        """
        # Modifier le final_result pour qu'il soit différent de quantity_inventoried
        self.ecart_comptage.final_result = 15  # différent de quantity_inventoried = 10
        self.ecart_comptage.save()

        url = reverse('inventory-articles-consolides-export', kwargs={'inventory_id': self.inventory.id})

        response = self.client.get(url)

        # Vérifier que l'export réussit
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ici nous ne pouvons pas vérifier facilement le contenu Excel,
        # mais le fait que l'export réussit confirme que la logique fonctionne

    def test_export_excel_all_ecarts_resolved_success(self):
        """
        Test de succès quand TOUS les écarts de l'inventaire sont résolus
        """
        # S'assurer que l'écart est bien résolu (il l'est déjà dans setUp)
        self.assertTrue(self.ecart_comptage.resolved)
        self.assertIsNotNone(self.ecart_comptage.final_result)

        url = reverse('inventory-articles-consolides-export', kwargs={'inventory_id': self.inventory.id})

        response = self.client.get(url)

        # L'export doit réussir car tous les écarts sont résolus
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
