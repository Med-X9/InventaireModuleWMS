"""
Tests pour la logique de mise à jour du statut des jobs lors de l'affectation
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
from apps.inventory.services.assignment_service import AssignmentService

User = get_user_model()

class AssignmentStatusUpdateTestCase(TestCase):
    """Tests pour la mise à jour du statut des jobs lors de l'affectation"""
    
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
        
        # Créer des jobs avec statut VALIDE
        self.job1 = Job.objects.create(
            status='VALIDE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        self.job2 = Job.objects.create(
            status='VALIDE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        # Créer deux comptages
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
        
        # Créer des sessions mobile
        self.session1 = UserApp.objects.create(
            username='mobile1',
            type='Mobile'
        )
        
        self.session2 = UserApp.objects.create(
            username='mobile2',
            type='Mobile'
        )
        
        # Service d'affectation
        self.assignment_service = AssignmentService()
    
    def test_job_status_remains_valide_after_first_counting(self):
        """Test que le statut reste VALIDE après le premier comptage"""
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 1,
            'session_id': self.session1.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le statut du job reste VALIDE
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, 'VALIDE')
        
        # Vérifier que l'affectation a été créée
        assignment = Assigment.objects.get(job=self.job1, counting=self.counting1)
        self.assertEqual(assignment.session, self.session1)
    
    def test_job_status_becomes_affecte_after_second_counting(self):
        """Test que le statut devient AFFECTE après le deuxième comptage"""
        # D'abord, affecter le premier comptage
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 1,
            'session_id': self.session1.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Ensuite, affecter le deuxième comptage
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.session2.id,
            'date_start': '2024-01-15T11:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le statut du job est devenu AFFECTE
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, 'AFFECTE')
        
        # Vérifier que les deux affectations ont été créées
        assignments = Assigment.objects.filter(job=self.job1)
        self.assertEqual(assignments.count(), 2)
        
        # Vérifier que les deux affectations ont des sessions
        assignments_with_session = assignments.filter(session__isnull=False)
        self.assertEqual(assignments_with_session.count(), 2)
    
    def test_job_status_remains_valide_without_session(self):
        """Test que le statut reste VALIDE si pas de session pour le deuxième comptage"""
        # D'abord, affecter le premier comptage avec session
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 1,
            'session_id': self.session1.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Ensuite, affecter le deuxième comptage sans session
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'date_start': '2024-01-15T11:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le statut du job reste VALIDE
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, 'VALIDE')
        
        # Vérifier qu'il n'y a qu'une affectation avec session
        assignments_with_session = Assigment.objects.filter(job=self.job1, session__isnull=False)
        self.assertEqual(assignments_with_session.count(), 1)
    
    def test_multiple_jobs_status_update(self):
        """Test de mise à jour du statut pour plusieurs jobs"""
        # Affecter le premier comptage pour les deux jobs
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id, self.job2.id],
            'counting_order': 1,
            'session_id': self.session1.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Affecter le deuxième comptage pour les deux jobs
        data = {
            'job_ids': [self.job1.id, self.job2.id],
            'counting_order': 2,
            'session_id': self.session2.id,
            'date_start': '2024-01-15T11:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que les deux jobs sont devenus AFFECTE
        self.job1.refresh_from_db()
        self.job2.refresh_from_db()
        self.assertEqual(self.job1.status, 'AFFECTE')
        self.assertEqual(self.job2.status, 'AFFECTE')
    
    def test_job_status_update_with_existing_assignments(self):
        """Test de mise à jour du statut avec des affectations existantes"""
        # Créer une affectation existante pour le premier comptage
        existing_assignment = Assigment.objects.create(
            job=self.job1,
            counting=self.counting1,
            session=self.session1,
            date_start=timezone.now()
        )
        
        # Affecter le deuxième comptage
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.session2.id,
            'date_start': '2024-01-15T11:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le statut du job est devenu AFFECTE
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, 'AFFECTE')
        
        # Vérifier que les deux affectations existent
        assignments = Assigment.objects.filter(job=self.job1)
        self.assertEqual(assignments.count(), 2)
    
    def test_job_status_not_updated_with_single_counting(self):
        """Test que le statut n'est pas mis à jour s'il n'y a qu'un seul comptage"""
        # Supprimer le deuxième comptage
        self.counting2.delete()
        
        # Affecter le premier comptage
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 1,
            'session_id': self.session1.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le statut du job reste VALIDE
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, 'VALIDE')
    
    def test_assignments_status_updated_to_affecte_when_both_countings_have_sessions(self):
        """Test que le statut des affectations passe à 'AFFECTE' quand les deux comptages ont des sessions."""
        
        # Créer une affectation pour le premier comptage avec session
        assignment1 = Assigment.objects.create(
            reference='ASS001',
            status='EN ATTENTE',
            job=self.job1,
            counting=self.counting1,
            session=self.session1,
            date_start=timezone.now()
        )
        
        # Créer une affectation pour le deuxième comptage avec session
        assignment2 = Assigment.objects.create(
            reference='ASS002',
            status='EN ATTENTE',
            job=self.job1,
            counting=self.counting2,
            session=self.session2,
            date_start=timezone.now()
        )
        
        # Vérifier que les deux comptages ont des sessions
        self.assertTrue(self.assignment_service.should_update_job_status_to_affecte(self.job1.id, self.inventory.id))
        
        # Mettre à jour le statut des affectations
        self.assignment_service.update_assignments_status_to_affecte(self.job1.id, self.inventory.id)
        
        # Vérifier que les statuts ont été mis à jour
        assignment1.refresh_from_db()
        assignment2.refresh_from_db()
        
        self.assertEqual(assignment1.status, 'AFFECTE')
        self.assertEqual(assignment2.status, 'AFFECTE')
        self.assertIsNotNone(assignment1.affecte_date)
        self.assertIsNotNone(assignment2.affecte_date)
    
    def test_assignments_status_not_updated_when_only_one_counting_has_session(self):
        """Test que le statut des affectations ne change pas quand un seul comptage a une session."""
        
        # Créer une affectation pour le premier comptage avec session
        assignment1 = Assigment.objects.create(
            reference='ASS001',
            status='EN ATTENTE',
            job=self.job1,
            counting=self.counting1,
            session=self.session1,
            date_start=timezone.now()
        )
        
        # Créer une affectation pour le deuxième comptage SANS session
        assignment2 = Assigment.objects.create(
            reference='ASS002',
            status='EN ATTENTE',
            job=self.job1,
            counting=self.counting2,
            session=None,
            date_start=timezone.now()
        )
        
        # Vérifier que les deux comptages n'ont pas tous les deux des sessions
        self.assertFalse(self.assignment_service.should_update_job_status_to_affecte(self.job1.id, self.inventory.id))
        
        # Mettre à jour le statut des affectations (ne devrait rien changer)
        self.assignment_service.update_assignments_status_to_affecte(self.job1.id, self.inventory.id)
        
        # Vérifier que les statuts n'ont pas changé
        assignment1.refresh_from_db()
        assignment2.refresh_from_db()
        
        self.assertEqual(assignment1.status, 'EN ATTENTE')
        self.assertEqual(assignment2.status, 'EN ATTENTE')
    
    def test_assign_jobs_api_updates_assignments_status_automatically(self):
        """Test que l'API assign-jobs met automatiquement à jour le statut des affectations."""
        
        # Créer une affectation pour le premier comptage avec session
        assignment1 = Assigment.objects.create(
            reference='ASS001',
            status='EN ATTENTE',
            job=self.job1,
            counting=self.counting1,
            session=self.session1,
            date_start=timezone.now()
        )
        
        # Données pour l'affectation du deuxième comptage
        assignment_data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.session2.id,
            'date_start': timezone.now()
        }
        
        # Appeler le service d'affectation
        result = self.assignment_service.assign_jobs(assignment_data)
        
        # Vérifier que l'affectation a été créée
        self.assertTrue(result['success'])
        self.assertEqual(result['assignments_created'], 1)
        
        # Vérifier que les statuts ont été mis à jour automatiquement
        assignment1.refresh_from_db()
        assignment2 = Assigment.objects.get(job=self.job1, counting=self.counting2)
        
        self.assertEqual(assignment1.status, 'AFFECTE')
        self.assertEqual(assignment2.status, 'AFFECTE')
        self.assertIsNotNone(assignment1.affecte_date)
        self.assertIsNotNone(assignment2.affecte_date) 