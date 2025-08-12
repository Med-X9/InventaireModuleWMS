#!/usr/bin/env python3
"""
Test script pour vérifier la séparation finale du core
Teste les imports, instanciation et gestion d'exceptions
"""

import sys
import os

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test des imports du core séparé"""
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
        from core.exceptions.auth_exceptions import (
            AuthException, UserNotFoundException, InvalidCredentialsException
        )
        from core.exceptions.sync_exceptions import (
            SyncException, SyncDataException, UploadDataException
        )
        from core.exceptions.inventory_exceptions import (
            InventoryException, InventoryNotFoundException, AccountNotFoundException
        )
        from core.exceptions.user_exceptions import (
            UserException, ProductNotFoundException, LocationNotFoundException, StockNotFoundException
        )
        print("✓ Exceptions importées avec succès")
        
        # Test des vues
        from apps.mobile.views import (
            LoginView, LogoutView, RefreshTokenView,
            SyncDataView, UploadDataView,
            InventoryUsersView, UserInventoriesView,
            UserProductsView, UserLocationsView, UserStocksView
        )
        print("✓ Vues importées avec succès")
        
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
        return False

def test_instantiation():
    """Test de l'instanciation des services"""
    print("\n=== Test d'instanciation ===")
    
    try:
        # Test des services
        auth_service = AuthService()
        sync_service = SyncService()
        inventory_service = InventoryService()
        user_service = UserService()
        print("✓ Services instanciés avec succès")
        
        # Test des repositories
        auth_repo = AuthRepository()
        sync_repo = SyncRepository()
        inventory_repo = InventoryRepository()
        user_repo = UserRepository()
        print("✓ Repositories instanciés avec succès")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur d'instanciation: {e}")
        return False

def test_exceptions():
    """Test de la gestion des exceptions"""
    print("\n=== Test des exceptions ===")
    
    try:
        # Test des exceptions d'authentification
        auth_exception = AuthException("Test auth exception")
        user_not_found = UserNotFoundException("Utilisateur non trouvé")
        invalid_credentials = InvalidCredentialsException("Identifiants invalides")
        print("✓ Exceptions d'authentification créées")
        
        # Test des exceptions de synchronisation
        sync_exception = SyncException("Test sync exception")
        sync_data_exception = SyncDataException("Erreur de synchronisation")
        upload_exception = UploadDataException("Erreur d'upload")
        print("✓ Exceptions de synchronisation créées")
        
        # Test des exceptions d'inventaire
        inventory_exception = InventoryException("Test inventory exception")
        inventory_not_found = InventoryNotFoundException("Inventaire non trouvé")
        account_not_found = AccountNotFoundException("Compte non trouvé")
        print("✓ Exceptions d'inventaire créées")
        
        # Test des exceptions utilisateur
        user_exception = UserException("Test user exception")
        product_not_found = ProductNotFoundException("Produit non trouvé")
        location_not_found = LocationNotFoundException("Location non trouvée")
        stock_not_found = StockNotFoundException("Stock non trouvé")
        print("✓ Exceptions utilisateur créées")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur de création d'exceptions: {e}")
        return False

def test_views():
    """Test de l'instanciation des vues"""
    print("\n=== Test des vues ===")
    
    try:
        # Test des vues d'authentification
        login_view = LoginView()
        logout_view = LogoutView()
        refresh_view = RefreshTokenView()
        print("✓ Vues d'authentification créées")
        
        # Test des vues de synchronisation
        sync_view = SyncDataView()
        upload_view = UploadDataView()
        print("✓ Vues de synchronisation créées")
        
        # Test des vues d'inventaire
        inventory_users_view = InventoryUsersView()
        user_inventories_view = UserInventoriesView()
        print("✓ Vues d'inventaire créées")
        
        # Test des vues utilisateur
        user_products_view = UserProductsView()
        user_locations_view = UserLocationsView()
        user_stocks_view = UserStocksView()
        print("✓ Vues utilisateur créées")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur de création des vues: {e}")
        return False

def test_core_structure():
    """Test de la structure du core"""
    print("\n=== Test de la structure du core ===")
    
    try:
        # Test des imports depuis core
        from core import (
            AuthService, SyncService, InventoryService, UserService,
            AuthRepository, SyncRepository, InventoryRepository, UserRepository
        )
        print("✓ Imports depuis core.__init__ réussis")
        
        # Test des imports depuis core.services
        from core.services import (
            AuthService, SyncService, InventoryService, UserService
        )
        print("✓ Imports depuis core.services réussis")
        
        # Test des imports depuis core.repositories
        from core.repositories import (
            AuthRepository, SyncRepository, InventoryRepository, UserRepository
        )
        print("✓ Imports depuis core.repositories réussis")
        
        # Test des imports depuis core.exceptions
        from core.exceptions import (
            UserNotFoundException, AccountNotFoundException,
            ProductNotFoundException, LocationNotFoundException, StockNotFoundException,
            InventoryNotFoundException, DatabaseConnectionException, DataValidationException,
            SyncDataException, UploadDataException
        )
        print("✓ Imports depuis core.exceptions réussis")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur de structure du core: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("Test de la séparation finale du core")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_instantiation,
        test_exceptions,
        test_views,
        test_core_structure
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
        print("🎉 Tous les tests sont passés! La séparation du core est fonctionnelle.")
        return True
    else:
        print("❌ Certains tests ont échoué. Vérifiez la structure du core.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 