#!/usr/bin/env python3
"""
Test script pour vérifier que les imports sont corrigés
"""

import sys
import os

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_exceptions_import():
    """Test des imports des exceptions du core"""
    print("=== Test des imports des exceptions ===")
    
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
        print(f"✗ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
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
        print(f"✗ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("Test des corrections d'imports")
    print("=" * 40)
    
    tests = [
        test_core_exceptions_import,
        test_mobile_views_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"✗ Test {test.__name__} a échoué")
    
    print("\n" + "=" * 40)
    print(f"Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les imports fonctionnent correctement!")
        return True
    else:
        print("❌ Certains imports ont échoué.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 