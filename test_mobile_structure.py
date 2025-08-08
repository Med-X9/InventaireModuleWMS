#!/usr/bin/env python3
"""
Test pour vérifier que la nouvelle structure mobile fonctionne
"""

import sys
import os

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mobile_structure():
    """Test de la structure mobile"""
    print("=== Test de la structure mobile ===")
    
    try:
        # Test des services
        from apps.mobile.services.auth_service import AuthService
        from apps.mobile.services.sync_service import SyncService
        from apps.mobile.services.inventory_service import InventoryService
        from apps.mobile.services.user_service import UserService
        print("✓ Services importés avec succès")
        
        # Test des repositories
        from apps.mobile.repositories.auth_repository import AuthRepository
        from apps.mobile.repositories.sync_repository import SyncRepository
        from apps.mobile.repositories.inventory_repository import InventoryRepository
        from apps.mobile.repositories.user_repository import UserRepository
        print("✓ Repositories importés avec succès")
        
        # Test des exceptions
        from apps.mobile.exceptions import (
            UserNotFoundException,
            AccountNotFoundException,
            ProductNotFoundException,
            LocationNotFoundException,
            StockNotFoundException,
            InventoryNotFoundException,
            DatabaseConnectionException,
            DataValidationException,
            SyncDataException,
            UploadDataException
        )
        print("✓ Exceptions importées avec succès")
        
        # Test des vues
        from apps.mobile.views import (
            LoginView,
            SyncDataView,
            UserProductsView
        )
        print("✓ Vues importées avec succès")
        
        # Test d'instanciation
        auth_service = AuthService()
        sync_service = SyncService()
        inventory_service = InventoryService()
        user_service = UserService()
        print("✓ Services instanciés avec succès")
        
        auth_repo = AuthRepository()
        sync_repo = SyncRepository()
        inventory_repo = InventoryRepository()
        user_repo = UserRepository()
        print("✓ Repositories instanciés avec succès")
        
        print("\n🎉 Tous les tests de structure mobile réussis!")
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    success = test_mobile_structure()
    sys.exit(0 if success else 1) 