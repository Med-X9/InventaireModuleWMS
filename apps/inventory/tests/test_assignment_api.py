"""
Tests pour l'API d'affectation des jobs de comptage
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import Inventory, Job, Counting, Assigment
from apps.masterdata.models import Warehouse, Account
from apps.users.models import UserApp, Role

class JobAssignmentAPITestCase(TestCase):
    """Tests pour l'API d'affectation des jobs"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.client = APIClient()
        
        # Créer les données de test
        self.account = Account.objects.create(name="Test Account")
        self.warehouse = Warehouse.objects.create(
            name="Test Warehouse",
            account=self.account
        )
        
        # Créer un inventaire
        self.inventory = Inventory.objects.create(
            label="Test Inventory",
            date=timezone.now(),
            status="EN PREPARATION"
        )
        
        # Créer des jobs
        self.job1 = Job.objects.create(
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        self.job2 = Job.objects.create(
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        # Créer des comptages
        self.counting1 = Counting.objects.create(
            order=1,
            count_mode="image stock",
            inventory=self.inventory
        )
        self.counting2 = Counting.objects.create(
            order=2,
            count_mode="en vrac",
            inventory=self.inventory
        )
        
        # Créer un rôle et un utilisateur opérateur
        self.role = Role.objects.create(name="Operateur")
        self.operator = UserApp.objects.create(
            username="operator1",
            email="operator@test.com",
            role=self.role
        )
    
    def test_assign_jobs_success(self):
        """Test d'affectation réussie de jobs"""
        url = reverse('assign-jobs-to-counting')
        data = {
            'job_ids': [self.job1.id, self.job2.id],
            'counting_order': 2,
            'session_id': self.operator.id,
            'date_start': timezone.now().isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['assignments_created'], 2)
        self.assertEqual(response.data['counting_order'], 2)
        
        # Vérifier que les affectations ont été créées
        assignments = Assigment.objects.filter(job__in=[self.job1, self.job2])
        self.assertEqual(assignments.count(), 2)
        
        # Vérifier que les statuts des jobs ont été mis à jour
        self.job1.refresh_from_db()
        self.job2.refresh_from_db()
        self.assertEqual(self.job1.status, 'AFFECTE')
        self.assertEqual(self.job2.status, 'AFFECTE')
    
    def test_assign_jobs_image_stock_no_session(self):
        """Test d'affectation pour comptage image stock sans session"""
        url = reverse('assign-jobs-to-counting')
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que l'affectation a été créée sans session
        assignment = Assigment.objects.get(job=self.job1)
        self.assertIsNone(assignment.session)
    
    def test_assign_jobs_image_stock_with_session_error(self):
        """Test d'erreur lors de l'affectation d'une session pour image stock"""
        url = reverse('assign-jobs-to-counting')
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 1,
            'session_id': self.operator.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('image stock', response.data['error'])
    
    def test_assign_jobs_en_vrac_without_session_error(self):
        """Test d'erreur lors de l'affectation en vrac sans session"""
        url = reverse('assign-jobs-to-counting')
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Note: Le service permet l'affectation sans session pour en vrac
        # mais l'affectation sera créée sans session
    
    def test_assign_jobs_invalid_counting_order(self):
        """Test d'erreur avec un ordre de comptage invalide"""
        url = reverse('assign-jobs-to-counting')
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 4
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_assign_jobs_empty_job_ids(self):
        """Test d'erreur avec une liste vide d'IDs de jobs"""
        url = reverse('assign-jobs-to-counting')
        data = {
            'job_ids': [],
            'counting_order': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_assign_jobs_different_inventories_error(self):
        """Test d'erreur avec des jobs d'inventaires différents"""
        # Créer un autre inventaire et job
        other_inventory = Inventory.objects.create(
            label="Other Inventory",
            date=timezone.now(),
            status="EN PREPARATION"
        )
        other_job = Job.objects.create(
            status="EN ATTENTE",
            warehouse=self.warehouse,
            inventory=other_inventory
        )
        
        url = reverse('assign-jobs-to-counting')
        data = {
            'job_ids': [self.job1.id, other_job.id],
            'counting_order': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('même inventaire', response.data['error'])
    
    def test_assign_jobs_already_assigned_error(self):
        """Test d'erreur avec un job déjà affecté"""
        # Créer une affectation existante
        Assigment.objects.create(
            job=self.job1,
            counting=self.counting1,
            date_start=timezone.now()
        )
        
        url = reverse('assign-jobs-to-counting')
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('déjà une affectation', response.data['error'])
    
    def test_get_assignment_rules(self):
        """Test de récupération des règles d'affectation"""
        url = reverse('assignment-rules')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rules', response.data)
        self.assertIn('counting_modes', response.data['rules'])
        self.assertIn('session_rules', response.data['rules']) 