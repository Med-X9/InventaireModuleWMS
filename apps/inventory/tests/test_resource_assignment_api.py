"""
Tests pour l'API d'affectation des ressources aux jobs.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.inventory.models import Job, JobDetailRessource, Inventory
from apps.masterdata.models import Warehouse, Ressource
from apps.inventory.services.resource_assignment_service import ResourceAssignmentService
from apps.inventory.exceptions.resource_assignment_exceptions import (
    ResourceAssignmentValidationError,
    ResourceAssignmentBusinessRuleError,
    ResourceAssignmentNotFoundError
)

User = get_user_model()

class ResourceAssignmentAPITestCase(TestCase):
    """Tests pour l'API d'affectation des ressources aux jobs."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = APIClient()
        
        # Créer un utilisateur pour l'authentification
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            type='Mobile'
        )
        self.client.force_authenticate(user=self.user)
        
        # Créer un inventaire
        self.inventory = Inventory.objects.create(
            label='Test Inventory',
            date='2024-01-01T10:00:00Z',
            status='EN PREPARATION'
        )
        
        # Créer un entrepôt
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='WH001'
        )
        
        # Créer des jobs avec différents statuts
        self.job_valide = Job.objects.create(
            status='VALIDE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        self.job_valide2 = Job.objects.create(
            status='VALIDE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        self.job_en_attente = Job.objects.create(
            status='EN ATTENTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        # Créer des ressources
        self.resource1 = Ressource.objects.create(
            libelle='Scanner',
            reference='SCAN001',
            status='ACTIVE'
        )
        
        self.resource2 = Ressource.objects.create(
            libelle='Terminal',
            reference='TERM001',
            status='ACTIVE'
        )
        
        self.resource3 = Ressource.objects.create(
            libelle='Imprimante',
            reference='PRINT001',
            status='ACTIVE'
        )

    def test_assign_resources_to_jobs_success(self):
        """Test d'affectation réussie de ressources communes à plusieurs jobs."""
        url = reverse('assign-resources-to-jobs')
        
        data = {
            'job_ids': [self.job_valide.id, self.job_valide2.id],
            'resource_assignments': [
                {
                    'resource_id': self.resource1.id,
                    'quantity': 2
                },
                {
                    'resource_id': self.resource2.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['total_jobs_processed'], 2)
        self.assertEqual(response.data['total_assignments_created'], 4)  # 2 jobs × 2 ressources
        self.assertEqual(response.data['total_assignments_updated'], 0)
        
        # Vérifier que les affectations ont été créées en base
        job1_resources = JobDetailRessource.objects.filter(job=self.job_valide)
        self.assertEqual(job1_resources.count(), 2)
        
        job2_resources = JobDetailRessource.objects.filter(job=self.job_valide2)
        self.assertEqual(job2_resources.count(), 2)
        
        # Vérifier que les deux jobs ont les mêmes ressources
        job1_resource_ids = set(job1_resources.values_list('ressource_id', flat=True))
        job2_resource_ids = set(job2_resources.values_list('ressource_id', flat=True))
        self.assertEqual(job1_resource_ids, job2_resource_ids)

    def test_assign_resources_to_jobs_with_en_attente_job(self):
        """Test d'affectation avec un job EN ATTENTE qui doit échouer."""
        url = reverse('assign-resources-to-jobs')
        
        data = {
            'job_ids': [self.job_valide.id, self.job_en_attente.id],
            'resource_assignments': [
                {
                    'resource_id': self.resource1.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['total_jobs_processed'], 2)
        
        # Vérifier que le premier job a été traité avec succès
        job_results = response.data['job_results']
        self.assertTrue(job_results[0]['success'])
        self.assertFalse(job_results[1]['success'])
        self.assertIn('EN ATTENTE', job_results[1]['message'])

    def test_assign_resources_to_nonexistent_job(self):
        """Test d'affectation de ressources à un job inexistant."""
        url = reverse('assign-resources-to-jobs')
        
        data = {
            'job_ids': [99999],
            'resource_assignments': [
                {
                    'resource_id': self.resource1.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job_results = response.data['job_results']
        self.assertFalse(job_results[0]['success'])
        self.assertIn('non trouvé', job_results[0]['message'])

    def test_assign_nonexistent_resource(self):
        """Test d'affectation d'une ressource inexistante."""
        url = reverse('assign-resources-to-jobs')
        
        data = {
            'job_ids': [self.job_valide.id],
            'resource_assignments': [
                {
                    'resource_id': 99999,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job_results = response.data['job_results']
        self.assertFalse(job_results[0]['success'])
        self.assertIn('non trouvée', job_results[0]['message'])

    def test_assign_resources_update_existing(self):
        """Test de mise à jour d'une affectation existante."""
        # Créer une affectation initiale
        JobDetailRessource.objects.create(
            job=self.job_valide,
            ressource=self.resource1,
            quantity=1
        )
        
        url = reverse('assign-resources-to-jobs')
        
        data = {
            'job_ids': [self.job_valide.id],
            'resource_assignments': [
                {
                    'resource_id': self.resource1.id,
                    'quantity': 3
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_assignments_created'], 0)
        self.assertEqual(response.data['total_assignments_updated'], 1)
        
        # Vérifier que la quantité a été mise à jour
        job_resource = JobDetailRessource.objects.get(job=self.job_valide, ressource=self.resource1)
        self.assertEqual(job_resource.quantity, 3)

    def test_assign_resources_invalid_data(self):
        """Test avec des données invalides."""
        url = reverse('assign-resources-to-jobs')
        
        # Test sans job_ids
        data = {}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test avec job_ids vide
        data = {'job_ids': []}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test avec resource_assignments vide
        data = {
            'job_ids': [self.job_valide.id],
            'resource_assignments': []
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test avec quantity négative
        data = {
            'job_ids': [self.job_valide.id],
            'resource_assignments': [
                {
                    'resource_id': self.resource1.id,
                    'quantity': -1
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_job_resources_success(self):
        """Test de récupération des ressources d'un job."""
        # Créer des affectations
        JobDetailRessource.objects.create(
            job=self.job_valide,
            ressource=self.resource1,
            quantity=2
        )
        JobDetailRessource.objects.create(
            job=self.job_valide,
            ressource=self.resource2,
            quantity=1
        )
        
        url = reverse('get-job-resources', kwargs={'job_id': self.job_valide.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Vérifier les données retournées
        resource_data = response.data[0]
        self.assertIn('id', resource_data)
        self.assertIn('reference', resource_data)
        self.assertIn('resource_id', resource_data)
        self.assertIn('resource_name', resource_data)
        self.assertIn('resource_code', resource_data)
        self.assertIn('quantity', resource_data)

    def test_get_job_resources_nonexistent_job(self):
        """Test de récupération des ressources d'un job inexistant."""
        url = reverse('get-job-resources', kwargs={'job_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_resources_from_job_success(self):
        """Test de suppression réussie de ressources d'un job."""
        # Créer des affectations
        JobDetailRessource.objects.create(
            job=self.job_valide,
            ressource=self.resource1,
            quantity=2
        )
        JobDetailRessource.objects.create(
            job=self.job_valide,
            ressource=self.resource2,
            quantity=1
        )
        
        url = reverse('remove-resources-from-job', kwargs={'job_id': self.job_valide.id})
        
        data = {
            'resource_ids': [self.resource1.id, self.resource3.id]  # resource3 n'existe pas
        }
        
        response = self.client.delete(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['deleted_count'], 1)  # Seule resource1 était affectée
        
        # Vérifier que resource1 a été supprimée mais pas resource2
        self.assertFalse(JobDetailRessource.objects.filter(
            job=self.job_valide, 
            ressource=self.resource1
        ).exists())
        
        self.assertTrue(JobDetailRessource.objects.filter(
            job=self.job_valide, 
            ressource=self.resource2
        ).exists())

    def test_remove_resources_from_job_en_attente_fails(self):
        """Test que la suppression de ressources d'un job EN ATTENTE échoue."""
        url = reverse('remove-resources-from-job', kwargs={'job_id': self.job_en_attente.id})
        
        data = {
            'resource_ids': [self.resource1.id]
        }
        
        response = self.client.delete(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('EN ATTENTE', response.data['error'])

    def test_remove_resources_from_nonexistent_job(self):
        """Test de suppression de ressources d'un job inexistant."""
        url = reverse('remove-resources-from-job', kwargs={'job_id': 99999})
        
        data = {
            'resource_ids': [self.resource1.id]
        }
        
        response = self.client.delete(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_resources_invalid_data(self):
        """Test de suppression avec des données invalides."""
        url = reverse('remove-resources-from-job', kwargs={'job_id': self.job_valide.id})
        
        # Test sans resource_ids
        data = {}
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test avec resource_ids vide
        data = {'resource_ids': []}
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assign_resources_without_authentication(self):
        """Test d'affectation de ressources sans authentification."""
        self.client.force_authenticate(user=None)
        
        url = reverse('assign-resources-to-jobs')
        data = {
            'job_ids': [self.job_valide.id],
            'resource_assignments': [
                {
                    'resource_id': self.resource1.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assign_resources_to_jobs_with_nonexistent_job_blocks_all(self):
        """Test que l'affectation est bloquée si un job n'existe pas."""
        # Préparer les données avec un job inexistant
        data = {
            'job_ids': [self.job_valide.id, 99999, self.job_valide2.id],  # Job 99999 n'existe pas
            'resource_assignments': [
                {'resource_id': self.resource1.id, 'quantity': 2},
                {'resource_id': self.resource2.id, 'quantity': 1}
            ]
        }
        
        url = reverse('assign-resources-to-jobs')
        response = self.client.post(url, data, format='json')
        
        # Vérifier que la requête échoue
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Job avec l\'ID 99999 non trouvé', response.data['error'])
        
        # Vérifier qu'aucune affectation n'a été créée
        self.assertEqual(JobDetailRessource.objects.count(), 0)

    def test_assign_resources_to_jobs_with_invalid_job_status_blocks_all(self):
        """Test que l'affectation est bloquée si un job est en statut EN ATTENTE."""
        # Préparer les données avec un job en statut EN ATTENTE
        data = {
            'job_ids': [self.job_valide.id, self.job_en_attente.id, self.job_valide2.id],
            'resource_assignments': [
                {'resource_id': self.resource1.id, 'quantity': 2},
                {'resource_id': self.resource2.id, 'quantity': 1}
            ]
        }
        
        url = reverse('assign-resources-to-jobs')
        response = self.client.post(url, data, format='json')
        
        # Vérifier que la requête échoue
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('Les ressources ne peuvent pas être affectées au job', response.data['error'])
        
        # Vérifier qu'aucune affectation n'a été créée
        self.assertEqual(JobDetailRessource.objects.count(), 0)

    def test_assign_resources_to_jobs_with_nonexistent_resource_blocks_all(self):
        """Test que l'affectation est bloquée si une ressource n'existe pas."""
        # Préparer les données avec une ressource inexistante
        data = {
            'job_ids': [self.job_valide.id, self.job_valide2.id],
            'resource_assignments': [
                {'resource_id': self.resource1.id, 'quantity': 2},
                {'resource_id': 99999, 'quantity': 1}  # Ressource 99999 n'existe pas
            ]
        }
        
        url = reverse('assign-resources-to-jobs')
        response = self.client.post(url, data, format='json')
        
        # Vérifier que la requête échoue
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Ressource avec l\'ID 99999 non trouvée', response.data['error'])
        
        # Vérifier qu'aucune affectation n'a été créée
        self.assertEqual(JobDetailRessource.objects.count(), 0) 