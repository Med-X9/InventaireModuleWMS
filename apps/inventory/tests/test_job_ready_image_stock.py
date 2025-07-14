"""
Tests pour la logique de job ready avec image de stock
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import json

from ..models import Inventory, Job, Counting, Assigment
from apps.masterdata.models import Warehouse, Account, Location
from apps.users.models import UserApp
from ..usecases.job_ready import JobReadyUseCase

User = get_user_model()

class JobReadyImageStockTestCase(TestCase):
    """Tests pour la logique de job ready avec image de stock"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.client = APIClient()
        
        # Créer un utilisateur pour l'authentification
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Créer les données de base
        self.account = Account.objects.create(
            name='Test Account',
            code='TEST001'
        )
        
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='WH001',
            account=self.account
        )
        
        # Créer un inventaire avec image de stock
        self.inventory_image_stock = Inventory.objects.create(
            label='Test Inventory Image Stock',
            date=timezone.now(),
            status='EN PREPARATION'
        )
        
        # Créer les comptages : 1er = image de stock, 2ème = en vrac
        self.counting1_image_stock = Counting.objects.create(
            order=1,
            count_mode='image de stock',
            inventory=self.inventory_image_stock
        )
        
        self.counting2_en_vrac = Counting.objects.create(
            order=2,
            count_mode='en vrac',
            inventory=self.inventory_image_stock
        )
        
        # Créer un job avec statut AFFECTE
        self.job_image_stock = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory_image_stock
        )
        
        # Créer une session mobile
        self.session = UserApp.objects.create(
            username='test_session',
            type='Mobile'
        )
        
        # Créer un inventaire normal pour comparaison
        self.inventory_normal = Inventory.objects.create(
            label='Test Inventory Normal',
            date=timezone.now(),
            status='EN PREPARATION'
        )
        
        self.counting1_normal = Counting.objects.create(
            order=1,
            count_mode='en vrac',
            inventory=self.inventory_normal
        )
        
        self.counting2_normal = Counting.objects.create(
            order=2,
            count_mode='par article',
            inventory=self.inventory_normal
        )
        
        self.job_normal = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory_normal
        )
    
    def test_job_ready_with_image_stock_valid(self):
        """Test de mise en prêt réussie avec image de stock (configuration valide)"""
        
        # Créer une affectation pour le 2ème comptage seulement
        assignment2 = Assigment.objects.create(
            job=self.job_image_stock,
            counting=self.counting2_en_vrac,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        # Tester via l'API
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_image_stock.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['ready_jobs_count'], 1)
        
        # Vérifier que les statuts ont été mis à jour
        self.job_image_stock.refresh_from_db()
        assignment2.refresh_from_db()
        
        self.assertEqual(self.job_image_stock.status, 'PRET')
        self.assertEqual(assignment2.status, 'PRET')
        self.assertIsNotNone(self.job_image_stock.pret_date)
        self.assertIsNotNone(assignment2.pret_date)
    
    def test_job_ready_with_image_stock_invalid_second_counting(self):
        """Test d'erreur avec 2ème comptage aussi image de stock"""
        
        # Créer un 2ème comptage image de stock
        counting2_invalid = Counting.objects.create(
            order=2,
            count_mode='image de stock',
            inventory=self.inventory_image_stock
        )
        
        # Créer une affectation pour le 2ème comptage image de stock
        assignment2_invalid = Assigment.objects.create(
            job=self.job_image_stock,
            counting=counting2_invalid,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        # Tester via l'API
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_image_stock.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('2ème comptage ne peut pas être image de stock', response.data['message'])
    
    def test_job_ready_with_image_stock_no_second_assignment(self):
        """Test d'erreur sans affectation du 2ème comptage"""
        
        # Ne pas créer d'affectation pour le 2ème comptage
        
        # Tester via l'API
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_image_stock.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('2ème comptage non affecté', response.data['message'])
    
    def test_job_ready_normal_configuration(self):
        """Test de mise en prêt réussie avec configuration normale"""
        
        # Créer les affectations pour les deux comptages
        assignment1 = Assigment.objects.create(
            job=self.job_normal,
            counting=self.counting1_normal,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        assignment2 = Assigment.objects.create(
            job=self.job_normal,
            counting=self.counting2_normal,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        # Tester via l'API
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_normal.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['ready_jobs_count'], 1)
        
        # Vérifier que les statuts ont été mis à jour
        self.job_normal.refresh_from_db()
        assignment1.refresh_from_db()
        assignment2.refresh_from_db()
        
        self.assertEqual(self.job_normal.status, 'PRET')
        self.assertEqual(assignment1.status, 'PRET')
        self.assertEqual(assignment2.status, 'PRET')
    
    def test_job_ready_normal_configuration_missing_first(self):
        """Test d'erreur avec configuration normale mais 1er comptage manquant"""
        
        # Créer seulement l'affectation pour le 2ème comptage
        assignment2 = Assigment.objects.create(
            job=self.job_normal,
            counting=self.counting2_normal,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        # Tester via l'API
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_normal.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('comptages non affectés', response.data['message'])
    
    def test_job_ready_use_case_direct(self):
        """Test direct du use case avec image de stock"""
        
        # Créer une affectation pour le 2ème comptage seulement
        assignment2 = Assigment.objects.create(
            job=self.job_image_stock,
            counting=self.counting2_en_vrac,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        # Tester directement le use case
        use_case = JobReadyUseCase()
        
        try:
            result = use_case.execute([self.job_image_stock.id])
            
            self.assertTrue(result['success'])
            self.assertEqual(result['ready_jobs_count'], 1)
            self.assertEqual(len(result['updated_assignments']), 1)
            
            # Vérifier les changements
            self.job_image_stock.refresh_from_db()
            assignment2.refresh_from_db()
            
            self.assertEqual(self.job_image_stock.status, 'PRET')
            self.assertEqual(assignment2.status, 'PRET')
            
        except Exception as e:
            self.fail(f"Le use case a levé une exception inattendue: {e}")
    
    def test_job_ready_mixed_jobs(self):
        """Test avec plusieurs jobs de configurations différentes"""
        
        # Créer un job avec image de stock
        job_image_stock2 = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory_image_stock
        )
        
        # Créer une affectation pour le 2ème comptage du job image de stock
        assignment_image_stock = Assigment.objects.create(
            job=job_image_stock2,
            counting=self.counting2_en_vrac,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        # Créer les affectations pour le job normal
        assignment1_normal = Assigment.objects.create(
            job=self.job_normal,
            counting=self.counting1_normal,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        assignment2_normal = Assigment.objects.create(
            job=self.job_normal,
            counting=self.counting2_normal,
            session=self.session,
            status='AFFECTE',
            affecte_date=timezone.now()
        )
        
        # Tester avec les deux jobs
        url = reverse('jobs-ready')
        data = {
            'job_ids': [job_image_stock2.id, self.job_normal.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['ready_jobs_count'], 2)
        
        # Vérifier que tous les statuts ont été mis à jour
        job_image_stock2.refresh_from_db()
        self.job_normal.refresh_from_db()
        assignment_image_stock.refresh_from_db()
        assignment1_normal.refresh_from_db()
        assignment2_normal.refresh_from_db()
        
        self.assertEqual(job_image_stock2.status, 'PRET')
        self.assertEqual(self.job_normal.status, 'PRET')
        self.assertEqual(assignment_image_stock.status, 'PRET')
        self.assertEqual(assignment1_normal.status, 'PRET')
        self.assertEqual(assignment2_normal.status, 'PRET') 