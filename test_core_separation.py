#!/usr/bin/env python3
"""
Script de test pour vérifier la séparation des services et repositories du core
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def test_core_imports():
    """Test des imports du core"""
    print("=== Test des imports du core ===")
    
    try:
        # Test des services
        from core.services.mobile_auth_service import MobileAuthService
        from core.services.mobile_sync_service import MobileSyncService
        print("✅ Services importés avec succès")
        
        # Test des repositories
        from core.repositories.mobile_sync_repository import MobileSyncRepository
        print("✅ Repository importé avec succès")
        
        # Test des exceptions
        from core.exceptions.mobile_exceptions import (
            MobileSyncException,
            InventoryNotFoundException,
            UserNotFoundException,
            StockNotFoundException
        )
        print("✅ Exceptions importées avec succès")
        
        # Test des vues mobile
        from apps.mobile.views import SyncDataView, UserStocksView
        print("✅ Vues mobile importées avec succès")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_service_instantiation():
    """Test de l'instanciation des services"""
    print("\n=== Test d'instanciation des services ===")
    
    try:
        from core.services.mobile_auth_service import MobileAuthService
        from core.services.mobile_sync_service import MobileSyncService
        
        # Instancier les services
        auth_service = MobileAuthService()
        sync_service = MobileSyncService()
        
        print("✅ Services instanciés avec succès")
        print(f"   - AuthService: {type(auth_service)}")
        print(f"   - SyncService: {type(sync_service)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'instanciation: {e}")
        return False

def test_repository_instantiation():
    """Test de l'instanciation du repository"""
    print("\n=== Test d'instanciation du repository ===")
    
    try:
        from core.repositories.mobile_sync_repository import MobileSyncRepository
        
        # Instancier le repository
        repository = MobileSyncRepository()
        
        print("✅ Repository instancié avec succès")
        print(f"   - Repository: {type(repository)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'instanciation: {e}")
        return False

def test_exception_handling():
    """Test de la gestion des exceptions"""
    print("\n=== Test de la gestion des exceptions ===")
    
    try:
        from core.exceptions.mobile_exceptions import (
            MobileSyncException,
            UserNotFoundException,
            StockNotFoundException
        )
        
        # Tester les exceptions
        try:
            raise UserNotFoundException("Test d'exception utilisateur")
        except UserNotFoundException as e:
            print(f"✅ Exception UserNotFoundException capturée: {e}")
        
        try:
            raise StockNotFoundException("Test d'exception stock")
        except StockNotFoundException as e:
            print(f"✅ Exception StockNotFoundException capturée: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de gestion d'exception: {e}")
        return False

def test_mobile_views():
    """Test des vues mobile"""
    print("\n=== Test des vues mobile ===")
    
    try:
        from apps.mobile.views import SyncDataView, UserStocksView
        
        # Vérifier que les vues existent
        print("✅ Vues mobile disponibles:")
        print(f"   - SyncDataView: {SyncDataView}")
        print(f"   - UserStocksView: {UserStocksView}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur des vues mobile: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test de séparation des services et repositories du core")
    print("=" * 60)
    
    tests = [
        test_core_imports,
        test_service_instantiation,
        test_repository_instantiation,
        test_exception_handling,
        test_mobile_views,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés! La séparation fonctionne correctement.")
        return True
    else:
        print("❌ Certains tests ont échoué. Vérifiez la configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 