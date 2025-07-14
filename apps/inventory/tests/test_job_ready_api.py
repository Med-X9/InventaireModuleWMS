"""
Tests pour l'API de mise en prêt des jobs affectés
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

User = get_user_model()

class JobReadyAPITestCase(TestCase):
    """Tests pour l'API de mise en prêt des jobs affectés"""
    
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
        
        self.inventory = Inventory.objects.create(
            label='Test Inventory',
            date=timezone.now(),
            status='EN PREPARATION'
        )
        
        # Créer des jobs avec différents statuts
        self.job_affecte = Job.objects.create(
            status='VALIDE',  # Le modèle Job n'a que 3 statuts
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        self.job_affecte2 = Job.objects.create(
            status='VALIDE',  # Le modèle Job n'a que 3 statuts
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        self.job_en_attente = Job.objects.create(
            status='EN ATTENTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        self.job_valide = Job.objects.create(
            status='VALIDE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        # Créer des affectations avec différents statuts
        from ..models import Assigment, Counting
        
        # Créer des comptages
        self.counting1 = Counting.objects.create(
            order=1,
            count_mode='image stock',
            inventory=self.inventory
        )
        
        self.counting2 = Counting.objects.create(
            order=2,
            count_mode='en vrac',
            inventory=self.inventory
        )
        
        # Affectation avec statut AFFECTE
        self.assignment_affecte = Assigment.objects.create(
            job=self.job_affecte,
            counting=self.counting1,
            status='AFFECTE'
        )
        
        # Job avec affectation PRET
        self.job_pret = Job.objects.create(
            status='VALIDE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        # Affectation avec statut PRET
        self.assignment_pret = Assigment.objects.create(
            job=self.job_pret,
            counting=self.counting1,
            status='PRET'
        )
    
    def test_make_jobs_ready_success(self):
        """Test de mise en prêt réussie de jobs affectés"""
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_affecte.id, self.job_affecte2.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Jobs mis au statut PRET avec succès')
        self.assertEqual(response.data['data']['ready_jobs_count'], 2)
        
        # Vérifier que les statuts des affectations ont été mis à jour
        self.assignment_affecte.refresh_from_db()
        self.assertEqual(self.assignment_affecte.status, 'PRET')
        self.assertIsNotNone(self.assignment_affecte.pret_date)
    
    def test_make_jobs_ready_invalid_status(self):
        """Test d'erreur lors de la mise en prêt de jobs non affectés"""
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_en_attente.id, self.job_valide.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Seuls les jobs affectés peuvent être mis au statut PRET', response.data['message'])
    
    def test_make_jobs_ready_mixed_status(self):
        """Test d'erreur avec un mélange de statuts valides et invalides"""
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_affecte.id, self.job_en_attente.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Seuls les jobs affectés peuvent être mis au statut PRET', response.data['message'])
    
    def test_make_jobs_ready_jobs_not_found(self):
        """Test avec des IDs de jobs inexistants"""
        url = reverse('jobs-ready')
        data = {
            'job_ids': [99999, 88888]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Jobs non trouvés', response.data['message'])
    
    def test_make_jobs_ready_empty_list(self):
        """Test avec une liste vide de jobs"""
        url = reverse('jobs-ready')
        data = {
            'job_ids': []
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_make_jobs_ready_invalid_data(self):
        """Test avec des données invalides"""
        url = reverse('jobs-ready')
        data = {
            'job_ids': 'invalid_data'  # Devrait être une liste
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_make_jobs_ready_already_ready(self):
        """Test de mise en prêt d'un job déjà au statut PRET"""
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_pret.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Seuls les jobs affectés peuvent être mis au statut PRET', response.data['message'])
    
    def test_make_jobs_ready_single_job(self):
        """Test de mise en prêt d'un seul job"""
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_affecte.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['ready_jobs_count'], 1)
        
        # Vérifier que le statut de l'affectation a été mis à jour
        self.assignment_affecte.refresh_from_db()
        self.assertEqual(self.assignment_affecte.status, 'PRET')
    
    def test_make_jobs_ready_multiple_jobs(self):
        """Test de mise en prêt de plusieurs jobs en une seule requête"""
        # Créer quelques jobs supplémentaires avec le statut AFFECTE
        job_affecte3 = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        job_affecte4 = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        job_affecte5 = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        url = reverse('jobs-ready')
        data = {
            'job_ids': [self.job_affecte.id, self.job_affecte2.id, job_affecte3.id, job_affecte4.id, job_affecte5.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['ready_jobs_count'], 5)
        
        # Vérifier que tous les jobs ont été mis à jour
        self.job_affecte.refresh_from_db()
        self.job_affecte2.refresh_from_db()
        job_affecte3.refresh_from_db()
        job_affecte4.refresh_from_db()
        job_affecte5.refresh_from_db()
        
        self.assertEqual(self.job_affecte.status, 'PRET')
        self.assertEqual(self.job_affecte2.status, 'PRET')
        self.assertEqual(job_affecte3.status, 'PRET')
        self.assertEqual(job_affecte4.status, 'PRET')
        self.assertEqual(job_affecte5.status, 'PRET')
        
        # Vérifier que toutes les dates ont été définies
        self.assertIsNotNone(self.job_affecte.pret_date)
        self.assertIsNotNone(self.job_affecte2.pret_date)
        self.assertIsNotNone(job_affecte3.pret_date)
        self.assertIsNotNone(job_affecte4.pret_date)
        self.assertIsNotNone(job_affecte5.pret_date) 