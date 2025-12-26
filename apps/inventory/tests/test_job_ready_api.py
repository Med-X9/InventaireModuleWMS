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
from ..exceptions import JobCreationError
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
            password='testpass123',
            type='Web'
        )
        self.client.force_authenticate(user=self.user)
        
        # Créer les données de base
        self.account = Account.objects.create(
            account_name='Test Account',
            reference='TEST001'
        )
        
        self.warehouse = Warehouse.objects.create(
            warehouse_name='Test Warehouse',
            reference='WH001',
            warehouse_type='CENTRAL',
            status='ACTIVE'
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


class JobAutoSetReadyAPITestCase(TestCase):
    """Tests pour l'API de mise automatique en prêt des jobs - logique tout ou rien"""

    def setUp(self):
        """Configuration initiale pour les tests"""
        self.client = APIClient()

        # Créer un utilisateur pour l'authentification
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            type='Web'
        )
        self.client.force_authenticate(user=self.user)

        # Créer les données de base
        self.account = Account.objects.create(
            account_name='Test Account',
            reference='TEST001'
        )

        self.warehouse = Warehouse.objects.create(
            warehouse_name='Test Warehouse',
            reference='WH001',
            warehouse_type='CENTRAL',
            status='ACTIVE'
        )

        self.inventory = Inventory.objects.create(
            label='Test Inventory',
            date=timezone.now(),
            status='EN PREPARATION'
        )

        # Créer des jobs avec différents statuts pour tester la validation
        self.job1 = Job.objects.create(
            status='AFFECTE',  # Job en AFFECTE avec assignments AFFECTE à traiter
            warehouse=self.warehouse,
            inventory=self.inventory,
            reference='JOB-0001'
        )

        self.job2 = Job.objects.create(
            status='PRET',  # Job déjà PRET - ne sera pas traité
            warehouse=self.warehouse,
            inventory=self.inventory,
            reference='JOB-0002'
        )

        self.job3 = Job.objects.create(
            status='VALIDE',  # Job VALIDE - ne sera pas traité
            warehouse=self.warehouse,
            inventory=self.inventory,
            reference='JOB-0003'
        )

        # Créer des comptages
        self.counting1 = Counting.objects.create(
            order=1,
            count_mode='image stock',
            inventory=self.inventory,
            reference='CNT-001'
        )

        self.counting2 = Counting.objects.create(
            order=2,
            count_mode='en vrac',
            inventory=self.inventory,
            reference='CNT-002'
        )

        # Créer des assignments AFFECTE pour les jobs
        self.assignment1_job1 = Assigment.objects.create(
            job=self.job1,
            counting=self.counting1,
            status='AFFECTE',
            reference='ASS-001'
        )

        self.assignment2_job1 = Assigment.objects.create(
            job=self.job1,
            counting=self.counting2,
            status='AFFECTE',
            reference='ASS-002'
        )

        self.assignment1_job2 = Assigment.objects.create(
            job=self.job2,
            counting=self.counting1,
            status='AFFECTE',
            reference='ASS-003'
        )

        self.assignment1_job3 = Assigment.objects.create(
            job=self.job3,
            counting=self.counting2,
            status='AFFECTE',
            reference='ASS-004'
        )

    def test_auto_set_ready_success(self):
        """Test que l'API set-ready fonctionne correctement avec la logique tout ou rien"""
        # S'assurer que tous les jobs sont AFFECTE pour ce test
        Job.objects.filter(id__in=[self.job1.id, self.job2.id, self.job3.id]).update(status='AFFECTE')

        url = reverse('jobs-auto-set-ready', kwargs={
            'inventory_id': self.inventory.id,
            'warehouse_id': self.warehouse.id
        })

        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Vérifier les données de réponse - tous les jobs AFFECTE sont traités
        data = response.data['data']
        self.assertEqual(data['jobs_processed'], 3)  # Tous les jobs AFFECTE sont traités
        self.assertEqual(data['assignments_processed'], 4)  # Tous les assignments AFFECTE
        self.assertEqual(len(data['jobs']), 3)

        # Vérifier que les statuts ont été mis à jour - tous les jobs AFFECTE deviennent PRET
        self.job1.refresh_from_db()
        self.job2.refresh_from_db()
        self.job3.refresh_from_db()
        self.assignment1_job1.refresh_from_db()
        self.assignment2_job1.refresh_from_db()
        self.assignment1_job2.refresh_from_db()
        self.assignment1_job3.refresh_from_db()

        # Tous les jobs AFFECTE deviennent PRET
        self.assertEqual(self.job1.status, 'PRET')
        self.assertEqual(self.job2.status, 'PRET')
        self.assertEqual(self.job3.status, 'PRET')
        self.assertIsNotNone(self.job1.pret_date)
        self.assertIsNotNone(self.job2.pret_date)
        self.assertIsNotNone(self.job3.pret_date)

        # Tous les assignments AFFECTE deviennent PRET
        self.assertEqual(self.assignment1_job1.status, 'PRET')
        self.assertEqual(self.assignment2_job1.status, 'PRET')
        self.assertEqual(self.assignment1_job2.status, 'PRET')
        self.assertEqual(self.assignment1_job3.status, 'PRET')
        self.assertIsNotNone(self.assignment1_job1.pret_date)
        self.assertIsNotNone(self.assignment2_job1.pret_date)
        self.assertIsNotNone(self.assignment1_job2.pret_date)
        self.assertIsNotNone(self.assignment1_job3.pret_date)

    def test_auto_set_ready_no_eligible_jobs(self):
        """
        Test quand aucun job AFFECTE n'est trouvé parmi tous les jobs
        On récupère tous les jobs, valide leurs statuts, et vérifie qu'aucun n'est AFFECTE
        """
        # Changer le statut des jobs AFFECTE pour qu'ils ne soient plus AFFECTE
        Job.objects.filter(id=self.job1.id).update(status='PRET')

        url = reverse('jobs-auto-set-ready', kwargs={
            'inventory_id': self.inventory.id,
            'warehouse_id': self.warehouse.id
        })

        response = self.client.post(url, format='json')

        # On retourne une erreur car aucun job n'est en AFFECTE
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Aucun job en statut AFFECTE trouvé', response.data['message'])

    def test_auto_set_ready_invalid_inventory(self):
        """Test avec un ID d'inventaire invalide"""
        url = reverse('jobs-auto-set-ready', kwargs={
            'inventory_id': 99999,
            'warehouse_id': self.warehouse.id
        })

        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_auto_set_ready_invalid_warehouse(self):
        """Test avec un ID de warehouse invalide"""
        url = reverse('jobs-auto-set-ready', kwargs={
            'inventory_id': self.inventory.id,
            'warehouse_id': 99999
        })

        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_auto_set_ready_invalid_job_status(self):
        """
        Test que si un job a un statut invalide, l'opération est bloquée
        """
        # Changer le statut d'un job pour qu'il soit invalide
        Job.objects.filter(id=self.job1.id).update(status='EN ATTENTE')

        url = reverse('jobs-auto-set-ready', kwargs={
            'inventory_id': self.inventory.id,
            'warehouse_id': self.warehouse.id
        })

        response = self.client.post(url, format='json')

        # La requête doit échouer car il y a un job avec statut invalide
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Erreurs de validation', response.data['message'])
        self.assertIn('statut \'EN ATTENTE\'', response.data['message'])

    def test_auto_set_ready_any_invalid_blocks_all(self):
        """
        Test que si UN SEUL assignment a un statut invalide,
        TOUT le traitement est bloqué avec une erreur
        """
        # Créer des jobs frais pour ce test
        test_job1 = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            reference='TEST-JOB-001'
        )
        test_job2 = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            reference='TEST-JOB-002'
        )

        # Créer des assignments AFFECTE pour les deux jobs
        Assigment.objects.create(
            job=test_job1,
            counting=self.counting1,
            status='AFFECTE',
            reference='TEST-ASS-001'
        )
        Assigment.objects.create(
            job=test_job2,
            counting=self.counting2,
            status='AFFECTE',
            reference='TEST-ASS-002'
        )

        # Modifier un assignment pour qu'il soit invalide
        Assigment.objects.filter(job=test_job1).update(status='VALIDE')

        url = reverse('jobs-auto-set-ready', kwargs={
            'inventory_id': self.inventory.id,
            'warehouse_id': self.warehouse.id
        })

        response = self.client.post(url, format='json')

        # La requête doit échouer car il y a un assignment invalide
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Erreurs de validation', response.data['message'])
        self.assertIn('statut \'VALIDE\'', response.data['message'])

        # Vérifier que RIEN n'a été traité (logique "tout ou rien")
        test_job1.refresh_from_db()
        test_job2.refresh_from_db()

        # Les jobs restent AFFECTE car la transaction a été rollback
        self.assertEqual(test_job1.status, 'AFFECTE')
        self.assertEqual(test_job2.status, 'AFFECTE')

    def test_auto_set_ready_multiple_errors(self):
        """
        Test que les erreurs de jobs ET d'assignments sont affichées ensemble
        """
        # Créer des jobs avec statuts mixtes
        invalid_job = Job.objects.create(
            status='PRET',  # Invalide pour cette opération
            warehouse=self.warehouse,
            inventory=self.inventory,
            reference='INVALID-JOB'
        )

        valid_job = Job.objects.create(
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            reference='VALID-JOB'
        )

        # Créer des assignments
        Assigment.objects.create(
            job=invalid_job,
            counting=self.counting1,
            status='AFFECTE',  # Valide
            reference='ASS-INVALID-JOB'
        )
        Assigment.objects.create(
            job=valid_job,
            counting=self.counting2,
            status='VALIDE',  # Invalide
            reference='ASS-VALID-JOB'
        )

        url = reverse('jobs-auto-set-ready', kwargs={
            'inventory_id': self.inventory.id,
            'warehouse_id': self.warehouse.id
        })

        response = self.client.post(url, format='json')

        # La requête doit échouer avec les deux types d'erreurs
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Erreurs de validation', response.data['message'])

        # Vérifier que les deux erreurs sont présentes
        message = response.data['message']
        self.assertIn('statut \'PRET\'', message)  # Erreur de job
        self.assertIn('statut \'VALIDE\'', message)  # Erreur d'assignment 