from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import pandas as pd

# Create your tests here.

class InventoryWarehouseStatsTestCase(TestCase):
    """Tests pour l'API de statistiques des warehouses d'un inventaire"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        from django.contrib.auth import get_user_model
        from apps.masterdata.models import Account, Warehouse
        from apps.users.models import UserApp
        from apps.inventory.models import Inventory, Setting, Job, Counting, Assigment, JobDetail
        
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

from apps.inventory.usecases.inventory_launch_validation import InventoryLaunchValidationUseCase
from apps.inventory.models import Inventory, Job, JobDetail, Counting
from apps.masterdata.models import Location, RegroupementEmplacement, Stock
from django.core.exceptions import ValidationError

class InventoryLaunchValidationTournantTestCase(TestCase):
    def setUp(self):
        from apps.masterdata.models import Account, Warehouse, ZoneType, Zone, SousZone, LocationType
        self.account = Account.objects.create(reference='ACC-T', account_name='Compte Tournant')
        self.regroupement = RegroupementEmplacement.objects.create(account=self.account, nom='Regroupement T')
        
        # Créer les objets nécessaires pour Location
        self.warehouse = Warehouse.objects.create(
            reference='WH-T', 
            warehouse_name='Warehouse Test', 
            warehouse_type='CENTRAL', 
            status='ACTIVE'
        )
        self.zone_type = ZoneType.objects.create(
            reference='ZT-T', 
            type_name='Zone Type Test', 
            status='ACTIVE'
        )
        self.zone = Zone.objects.create(
            reference='Z-T', 
            warehouse=self.warehouse, 
            zone_name='Zone Test', 
            zone_type=self.zone_type, 
            zone_status='ACTIVE'
        )
        self.sous_zone = SousZone.objects.create(
            reference='SZ-T', 
            sous_zone_name='Sous Zone Test', 
            zone=self.zone, 
            sous_zone_status='ACTIVE'
        )
        self.location_type = LocationType.objects.create(
            reference='LT-T', 
            name='Location Type Test'
        )
        
        self.location = Location.objects.create(
            reference='LOC-T', 
            location_reference='LOC-REF-T', 
            sous_zone=self.sous_zone, 
            location_type=self.location_type, 
            regroupement=self.regroupement, 
            is_active=True
        )
        from datetime import date
        self.inventory = Inventory.objects.create(
            reference='INV-T', 
            label='Inventaire Tournant', 
            inventory_type='TOURNANT', 
            status='EN PREPARATION',
            date=date.today()
        )
        self.inventory.awi_links.create(account=self.account, warehouse=self.warehouse)
        self.counting = Counting.objects.create(reference='CNT-T', order=1, count_mode='en vrac', inventory=self.inventory)

    def test_no_job_pret_raises_error(self):
        # Aucun job PRET
        Job.objects.create(reference='J1', inventory=self.inventory, status='EN ATTENTE', warehouse=self.warehouse)
        usecase = InventoryLaunchValidationUseCase()
        with self.assertRaises(Exception) as context:
            usecase.validate(self.inventory.id)
        self.assertIn('Au moins un job doit être au statut PRET', str(context.exception))

    def test_no_location_affected_raises_error(self):
        # Un job PRET mais aucun emplacement affecté
        job = Job.objects.create(reference='J2', inventory=self.inventory, status='PRET', warehouse=self.warehouse)
        usecase = InventoryLaunchValidationUseCase()
        with self.assertRaises(Exception) as context:
            usecase.validate(self.inventory.id)
        self.assertIn('Au moins un emplacement doit être affecté', str(context.exception))

    def test_success_with_job_pret_and_location_affected(self):
        # Un job PRET et un emplacement affecté
        job = Job.objects.create(reference='J3', inventory=self.inventory, status='PRET', warehouse=self.warehouse)
        JobDetail.objects.create(job=job, location=self.location)
        usecase = InventoryLaunchValidationUseCase()
        result = usecase.validate(self.inventory.id)
        self.assertTrue(result['success'])
        self.assertIn('Validation OK', result['message'])

class StockImportAPITestCase(TestCase):
    """Tests pour l'API d'importation de stocks"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        from django.contrib.auth import get_user_model
        from apps.masterdata.models import Account, Warehouse, ZoneType, Zone, SousZone, LocationType, RegroupementEmplacement, Location
        from apps.users.models import UserApp
        from apps.inventory.models import Inventory, Setting, Job, Counting, Assigment, JobDetail
        from datetime import date
        
        # Créer un utilisateur pour l'authentification
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            type='Web'
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
            date=date.today(),
            status='EN PREPARATION',
            inventory_type='TOURNANT'
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
            status='PRET',
            warehouse=self.warehouse1,
            inventory=self.inventory
        )
        
        self.job2 = Job.objects.create(
            reference='JOB002',
            status='EN ATTENTE',
            warehouse=self.warehouse2,
            inventory=self.inventory
        )
        
        # Créer le regroupement d'emplacement et les emplacements
        self.regroupement = RegroupementEmplacement.objects.create(
            account=self.account,
            nom='Regroupement Test'
        )
        
        # Créer les objets nécessaires pour Location
        self.zone_type = ZoneType.objects.create(
            reference='ZT001',
            type_name='Zone Type Test',
            status='ACTIVE'
        )
        
        self.zone = Zone.objects.create(
            reference='Z001',
            warehouse=self.warehouse1,
            zone_name='Zone Test',
            zone_type=self.zone_type,
            zone_status='ACTIVE'
        )
        
        self.sous_zone = SousZone.objects.create(
            reference='SZ001',
            sous_zone_name='Sous Zone Test',
            zone=self.zone,
            sous_zone_status='ACTIVE'
        )
        
        self.location_type = LocationType.objects.create(
            reference='LT001',
            name='Location Type Test'
        )
        
        # Créer des emplacements
        self.location1 = Location.objects.create(
            reference='LOC001',
            location_reference='LOC-REF-001',
            sous_zone=self.sous_zone,
            location_type=self.location_type,
            regroupement=self.regroupement,
            is_active=True
        )
        
        self.location2 = Location.objects.create(
            reference='LOC002',
            location_reference='LOC-REF-002',
            sous_zone=self.sous_zone,
            location_type=self.location_type,
            regroupement=self.regroupement,
            is_active=True
        )
        
        # Créer des JobDetail pour lier jobs et emplacements
        self.job_detail1 = JobDetail.objects.create(
            reference='JBD001',
            job=self.job1,
            location=self.location1,
            status='PRET'
        )
        
        self.job_detail2 = JobDetail.objects.create(
            reference='JBD002',
            job=self.job2,
            location=self.location2,
            status='EN ATTENTE'
        )
        
        # Créer des produits pour les tests
        from apps.masterdata.models import Family, Product, UnitOfMeasure
        
        # Créer une famille de produits
        self.family = Family.objects.create(
            reference='FAM001',
            family_name='Famille Test',
            compte=self.account,
            family_status='ACTIVE'
        )
        
        # Créer une unité de mesure avec l'ID 4 (utilisé par défaut dans le service)
        self.unit_of_measure = UnitOfMeasure.objects.create(
            id=4,
            reference='UOM001',
            name='Pièce'
        )
        
        # Créer des produits
        self.product1 = Product.objects.create(
            reference='PRD001',
            Internal_Product_Code='PROD001',
            Short_Description='Produit Test 1',
            Product_Status='ACTIVE',
            Product_Family=self.family,
            Stock_Unit='PIECE'
        )
        
        self.product2 = Product.objects.create(
            reference='PRD002',
            Internal_Product_Code='PROD002',
            Short_Description='Produit Test 2',
            Product_Status='ACTIVE',
            Product_Family=self.family,
            Stock_Unit='PIECE'
        )
        
        # Créer le client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_stock_import_with_valid_locations(self):
        """Test l'import de stocks avec des emplacements valides"""
        # Créer un fichier Excel valide
        data = {
            'article': ['PROD001', 'PROD002'],
            'emplacement': ['LOC-REF-001', 'LOC-REF-002'],
            'quantite': [10, 20]
        }
        df = pd.DataFrame(data)
        
        # Créer le fichier Excel en mémoire
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buffer.seek(0)
        
        # Créer le fichier upload
        excel_file = SimpleUploadedFile(
            'test_stocks.xlsx',
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Appeler l'API
        url = reverse('stock-import', kwargs={'inventory_id': self.inventory.id})
        response = self.client.post(url, {'file': excel_file}, format='multipart')
        
        # Vérifier la réponse
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('Import terminé avec succès', response.data['message'])
        self.assertEqual(response.data['summary']['valid_rows'], 2)
        self.assertEqual(response.data['summary']['invalid_rows'], 0)

    def test_stock_import_without_regroupement(self):
        """Test l'import de stocks sans regroupement d'emplacement"""
        # Supprimer le regroupement d'emplacement
        self.regroupement.delete()
        
        # Créer un fichier Excel
        data = {
            'article': ['PROD001'],
            'emplacement': ['LOC-REF-001'],
            'quantite': [10]
        }
        df = pd.DataFrame(data)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buffer.seek(0)
        
        excel_file = SimpleUploadedFile(
            'test_stocks.xlsx',
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Appeler l'API
        url = reverse('stock-import', kwargs={'inventory_id': self.inventory.id})
        response = self.client.post(url, {'file': excel_file}, format='multipart')
        
        # Vérifier que l'import est refusé
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Aucun regroupement d\'emplacement trouvé', response.data['message'])

    def test_stock_import_without_active_locations(self):
        """Test l'import de stocks sans emplacements actifs"""
        # Désactiver tous les emplacements
        Location.objects.all().update(is_active=False)
        
        # Créer un fichier Excel
        data = {
            'article': ['PROD001'],
            'emplacement': ['LOC-REF-001'],
            'quantite': [10]
        }
        df = pd.DataFrame(data)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buffer.seek(0)
        
        excel_file = SimpleUploadedFile(
            'test_stocks.xlsx',
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Appeler l'API
        url = reverse('stock-import', kwargs={'inventory_id': self.inventory.id})
        response = self.client.post(url, {'file': excel_file}, format='multipart')
        
        # Vérifier que l'import est refusé
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Aucun emplacement actif trouvé', response.data['message'])

    def test_stock_import_without_account_link(self):
        """Test l'import de stocks sans lien de compte"""
        # Supprimer les liens de compte
        from apps.inventory.models import Setting
        Setting.objects.all().delete()
        
        # Créer un fichier Excel
        data = {
            'article': ['PROD001'],
            'emplacement': ['LOC-REF-001'],
            'quantite': [10]
        }
        df = pd.DataFrame(data)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buffer.seek(0)
        
        excel_file = SimpleUploadedFile(
            'test_stocks.xlsx',
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Appeler l'API
        url = reverse('stock-import', kwargs={'inventory_id': self.inventory.id})
        response = self.client.post(url, {'file': excel_file}, format='multipart')
        
        # Vérifier que l'import est refusé
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Aucun compte lié à cet inventaire', response.data['message'])

    def test_stock_import_with_invalid_locations(self):
        """Test l'import de stocks avec des emplacements qui ne font pas partie du regroupement"""
        # Créer un emplacement qui n'appartient pas au regroupement
        other_location = Location.objects.create(
            reference='LOC003',
            location_reference='LOC-REF-003',
            sous_zone=self.sous_zone,
            location_type=self.location_type,
            regroupement=None,  # Pas de regroupement
            is_active=True
        )
        
        # Créer un fichier Excel avec un emplacement invalide
        data = {
            'article': ['PROD001', 'PROD002'],
            'emplacement': ['LOC-REF-001', 'LOC-REF-003'],  # LOC-REF-003 n'est pas dans le regroupement
            'quantite': [10, 20]
        }
        df = pd.DataFrame(data)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buffer.seek(0)
        
        excel_file = SimpleUploadedFile(
            'test_stocks.xlsx',
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Appeler l'API
        url = reverse('stock-import', kwargs={'inventory_id': self.inventory.id})
        response = self.client.post(url, {'file': excel_file}, format='multipart')
        
        # Vérifier que l'import est refusé
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('ne font pas partie du regroupement', response.data['message'])
        self.assertIn('LOC-REF-003', response.data['message'])
