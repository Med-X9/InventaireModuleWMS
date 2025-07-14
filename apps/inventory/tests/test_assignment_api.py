"""
Tests pour l'API d'affectation des jobs de comptage
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

class JobAssignmentAPITestCase(TestCase):
    """Tests pour l'API d'affectation des jobs"""
    
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
        
        # Créer des jobs
        self.job1 = Job.objects.create(
            status='EN ATTENTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        self.job2 = Job.objects.create(
            status='EN ATTENTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
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
        
        # Créer une session mobile
        self.mobile_session = UserApp.objects.create(
            username='mobile1',
            type='Mobile'
        )
    
    def test_assign_jobs_success(self):
        """Test d'affectation réussie de jobs"""
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id, self.job2.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['assignments_created'], 2)
        self.assertEqual(response.data['assignments_updated'], 0)
        self.assertEqual(response.data['total_assignments'], 2)
        
        # Vérifier que les affectations ont été créées
        assignments = Assigment.objects.filter(job__in=[self.job1, self.job2])
        self.assertEqual(assignments.count(), 2)
        
        # Vérifier que les statuts des jobs ont été mis à jour
        self.job1.refresh_from_db()
        self.job2.refresh_from_db()
        self.assertEqual(self.job1.status, 'AFFECTE')
        self.assertEqual(self.job2.status, 'AFFECTE')
    
    def test_assign_jobs_image_stock_no_session(self):
        """Test d'affectation pour mode image stock sans session"""
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['assignments_created'], 1)
        
        # Vérifier que l'affectation a été créée sans session
        assignment = Assigment.objects.get(job=self.job1)
        self.assertIsNone(assignment.session)
    
    def test_assign_jobs_image_stock_with_session_error(self):
        """Test d'erreur lors d'affectation de session pour mode image stock"""
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 1,
            'session_id': self.mobile_session.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('image stock', response.data['error'])
    
    def test_assign_jobs_invalid_data(self):
        """Test avec des données invalides"""
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [],  # Liste vide
            'counting_order': 3  # Ordre invalide
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_assign_jobs_jobs_not_found(self):
        """Test avec des IDs de jobs inexistants"""
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [99999, 88888],
            'counting_order': 2
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_assign_jobs_session_not_found(self):
        """Test avec une session inexistante"""
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': 99999
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_update_existing_assignment(self):
        """Test de mise à jour d'une affectation existante"""
        # Créer une affectation existante
        existing_assignment = Assigment.objects.create(
            job=self.job1,
            counting=self.counting2,
            session=self.mobile_session,
            date_start=timezone.now()
        )
        
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id,
            'date_start': '2024-01-16T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['assignments_created'], 0)
        self.assertEqual(response.data['assignments_updated'], 1)
        
        # Vérifier que l'affectation a été mise à jour
        existing_assignment.refresh_from_db()
        self.assertEqual(existing_assignment.date_start, datetime.fromisoformat('2024-01-16T10:00:00+00:00'))
    
    def test_get_assignment_rules(self):
        """Test de récupération des règles d'affectation"""
        url = reverse('assignment-rules')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rules', response.data)
        self.assertIn('counting_modes', response.data['rules'])
        self.assertIn('counting_orders', response.data['rules'])
    
    def test_assign_jobs_different_inventories_error(self):
        """Test d'erreur avec des jobs d'inventaires différents"""
        # Créer un autre inventaire et job
        other_inventory = Inventory.objects.create(
            label='Other Inventory',
            date=timezone.now(),
            status='EN PREPARATION'
        )
        
        other_job = Job.objects.create(
            status='EN ATTENTE',
            warehouse=self.warehouse,
            inventory=other_inventory
        )
        
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id, other_job.id],
            'counting_order': 2
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_assign_jobs_multiple_assignments_cleanup(self):
        """Test de nettoyage des affectations multiples pour un même job"""
        # Créer plusieurs affectations pour le même job
        assignment1 = Assigment.objects.create(
            job=self.job1,
            counting=self.counting2,
            session=self.mobile_session,
            date_start=timezone.now() - timedelta(hours=1)
        )
        
        assignment2 = Assigment.objects.create(
            job=self.job1,
            counting=self.counting2,
            session=self.mobile_session,
            date_start=timezone.now()
        )
        
        # Vérifier qu'il y a bien 2 affectations
        self.assertEqual(Assigment.objects.filter(job=self.job1).count(), 2)
        
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier qu'il ne reste qu'une seule affectation (la plus récente)
        self.assertEqual(Assigment.objects.filter(job=self.job1).count(), 1)
        remaining_assignment = Assigment.objects.get(job=self.job1)
        self.assertEqual(remaining_assignment.id, assignment2.id)
    
    def test_get_assignments_by_session(self):
        """Test de récupération des affectations d'une session"""
        # Créer des affectations pour la session
        assignment1 = Assigment.objects.create(
            job=self.job1,
            counting=self.counting2,
            session=self.mobile_session,
            date_start=timezone.now()
        )
        
        assignment2 = Assigment.objects.create(
            job=self.job2,
            counting=self.counting2,
            session=self.mobile_session,
            date_start=timezone.now()
        )
        
        url = reverse('assignments-by-session', kwargs={'session_id': self.mobile_session.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['session_id'], self.mobile_session.id)
        self.assertEqual(response.data['assignments_count'], 2)
        self.assertEqual(len(response.data['assignments']), 2)
        
        # Vérifier les données des affectations
        assignments_data = response.data['assignments']
        job_ids = [assignment['job_id'] for assignment in assignments_data]
        self.assertIn(self.job1.id, job_ids)
        self.assertIn(self.job2.id, job_ids)
    
    def test_get_assignments_by_session_empty(self):
        """Test de récupération des affectations d'une session sans affectations"""
        url = reverse('assignments-by-session', kwargs={'session_id': self.mobile_session.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['session_id'], self.mobile_session.id)
        self.assertEqual(response.data['assignments_count'], 0)
        self.assertEqual(len(response.data['assignments']), 0)
    
    def test_get_assignments_by_session_not_found(self):
        """Test de récupération des affectations d'une session inexistante"""
        url = reverse('assignments-by-session', kwargs={'session_id': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['assignments_count'], 0)
        self.assertEqual(len(response.data['assignments']), 0)
    
    def test_assign_jobs_invalid_status_error(self):
        """Test d'erreur lors d'affectation de jobs avec statut invalide"""
        # Créer un job avec statut invalide (EN ATTENTE)
        self.job1.status = 'EN ATTENTE'
        self.job1.save()
        
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('EN ATTENTE', response.data['error'])
        self.assertIn('doivent d\'abord être validés', response.data['error'])

    def test_assign_jobs_valid_status_success(self):
        """Test d'affectation réussie de jobs en statut VALIDE"""
        # Créer un job avec statut VALIDE
        self.job1.status = 'VALIDE'
        self.job1.save()
        
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['assignments_created'], 1)
        
        # Vérifier que le statut du job a été mis à jour vers AFFECTE
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, 'AFFECTE')

    def test_assign_jobs_affecte_status_success(self):
        """Test d'affectation réussie de jobs en statut AFFECTE"""
        # Créer un job avec statut AFFECTE
        self.job1.status = 'AFFECTE'
        self.job1.save()
        
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['assignments_updated'], 1)  # Mise à jour car déjà affecté

    def test_assign_jobs_other_statuses_success(self):
        """Test d'affectation réussie de jobs avec d'autres statuts"""
        # Tester différents statuts autorisés
        allowed_statuses = ['PRET', 'TRANSFERT', 'ENTAME', 'TERMINE']
        
        for status in allowed_statuses:
            self.job1.status = status
            self.job1.save()
            
            url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
            data = {
                'job_ids': [self.job1.id],
                'counting_order': 2,
                'session_id': self.mobile_session.id,
                'date_start': '2024-01-15T10:00:00Z'
            }
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Échec pour le statut {status}")
            self.assertTrue(response.data['success'], f"Échec pour le statut {status}")

    def test_assign_jobs_en_attente_not_allowed(self):
        """Test que les jobs en statut EN ATTENTE ne peuvent pas être affectés"""
        # Créer un job avec statut EN ATTENTE
        self.job1.status = 'EN ATTENTE'
        self.job1.save()
        
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('EN ATTENTE', response.data['error'])
        self.assertIn('doivent d\'abord être validés', response.data['error'])
        
        # Vérifier que le statut du job n'a pas changé
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, 'EN ATTENTE')

    def test_assign_jobs_mixed_status_error(self):
        """Test d'erreur lors d'affectation de jobs avec statuts mixtes"""
        # Créer des jobs avec différents statuts
        self.job1.status = 'VALIDE'
        self.job1.save()
        
        self.job2.status = 'EN ATTENTE'
        self.job2.save()
        
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data = {
            'job_ids': [self.job1.id, self.job2.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('EN ATTENTE', response.data['error'])
        
        # Vérifier qu'aucun job n'a été affecté
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, 'VALIDE')

    def test_assign_jobs_different_countings_independent(self):
        """Test que les affectations pour différents comptages sont indépendantes"""
        # Créer des jobs en statut VALIDE
        self.job1.status = 'VALIDE'
        self.job1.save()
        
        self.job2.status = 'VALIDE'
        self.job2.save()
        
        # Créer un troisième comptage pour tester
        counting3 = Counting.objects.create(
            order=3,
            count_mode='en vrac',
            inventory=self.inventory
        )
        
        # Première affectation : comptage 1
        url = reverse('assign-jobs-to-counting', kwargs={'inventory_id': self.inventory.id})
        data1 = {
            'job_ids': [self.job1.id, self.job2.id],
            'counting_order': 1,
            'session_id': self.mobile_session.id,
            'date_start': '2024-01-15T10:00:00Z'
        }
        
        response1 = self.client.post(url, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response1.data['success'])
        
        # Vérifier qu'il y a 2 affectations pour le comptage 1
        assignments_counting1 = Assigment.objects.filter(counting=self.counting1)
        self.assertEqual(assignments_counting1.count(), 2)
        
        # Deuxième affectation : comptage 2
        data2 = {
            'job_ids': [self.job1.id, self.job2.id],
            'counting_order': 2,
            'session_id': self.mobile_session.id,
            'date_start': '2024-01-16T10:00:00Z'
        }
        
        response2 = self.client.post(url, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response2.data['success'])
        
        # Vérifier qu'il y a maintenant 4 affectations au total (2 pour chaque comptage)
        total_assignments = Assigment.objects.filter(job__in=[self.job1, self.job2])
        self.assertEqual(total_assignments.count(), 4)
        
        # Vérifier qu'il y a 2 affectations pour le comptage 1 (inchangées)
        assignments_counting1_after = Assigment.objects.filter(counting=self.counting1)
        self.assertEqual(assignments_counting1_after.count(), 2)
        
        # Vérifier qu'il y a 2 affectations pour le comptage 2 (nouvelles)
        assignments_counting2 = Assigment.objects.filter(counting=self.counting2)
        self.assertEqual(assignments_counting2.count(), 2)
        
        # Troisième affectation : mettre à jour le comptage 1
        data3 = {
            'job_ids': [self.job1.id],
            'counting_order': 1,
            'session_id': self.mobile_session.id,
            'date_start': '2024-01-17T10:00:00Z'
        }
        
        response3 = self.client.post(url, data3, format='json')
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response3.data['success'])
        self.assertEqual(response3.data['assignments_updated'], 1)
        
        # Vérifier que le comptage 2 n'a pas été affecté
        assignments_counting2_after = Assigment.objects.filter(counting=self.counting2)
        self.assertEqual(assignments_counting2_after.count(), 2) 