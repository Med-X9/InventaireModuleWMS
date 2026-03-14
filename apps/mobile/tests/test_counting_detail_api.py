"""
Tests unitaires pour l'API CountingDetail avec fonctionnalité UPSERT.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.inventory.models import Counting, CountingDetail, Job, Assigment, Inventory
from apps.masterdata.models import Product, Location, Warehouse, Account
import json

User = get_user_model()


class CountingDetailAPITestCase(TestCase):
    """
    Tests pour l'API CountingDetail avec UPSERT.
    """
    
    def setUp(self):
        """Configure les données de test."""
        self.client = APIClient()
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123',
            type='ADMIN'  # Type requis par le modèle
        )
        self.client.force_authenticate(user=self.user)
        
        # Créer un Warehouse (sans account si pas requis)
        self.warehouse = Warehouse.objects.create(
            warehouse_name='TEST_WAREHOUSE'
        )
        
        # Créer un inventaire
        self.inventory = Inventory.objects.create(
            reference='INV_TEST',
            status='EN_PREPARATION',
            date=timezone.now()  # DateTimeField, pas DateField
        )
        
        # Créer un comptage
        self.counting = Counting.objects.create(
            inventory=self.inventory,
            count_mode='par article',
            order=1,
            n_serie=False,
            dlc=False,
            n_lot=False
        )
        
        # Créer un job
        self.job = Job.objects.create(
            inventory=self.inventory,
            warehouse=self.warehouse,  # Champ requis
            status='EN_ATTENTE'
        )
        
        # Créer un produit
        self.product = Product.objects.create(
            barcode='TEST_PRODUCT_001',
            Short_Description='Produit Test'
        )
        
        # Créer une location
        self.location = Location.objects.create(
            code='LOC_TEST_001',
            location_reference='Location Test'
        )
        
        # Créer un assignment
        self.assignment = Assigment.objects.create(
            job=self.job,
            counting=self.counting,
            status='EN_ATTENTE'
        )
    
    def test_create_counting_detail(self):
        """Test 1: Création d'un nouveau CountingDetail."""
        data = [{
            'counting_id': self.counting.id,
            'location_id': self.location.id,
            'quantity_inventoried': 10,
            'assignment_id': self.assignment.id,
            'product_id': self.product.id
        }]
        
        response = self.client.post(
            f'/mobile/api/job/{self.job.id}/counting-detail/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['success'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['result']['action'], 'created')
        
        # Vérifier que le CountingDetail a été créé
        counting_detail = CountingDetail.objects.get(
            counting=self.counting,
            location=self.location,
            product=self.product
        )
        self.assertEqual(counting_detail.quantity_inventoried, 10)
    
    def test_update_counting_detail_upsert(self):
        """Test 2: Mise à jour d'un CountingDetail existant (UPSERT)."""
        # Créer un CountingDetail existant
        existing_detail = CountingDetail.objects.create(
            counting=self.counting,
            location=self.location,
            product=self.product,
            job=self.job,
            quantity_inventoried=5
        )
        
        # Envoyer une requête avec la même combinaison mais nouvelle quantité
        data = [{
            'counting_id': self.counting.id,
            'location_id': self.location.id,
            'quantity_inventoried': 15,  # Nouvelle quantité
            'assignment_id': self.assignment.id,
            'product_id': self.product.id
        }]
        
        response = self.client.post(
            f'/mobile/api/job/{self.job.id}/counting-detail/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['result']['action'], 'updated')
        
        # Vérifier que la quantité a été mise à jour
        existing_detail.refresh_from_db()
        self.assertEqual(existing_detail.quantity_inventoried, 15)
    
    def test_batch_upsert(self):
        """Test 3: UPSERT en lot (mix création et mise à jour)."""
        # Créer un CountingDetail existant
        CountingDetail.objects.create(
            counting=self.counting,
            location=self.location,
            product=self.product,
            job=self.job,
            quantity_inventoried=20
        )
        
        # Créer une deuxième location
        location2 = Location.objects.create(
            code='LOC_TEST_002',
            location_reference='Location Test 2'
        )
        
        data = [
            {
                'counting_id': self.counting.id,
                'location_id': self.location.id,
                'quantity_inventoried': 25,  # Mise à jour
                'assignment_id': self.assignment.id,
                'product_id': self.product.id
            },
            {
                'counting_id': self.counting.id,
                'location_id': location2.id,
                'quantity_inventoried': 5,  # Nouveau
                'assignment_id': self.assignment.id,
                'product_id': self.product.id
            }
        ]
        
        response = self.client.post(
            f'/mobile/api/job/{self.job.id}/counting-detail/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 2)
        
        actions = [r['result']['action'] for r in response.data['data']['results']]
        self.assertIn('updated', actions)
        self.assertIn('created', actions)
    
    def test_ignore_invalid_quantity(self):
        """Test 4: Ignorer les éléments sans quantité valide."""
        data = [
            {
                'counting_id': self.counting.id,
                'location_id': self.location.id,
                'quantity_inventoried': 30,  # Valide
                'assignment_id': self.assignment.id,
                'product_id': self.product.id
            },
            {
                'counting_id': self.counting.id,
                'location_id': self.location.id,
                'quantity_inventoried': 0,  # Invalide (ignoré)
                'assignment_id': self.assignment.id,
                'product_id': self.product.id
            },
            {
                'counting_id': self.counting.id,
                'location_id': self.location.id,
                # Pas de quantity_inventoried (ignoré)
                'assignment_id': self.assignment.id,
                'product_id': self.product.id
            }
        ]
        
        response = self.client.post(
            f'/mobile/api/job/{self.job.id}/counting-detail/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        # Seul l'élément avec quantité valide doit être traité
        self.assertEqual(len(response.data['data']['results']), 1)
    
    def test_final_result_calculation(self):
        """Test 5: Vérifier le calcul du résultat final (2 comptages ou plus)."""
        # Premier comptage
        data1 = [{
            'counting_id': self.counting.id,
            'location_id': self.location.id,
            'quantity_inventoried': 30,
            'assignment_id': self.assignment.id,
            'product_id': self.product.id
        }]
        
        response1 = self.client.post(
            f'/mobile/api/job/{self.job.id}/counting-detail/',
            data=data1,
            format='json'
        )
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        final_result_1 = response1.data['data']['results'][0]['result'].get('ecart_comptage', {}).get('final_result')
        self.assertIsNone(final_result_1, "Final result should be None with 1 count")
        
        # Deuxième comptage (même valeur)
        data2 = [{
            'counting_id': self.counting.id,
            'location_id': self.location.id,
            'quantity_inventoried': 30,  # Même valeur
            'assignment_id': self.assignment.id,
            'product_id': self.product.id
        }]
        
        response2 = self.client.post(
            f'/mobile/api/job/{self.job.id}/counting-detail/',
            data=data2,
            format='json'
        )
        
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        final_result_2 = response2.data['data']['results'][0]['result'].get('ecart_comptage', {}).get('final_result')
        self.assertEqual(final_result_2, 30, "Final result should be 30 (2 identical counts)")

