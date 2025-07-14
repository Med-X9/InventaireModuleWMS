from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# Create your tests here.

class InventoryWarehouseStatsTestCase(TestCase):
    """Tests pour l'API de statistiques des warehouses d'un inventaire"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        from django.contrib.auth import get_user_model
        from apps.masterdata.models import Account, Warehouse
        from apps.users.models import UserApp
        from ..models import Inventory, Setting, Job, Counting, Assigment
        
        # Créer un utilisateur pour l'authentification
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Créer un compte
        self.account = Account.objects.create(
            reference='ACC001',
            account_name='Test Account'
        )
        
        # Créer des warehouses
        self.warehouse1 = Warehouse.objects.create(
            reference='WH001',
            warehouse_name='Warehouse 1',
            warehouse_type='CENTRAL',
            status='ACTIVE'
        )
        
        self.warehouse2 = Warehouse.objects.create(
            reference='WH002',
            warehouse_name='Warehouse 2',
            warehouse_type='RECEIVING',
            status='ACTIVE'
        )
        
        # Créer un inventaire
        self.inventory = Inventory.objects.create(
            reference='INV001',
            label='Test Inventory',
            date='2024-01-15',
            status='EN PREPARATION'
        )
        
        # Créer des liens entre l'inventaire et les warehouses
        self.setting1 = Setting.objects.create(
            reference='SET001',
            account=self.account,
            warehouse=self.warehouse1,
            inventory=self.inventory
        )
        
        self.setting2 = Setting.objects.create(
            reference='SET002',
            account=self.account,
            warehouse=self.warehouse2,
            inventory=self.inventory
        )
        
        # Créer des comptages
        self.counting1 = Counting.objects.create(
            reference='CNT001',
            order=1,
            count_mode='image stock',
            inventory=self.inventory
        )
        
        self.counting2 = Counting.objects.create(
            reference='CNT002',
            order=2,
            count_mode='en vrac',
            inventory=self.inventory
        )
        
        # Créer des sessions mobiles (équipes)
        self.session1 = UserApp.objects.create(
            username='mobile1',
            nom='User1',
            prenom='Test',
            type='Mobile'
        )
        
        self.session2 = UserApp.objects.create(
            username='mobile2',
            nom='User2',
            prenom='Test',
            type='Mobile'
        )
        
        # Créer des jobs
        self.job1 = Job.objects.create(
            reference='JOB001',
            status='VALIDE',
            warehouse=self.warehouse1,
            inventory=self.inventory
        )
        
        self.job2 = Job.objects.create(
            reference='JOB002',
            status='VALIDE',
            warehouse=self.warehouse1,
            inventory=self.inventory
        )
        
        self.job3 = Job.objects.create(
            reference='JOB003',
            status='VALIDE',
            warehouse=self.warehouse2,
            inventory=self.inventory
        )
        
        # Créer des affectations
        self.assignment1 = Assigment.objects.create(
            reference='ASS001',
            status='AFFECTE',
            job=self.job1,
            counting=self.counting1,
            session=self.session1
        )
        
        self.assignment2 = Assigment.objects.create(
            reference='ASS002',
            status='AFFECTE',
            job=self.job2,
            counting=self.counting1,
            session=self.session1
        )
        
        self.assignment3 = Assigment.objects.create(
            reference='ASS003',
            status='AFFECTE',
            job=self.job3,
            counting=self.counting2,
            session=self.session2
        )
        
        # Client pour les tests
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_get_warehouse_stats_success(self):
        """Test de récupération réussie des statistiques des warehouses"""
        url = reverse('inventory-warehouse-stats', kwargs={'inventory_id': self.inventory.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'] == 'success')
        self.assertEqual(response.data['inventory_id'], self.inventory.id)
        self.assertEqual(response.data['warehouses_count'], 2)
        
        # Vérifier les données des warehouses
        data = response.data['data']
        self.assertEqual(len(data), 2)
        
        # Vérifier warehouse1
        warehouse1_data = next(w for w in data if w['warehouse_id'] == self.warehouse1.id)
        self.assertEqual(warehouse1_data['warehouse_reference'], 'WH001')
        self.assertEqual(warehouse1_data['warehouse_name'], 'Warehouse 1')
        self.assertEqual(warehouse1_data['jobs_count'], 2)  # job1 et job2
        self.assertEqual(warehouse1_data['teams_count'], 1)  # session1 seulement
        
        # Vérifier warehouse2
        warehouse2_data = next(w for w in data if w['warehouse_id'] == self.warehouse2.id)
        self.assertEqual(warehouse2_data['warehouse_reference'], 'WH002')
        self.assertEqual(warehouse2_data['warehouse_name'], 'Warehouse 2')
        self.assertEqual(warehouse2_data['jobs_count'], 1)  # job3 seulement
        self.assertEqual(warehouse2_data['teams_count'], 1)  # session2 seulement
    
    def test_get_warehouse_stats_inventory_not_found(self):
        """Test avec un inventaire inexistant"""
        url = reverse('inventory-warehouse-stats', kwargs={'inventory_id': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'] == 'success')
        self.assertIn('Inventaire non trouvé', response.data['message'])
    
    def test_get_warehouse_stats_no_warehouses(self):
        """Test avec un inventaire sans warehouses"""
        # Créer un nouvel inventaire sans warehouses
        inventory_no_warehouses = Inventory.objects.create(
            reference='INV002',
            label='Inventory No Warehouses',
            date='2024-01-15',
            status='EN PREPARATION'
        )
        
        url = reverse('inventory-warehouse-stats', kwargs={'inventory_id': inventory_no_warehouses.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'] == 'success')
        self.assertEqual(response.data['warehouses_count'], 0)
        self.assertEqual(len(response.data['data']), 0)
    
    def test_get_warehouse_stats_no_jobs(self):
        """Test avec des warehouses sans jobs"""
        # Créer un warehouse sans jobs
        warehouse_no_jobs = Warehouse.objects.create(
            reference='WH003',
            warehouse_name='Warehouse No Jobs',
            warehouse_type='SHIPPING',
            status='ACTIVE'
        )
        
        setting_no_jobs = Setting.objects.create(
            reference='SET003',
            account=self.account,
            warehouse=warehouse_no_jobs,
            inventory=self.inventory
        )
        
        url = reverse('inventory-warehouse-stats', kwargs={'inventory_id': self.inventory.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'] == 'success')
        self.assertEqual(response.data['warehouses_count'], 3)  # 3 warehouses maintenant
        
        # Vérifier le warehouse sans jobs
        warehouse_no_jobs_data = next(w for w in response.data['data'] if w['warehouse_id'] == warehouse_no_jobs.id)
        self.assertEqual(warehouse_no_jobs_data['jobs_count'], 0)
        self.assertEqual(warehouse_no_jobs_data['teams_count'], 0)
    
    def test_get_warehouse_stats_multiple_teams(self):
        """Test avec plusieurs équipes par warehouse"""
        # Créer une troisième session
        session3 = UserApp.objects.create(
            username='mobile3',
            nom='User3',
            prenom='Test',
            type='Mobile'
        )
        
        # Créer un job supplémentaire pour warehouse1 avec session3
        job4 = Job.objects.create(
            reference='JOB004',
            status='VALIDE',
            warehouse=self.warehouse1,
            inventory=self.inventory
        )
        
        assignment4 = Assigment.objects.create(
            reference='ASS004',
            status='AFFECTE',
            job=job4,
            counting=self.counting2,
            session=session3
        )
        
        url = reverse('inventory-warehouse-stats', kwargs={'inventory_id': self.inventory.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que warehouse1 a maintenant 2 équipes
        warehouse1_data = next(w for w in response.data['data'] if w['warehouse_id'] == self.warehouse1.id)
        self.assertEqual(warehouse1_data['teams_count'], 2)  # session1 et session3
        self.assertEqual(warehouse1_data['jobs_count'], 3)  # job1, job2, job4
    
    def test_get_warehouse_stats_web_users_not_counted(self):
        """Test que les utilisateurs web ne sont pas comptés comme équipes"""
        # Créer un utilisateur web
        web_user = UserApp.objects.create(
            username='webuser',
            nom='Web',
            prenom='User',
            type='Web'
        )
        
        # Créer un job avec affectation à un utilisateur web
        job5 = Job.objects.create(
            reference='JOB005',
            status='VALIDE',
            warehouse=self.warehouse1,
            inventory=self.inventory
        )
        
        assignment5 = Assigment.objects.create(
            reference='ASS005',
            status='AFFECTE',
            job=job5,
            counting=self.counting1,
            session=web_user
        )
        
        url = reverse('inventory-warehouse-stats', kwargs={'inventory_id': self.inventory.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que l'utilisateur web n'est pas compté comme équipe
        warehouse1_data = next(w for w in response.data['data'] if w['warehouse_id'] == self.warehouse1.id)
        # Le nombre d'équipes devrait rester le même (seuls les utilisateurs Mobile sont comptés)
        self.assertEqual(warehouse1_data['teams_count'], 1)  # session1 seulement
