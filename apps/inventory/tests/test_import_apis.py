"""
Tests pour les APIs d'importation d'inventaires et de stocks.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from apps.masterdata.models import Account, Warehouse, Product, Location, UnitOfMeasure
from apps.inventory.models import Inventory
from apps.users.models import UserApp


class InventoryImportAPITestCase(APITestCase):
    """Tests pour l'API d'importation d'inventaires."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.account = Account.objects.create(name="Test Account")
        self.warehouse1 = Warehouse.objects.create(name="Warehouse 1")
        self.warehouse2 = Warehouse.objects.create(name="Warehouse 2")
        
        # Créer un utilisateur de test
        self.user = UserApp.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_import_inventories_success(self):
        """Test d'importation réussie d'inventaires."""
        url = reverse('inventory-import')
        
        data = {
            "inventories": [
                {
                    "label": "Inventaire Test 1",
                    "date": "2024-03-20T10:00:00Z",
                    "account_id": self.account.id,
                    "warehouse": [
                        {"id": self.warehouse1.id, "date": "2024-12-12"},
                        {"id": self.warehouse2.id, "date": "2024-12-13"}
                    ],
                    "comptages": [
                        {
                            "order": 1,
                            "count_mode": "en vrac",
                            "unit_scanned": True,
                            "entry_quantity": False,
                            "is_variant": False,
                            "stock_situation": False,
                            "quantity_show": True,
                            "show_product": True,
                            "dlc": False,
                            "n_serie": False,
                            "n_lot": False
                        }
                    ]
                }
            ],
            "options": {
                "validate_only": False,
                "stop_on_error": True,
                "return_details": True
            }
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['summary']['total'], 1)
        self.assertEqual(response.data['summary']['success_count'], 1)
        self.assertEqual(response.data['summary']['error_count'], 0)
    
    def test_import_inventories_validation_only(self):
        """Test d'importation avec validation uniquement."""
        url = reverse('inventory-import')
        
        data = {
            "inventories": [
                {
                    "label": "Inventaire Test Validation",
                    "date": "2024-03-20T10:00:00Z",
                    "account_id": self.account.id,
                    "warehouse": [
                        {"id": self.warehouse1.id, "date": "2024-12-12"}
                    ],
                    "comptages": [
                        {
                            "order": 1,
                            "count_mode": "en vrac",
                            "unit_scanned": True,
                            "entry_quantity": False,
                            "is_variant": False,
                            "stock_situation": False,
                            "quantity_show": True,
                            "show_product": True,
                            "dlc": False,
                            "n_serie": False,
                            "n_lot": False
                        }
                    ]
                }
            ],
            "options": {
                "validate_only": True,
                "stop_on_error": True,
                "return_details": True
            }
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'][0]['status'], 'validated')
        
        # Vérifier qu'aucun inventaire n'a été créé
        self.assertEqual(Inventory.objects.count(), 0)
    
    def test_import_inventories_invalid_data(self):
        """Test d'importation avec données invalides."""
        url = reverse('inventory-import')
        
        data = {
            "inventories": [
                {
                    "label": "",  # Label vide
                    "date": "2024-03-20T10:00:00Z",
                    "account_id": self.account.id,
                    "warehouse": [],
                    "comptages": []
                }
            ],
            "options": {
                "validate_only": False,
                "stop_on_error": True,
                "return_details": True
            }
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['summary']['error_count'], 1)
    
    def test_import_inventories_missing_field(self):
        """Test d'importation avec champ manquant."""
        url = reverse('inventory-import')
        
        data = {
            "inventories": [
                {
                    "date": "2024-03-20T10:00:00Z",
                    "account_id": self.account.id,
                    # Label manquant
                    "warehouse": [],
                    "comptages": []
                }
            ]
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class StockImportAPITestCase(APITestCase):
    """Tests pour l'API d'importation de stocks."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.account = Account.objects.create(name="Test Account")
        self.warehouse = Warehouse.objects.create(name="Test Warehouse")
        self.inventory = Inventory.objects.create(
            label="Test Inventory",
            date="2024-03-20T10:00:00Z",
            status="EN PREPARATION"
        )
        
        # Créer des produits et emplacements de test
        self.product1 = Product.objects.create(
            product_name="Product 1",
            Internal_Product_Code="PROD001"
        )
        self.product2 = Product.objects.create(
            product_name="Product 2", 
            Internal_Product_Code="PROD002"
        )
        
        self.location1 = Location.objects.create(
            location_name="Location A1",
            location_reference="LOC-A1"
        )
        self.location2 = Location.objects.create(
            location_name="Location B2",
            location_reference="LOC-B2"
        )
        
        # Créer un utilisateur de test
        self.user = UserApp.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_import_stocks_success(self):
        """Test d'importation réussie de stocks."""
        url = reverse('stock-import', kwargs={'inventory_id': self.inventory.id})
        
        # Créer un fichier Excel de test
        excel_content = b"""article,emplacement,quantite
PROD001,LOC-A1,10
PROD002,LOC-B2,25"""
        
        excel_file = SimpleUploadedFile(
            "stocks.xlsx",
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response = self.client.post(
            url,
            {'file': excel_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['summary']['total_rows'], 2)
        self.assertEqual(response.data['summary']['valid_rows'], 2)
        self.assertEqual(response.data['summary']['invalid_rows'], 0)
    
    def test_import_stocks_no_file(self):
        """Test d'importation sans fichier."""
        url = reverse('stock-import', kwargs={'inventory_id': self.inventory.id})
        
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Aucun fichier fourni', response.data['message'])
    
    def test_import_stocks_invalid_inventory(self):
        """Test d'importation avec inventaire inexistant."""
        url = reverse('stock-import', kwargs={'inventory_id': 99999})
        
        excel_content = b"""article,emplacement,quantite
PROD001,LOC-A1,10"""
        
        excel_file = SimpleUploadedFile(
            "stocks.xlsx",
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response = self.client.post(
            url,
            {'file': excel_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_import_stocks_invalid_product(self):
        """Test d'importation avec produit inexistant."""
        url = reverse('stock-import', kwargs={'inventory_id': self.inventory.id})
        
        excel_content = b"""article,emplacement,quantite
PROD999,LOC-A1,10"""  # Produit inexistant
        
        excel_file = SimpleUploadedFile(
            "stocks.xlsx",
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response = self.client.post(
            url,
            {'file': excel_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['summary']['invalid_rows'], 1)
        self.assertIn('PROD999', str(response.data['errors'])) 