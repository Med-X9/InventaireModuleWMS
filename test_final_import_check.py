#!/usr/bin/env python3
"""
Test simple pour vérifier que tous les imports sont corrigés
"""

import sys
import os

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test des imports principaux"""
    print("=== Test des imports ===")
    
    try:
        # Test des services
        from core.services.auth_service import AuthService
        from core.services.sync_service import SyncService
        from core.services.inventory_service import InventoryService
        from core.services.user_service import UserService
        print("✓ Services importés avec succès")
        
        # Test des repositories
        from core.repositories.auth_repository import AuthRepository
        from core.repositories.sync_repository import SyncRepository
        from core.repositories.inventory_repository import InventoryRepository
        from core.repositories.user_repository import UserRepository
        print("✓ Repositories importés avec succès")
        
        # Test des exceptions
        from core.exceptions import (
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
        
        print("\n🎉 Tous les imports fonctionnent correctement!")
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 