#!/usr/bin/env python3
"""
Test script final pour vérifier que tous les imports sont corrigés
"""

import sys
import os

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_repositories_import():
    """Test des imports des repositories du core"""
    print("=== Test des imports des repositories ===")
    
    try:
        from core.repositories.auth_repository import AuthRepository
        from core.repositories.sync_repository import SyncRepository
        from core.repositories.inventory_repository import InventoryRepository
        from core.repositories.user_repository import UserRepository
        print("✓ Tous les repositories importés avec succès")
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'import des repositories: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue des repositories: {e}")
        return False

def test_core_services_import():
    """Test des imports des services du core"""
    print("\n=== Test des imports des services ===")
    
    try:
        from core.services.auth_service import AuthService
        from core.services.sync_service import SyncService
        from core.services.inventory_service import InventoryService
        from core.services.user_service import UserService
        print("✓ Tous les services importés avec succès")
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'import des services: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue des services: {e}")
        return False

def test_core_exceptions_import():
    """Test des imports des exceptions du core"""
    print("\n=== Test des imports des exceptions ===")
    
    try:
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
        print("✓ Toutes les exceptions importées avec succès")
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'import des exceptions: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue des exceptions: {e}")
        return False

def test_mobile_views_import():
    """Test des imports des vues mobile"""
    print("\n=== Test des imports des vues mobile ===")
    
    try:
        from apps.mobile.views import (
            LoginView,
            LogoutView,
            RefreshTokenView,
            SyncDataView,
            UploadDataView,
            InventoryUsersView,
            UserInventoriesView,
            UserProductsView,
            UserLocationsView,
            UserStocksView
        )
        print("✓ Toutes les vues importées avec succès")
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'import des vues: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue des vues: {e}")
        return False

def test_instantiation():
    """Test de l'instanciation des classes"""
    print("\n=== Test d'instanciation ===")
    
    try:
        # Test des repositories
        auth_repo = AuthRepository()
        sync_repo = SyncRepository()
        inventory_repo = InventoryRepository()
        user_repo = UserRepository()
        print("✓ Tous les repositories instanciés avec succès")
        
        # Test des services
        auth_service = AuthService()
        sync_service = SyncService()
        inventory_service = InventoryService()
        user_service = UserService()
        print("✓ Tous les services instanciés avec succès")
        
        # Test des vues
        login_view = LoginView()
        sync_view = SyncDataView()
        inventory_users_view = InventoryUsersView()
        user_products_view = UserProductsView()
        print("✓ Toutes les vues instanciées avec succès")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur d'instanciation: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("Test final des corrections d'imports")
    print("=" * 50)
    
    tests = [
        test_core_repositories_import,
        test_core_services_import,
        test_core_exceptions_import,
        test_mobile_views_import,
        test_instantiation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"✗ Test {test.__name__} a échoué")
    
    print("\n" + "=" * 50)
    print(f"Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les imports fonctionnent correctement!")
        print("✅ La séparation du core est complète et fonctionnelle")
        return True
    else:
        print("❌ Certains imports ont échoué.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 