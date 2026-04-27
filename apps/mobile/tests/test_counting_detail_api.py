"""
Tests unitaires pour l'API CountingDetail avec fonctionnalité UPSERT.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.inventory.models import Counting, CountingDetail, Job, Assigment, Inventory, JobDetail
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
        # JobDetail requis pour la validation counting-detail (job, counting, location)
        JobDetail.objects.create(
            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
            location=self.location,
            job=self.job,
            counting=self.counting,
            status='EN_ATTENTE',
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
        JobDetail.objects.create(
            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
            location=location2,
            job=self.job,
            counting=self.counting,
            status='EN_ATTENTE',
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

    def test_counting_order_2_then_1_consensus_and_sequence_order(self):
        """
        Test 6: Envoi 2e comptage puis 1er comptage (même product/location).
        Vérifie que le tri des séquences par sequence_number donne le bon consensus
        et que final_result / ecart_with_previous sont cohérents.
        """
        from apps.inventory.models import ComptageSequence, EcartComptage
        # Deuxième comptage (order=2)
        counting_2 = Counting.objects.create(
            inventory=self.inventory,
            count_mode='par article',
            order=2,
            n_serie=False,
            dlc=False,
            n_lot=False,
        )
        assignment_2 = Assigment.objects.create(
            job=self.job,
            counting=counting_2,
            status='EN_ATTENTE',
        )
        JobDetail.objects.create(
            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
            location=self.location,
            job=self.job,
            counting=counting_2,
            status='EN_ATTENTE',
        )
        # Envoyer d'abord 2e comptage (q=50), puis 1er comptage (q=50) -> consensus 50
        data = [
            {
                'counting_id': counting_2.id,
                'location_id': self.location.id,
                'quantity_inventoried': 50,
                'assignment_id': assignment_2.id,
                'product_id': self.product.id,
            },
            {
                'counting_id': self.counting.id,
                'location_id': self.location.id,
                'quantity_inventoried': 50,
                'assignment_id': self.assignment.id,
                'product_id': self.product.id,
            },
        ]
        response = self.client.post(
            f'/mobile/api/job/{self.job.id}/counting-detail/',
            data=data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 2)
        # Dernier résultat (1er comptage traité en 2e) doit avoir final_result=50 (consensus)
        last_ecart = response.data['data']['results'][-1]['result'].get('ecart_comptage', {})
        self.assertEqual(last_ecart.get('final_result'), 50)
        # Vérifier en base : un seul EcartComptage, 2 ComptageSequence triées par sequence_number
        ecarts = EcartComptage.objects.filter(inventory=self.inventory)
        self.assertEqual(ecarts.count(), 1)
        sequences = list(
            ComptageSequence.objects.filter(ecart_comptage=ecarts.first()).order_by('sequence_number')
        )
        self.assertEqual(len(sequences), 2)
        self.assertEqual(sequences[0].sequence_number, 1)
        self.assertEqual(sequences[1].sequence_number, 2)
        # Premier enregistré (2e comptage) : quantity 50, ecart_with_previous None
        self.assertEqual(sequences[0].quantity, 50)
        self.assertIsNone(sequences[0].ecart_with_previous)
        # Second (1er comptage) : quantity 50, ecart_with_previous 0
        self.assertEqual(sequences[1].quantity, 50)
        self.assertEqual(sequences[1].ecart_with_previous, 0)

    def test_update_second_counting_recalculates_final_result(self):
        """
        Test 7: Créer 2 comptages puis mettre à jour la quantité du 2e via un 2e POST.
        Vérifier que EcartComptage.final_result et les ComptageSequence sont recalculés.
        """
        from apps.inventory.models import ComptageSequence, EcartComptage
        counting_2 = Counting.objects.create(
            inventory=self.inventory,
            count_mode='par article',
            order=2,
            n_serie=False,
            dlc=False,
            n_lot=False,
        )
        assignment_2 = Assigment.objects.create(
            job=self.job,
            counting=counting_2,
            status='EN_ATTENTE',
        )
        JobDetail.objects.create(
            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
            location=self.location,
            job=self.job,
            counting=counting_2,
            status='EN_ATTENTE',
        )
        # 1er comptage q=20, 2e comptage q=20 -> consensus 20
        batch1 = [
            {'counting_id': self.counting.id, 'location_id': self.location.id, 'quantity_inventoried': 20,
             'assignment_id': self.assignment.id, 'product_id': self.product.id},
            {'counting_id': counting_2.id, 'location_id': self.location.id, 'quantity_inventoried': 20,
             'assignment_id': assignment_2.id, 'product_id': self.product.id},
        ]
        r1 = self.client.post(f'/mobile/api/job/{self.job.id}/counting-detail/', data=batch1, format='json')
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        ecart = EcartComptage.objects.filter(inventory=self.inventory).first()
        self.assertIsNotNone(ecart)
        self.assertEqual(ecart.final_result, 20)
        # Mise à jour du 2e comptage : 20 -> 22. Pas de consensus (20 != 22) -> final_result doit devenir None
        batch2 = [{
            'counting_id': counting_2.id,
            'location_id': self.location.id,
            'quantity_inventoried': 22,
            'assignment_id': assignment_2.id,
            'product_id': self.product.id,
        }]
        r2 = self.client.post(f'/mobile/api/job/{self.job.id}/counting-detail/', data=batch2, format='json')
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        ecart.refresh_from_db()
        # Règles métier : 2 comptages différents -> pas de consensus
        self.assertIsNone(ecart.final_result)
        sequences = list(
            ComptageSequence.objects.filter(ecart_comptage=ecart).order_by('sequence_number')
        )
        self.assertEqual(len(sequences), 2)
        self.assertEqual(sequences[0].quantity, 20)
        self.assertEqual(sequences[1].quantity, 22)
        self.assertEqual(sequences[1].ecart_with_previous, 2)

