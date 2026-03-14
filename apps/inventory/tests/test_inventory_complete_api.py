"""
Tests pour l'API de finalisation d'inventaire.
Vérifie que l'inventaire ne peut être marqué comme terminé que si tous ses jobs sont terminés.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import Inventory, Job
from apps.masterdata.models import Warehouse, Account

User = get_user_model()


class InventoryCompleteAPITestCase(TestCase):
    """Tests pour l'API de finalisation d'inventaire"""
    
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
        
        # Créer un compte
        self.account = Account.objects.create(
            reference='ACC001',
            account_name='Test Account'
        )
        
        # Créer un warehouse
        self.warehouse = Warehouse.objects.create(
            reference='WH001',
            warehouse_name='Test Warehouse',
            warehouse_type='CENTRAL',
            status='ACTIVE'
        )
        
        # Créer un inventaire en statut EN REALISATION
        self.inventory = Inventory.objects.create(
            reference='INV001',
            label='Test Inventory',
            date=timezone.now(),
            status='EN REALISATION',
            en_realisation_status_date=timezone.now()
        )
    
    def test_complete_inventory_with_all_jobs_terminated(self):
        """Test que l'inventaire peut être finalisé quand tous les jobs sont terminés"""
        # Créer des jobs terminés
        job1 = Job.objects.create(
            reference='JOB001',
            status='TERMINE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            termine_date=timezone.now()
        )
        
        job2 = Job.objects.create(
            reference='JOB002',
            status='TERMINE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            termine_date=timezone.now()
        )
        
        # Appeler l'API de finalisation
        url = reverse('inventory-complete', kwargs={'pk': self.inventory.id})
        response = self.client.post(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertEqual(
            response.data['message'],
            "L'inventaire a été marqué comme terminé avec succès"
        )
        
        # Vérifier que l'inventaire a été mis à jour
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.status, 'TERMINE')
        self.assertIsNotNone(self.inventory.termine_status_date)
    
    def test_complete_inventory_with_some_jobs_not_terminated(self):
        """Test que l'inventaire ne peut pas être finalisé si certains jobs ne sont pas terminés"""
        # Créer un job terminé et un job non terminé
        job1 = Job.objects.create(
            reference='JOB001',
            status='TERMINE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            termine_date=timezone.now()
        )
        
        job2 = Job.objects.create(
            reference='JOB002',
            status='EN ATTENTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        # Appeler l'API de finalisation
        url = reverse('inventory-complete', kwargs={'pk': self.inventory.id})
        response = self.client.post(url)
        
        # Vérifier la réponse d'erreur
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('JOB002', response.data['error'])
        self.assertIn('EN ATTENTE', response.data['error'])
        
        # Vérifier que l'inventaire n'a pas été mis à jour
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.status, 'EN REALISATION')
        self.assertIsNone(self.inventory.termine_status_date)
    
    def test_complete_inventory_with_no_jobs(self):
        """Test que l'inventaire ne peut pas être finalisé s'il n'y a pas de jobs"""
        # Appeler l'API de finalisation sans jobs
        url = reverse('inventory-complete', kwargs={'pk': self.inventory.id})
        response = self.client.post(url)
        
        # Vérifier la réponse d'erreur
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Aucun job trouvé', response.data['error'])
        
        # Vérifier que l'inventaire n'a pas été mis à jour
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.status, 'EN REALISATION')
    
    def test_complete_inventory_not_in_realisation_status(self):
        """Test que l'inventaire ne peut pas être finalisé s'il n'est pas en statut EN REALISATION"""
        # Changer le statut de l'inventaire
        self.inventory.status = 'EN PREPARATION'
        self.inventory.save()
        
        # Créer des jobs terminés
        Job.objects.create(
            reference='JOB001',
            status='TERMINE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            termine_date=timezone.now()
        )
        
        # Appeler l'API de finalisation
        url = reverse('inventory-complete', kwargs={'pk': self.inventory.id})
        response = self.client.post(url)
        
        # Vérifier la réponse d'erreur
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('EN PREPARATION', response.data['error'])
        
        # Vérifier que l'inventaire n'a pas été mis à jour
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.status, 'EN PREPARATION')
    
    def test_complete_inventory_not_found(self):
        """Test que l'API retourne une erreur 404 si l'inventaire n'existe pas"""
        # Appeler l'API avec un ID inexistant
        url = reverse('inventory-complete', kwargs={'pk': 99999})
        response = self.client.post(url)
        
        # Vérifier la réponse d'erreur
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_complete_inventory_with_multiple_jobs_different_statuses(self):
        """Test avec plusieurs jobs ayant différents statuts"""
        # Créer des jobs avec différents statuts
        Job.objects.create(
            reference='JOB001',
            status='TERMINE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            termine_date=timezone.now()
        )
        
        Job.objects.create(
            reference='JOB002',
            status='TERMINE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            termine_date=timezone.now()
        )
        
        Job.objects.create(
            reference='JOB003',
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        Job.objects.create(
            reference='JOB004',
            status='PRET',
            warehouse=self.warehouse,
            inventory=self.inventory
        )
        
        # Appeler l'API de finalisation
        url = reverse('inventory-complete', kwargs={'pk': self.inventory.id})
        response = self.client.post(url)
        
        # Vérifier la réponse d'erreur
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('JOB003', response.data['error'])
        self.assertIn('JOB004', response.data['error'])
        self.assertIn('AFFECTE', response.data['error'])
        self.assertIn('PRET', response.data['error'])
        
        # Vérifier que l'inventaire n'a pas été mis à jour
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.status, 'EN REALISATION')
    
    def test_complete_inventory_success_with_single_job(self):
        """Test que l'inventaire peut être finalisé avec un seul job terminé"""
        # Créer un seul job terminé
        Job.objects.create(
            reference='JOB001',
            status='TERMINE',
            warehouse=self.warehouse,
            inventory=self.inventory,
            termine_date=timezone.now()
        )
        
        # Appeler l'API de finalisation
        url = reverse('inventory-complete', kwargs={'pk': self.inventory.id})
        response = self.client.post(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Vérifier que l'inventaire a été mis à jour
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.status, 'TERMINE')
        self.assertIsNotNone(self.inventory.termine_status_date)

