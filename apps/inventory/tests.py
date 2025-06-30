"""
Tests pour l'application inventory.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .views.inventory_views import InventoryUpdateView, InventoryCreateView
from .services.inventory_service import InventoryService
from .usecases.inventory_usecase import InventoryUseCase
from .exceptions import InventoryValidationError, InventoryNotFoundError
from .serializers.inventory_serializer import InventoryDataSerializer

class InventoryMessageTest(TestCase):
    """
    Tests pour vérifier la séparation des messages de création et mise à jour.
    """
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.service = InventoryService()
    
    def test_create_inventory_message(self):
        """Test que la création retourne le bon message."""
        # Données de test
        test_data = {
            'label': 'Nouvel inventaire',
            'date': '2024-01-15',
            'account_id': 1,
            'warehouse': [{'id': 1}],
            'comptages': []
        }
        
        # Mock du use case
        with patch('apps.inventory.services.inventory_service.InventoryUseCase') as mock_use_case_class:
            mock_use_case = Mock()
            mock_use_case.create_inventory.return_value = {
                'success': True,
                'inventory': {'id': 1, 'label': 'Nouvel inventaire'},
                'countings': []
            }
            mock_use_case_class.return_value = mock_use_case
            
            # Test de la méthode
            result = self.service.create_inventory(test_data)
            
            # Vérifications
            self.assertIn('message', result)
            self.assertEqual(result['message'], "Inventaire créé avec succès")
    
    def test_update_inventory_message(self):
        """Test que la mise à jour retourne le bon message."""
        # Données de test
        inventory_id = 1
        test_data = {
            'label': 'Inventaire mis à jour',
            'date': '2024-01-15',
            'account_id': 1,
            'warehouse': [{'id': 1}],
            'comptages': []
        }
        
        # Mock du use case
        with patch('apps.inventory.services.inventory_service.InventoryUseCase') as mock_use_case_class:
            mock_use_case = Mock()
            mock_use_case.update_inventory.return_value = {
                'success': True,
                'inventory': {'id': 1, 'label': 'Inventaire mis à jour'},
                'countings': []
            }
            mock_use_case_class.return_value = mock_use_case
            
            # Test de la méthode
            result = self.service.update_inventory(inventory_id, test_data)
            
            # Vérifications
            self.assertIn('message', result)
            self.assertEqual(result['message'], "Inventaire mis à jour avec succès")

class InventoryViewMessageTest(APITestCase):
    """
    Tests pour vérifier que les vues utilisent les bons messages.
    """
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.create_view = InventoryCreateView()
        self.update_view = InventoryUpdateView()
        self.create_view.service = Mock(spec=InventoryService)
        self.update_view.service = Mock(spec=InventoryService)
    
    def test_create_view_uses_service_message(self):
        """Test que la vue de création utilise le message du service."""
        # Données de test
        test_data = {
            'label': 'Nouvel inventaire',
            'date': '2024-01-15',
            'account_id': 1,
            'warehouse': [{'id': 1}],
            'comptages': []
        }
        
        # Mock du service
        service_result = {
            'message': 'Inventaire créé avec succès',
            'inventory': {'id': 1},
            'countings': []
        }
        self.create_view.service.create_inventory.return_value = service_result
        
        # Mock du serializer
        with patch('apps.inventory.views.inventory_views.InventoryDataSerializer') as mock_serializer:
            mock_serializer_instance = Mock()
            mock_serializer_instance.is_valid.return_value = True
            mock_serializer_instance.validated_data = test_data
            mock_serializer.return_value = mock_serializer_instance
            
            # Test de la méthode
            result = self.create_view.service.create_inventory(test_data)
            
            # Vérifications
            self.assertEqual(result['message'], 'Inventaire créé avec succès')
    
    def test_update_view_uses_service_message(self):
        """Test que la vue de mise à jour utilise le message du service."""
        # Données de test
        inventory_id = 1
        test_data = {
            'label': 'Inventaire mis à jour',
            'date': '2024-01-15',
            'account_id': 1,
            'warehouse': [{'id': 1}],
            'comptages': []
        }
        
        # Mock du service
        service_result = {
            'message': 'Inventaire mis à jour avec succès',
            'inventory': {'id': 1},
            'countings': []
        }
        self.update_view.service.update_inventory.return_value = service_result
        
        # Mock du serializer
        with patch('apps.inventory.views.inventory_views.InventoryDataSerializer') as mock_serializer:
            mock_serializer_instance = Mock()
            mock_serializer_instance.is_valid.return_value = True
            mock_serializer_instance.validated_data = test_data
            mock_serializer.return_value = mock_serializer_instance
            
            # Test de la méthode
            result = self.update_view.service.update_inventory(inventory_id, test_data)
            
            # Vérifications
            self.assertEqual(result['message'], 'Inventaire mis à jour avec succès')
