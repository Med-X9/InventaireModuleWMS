#!/usr/bin/env python3
"""
Script de test pour l'API CountingDetail mobile avec support des lots.
Teste la validation et création en lot avec vérification des enregistrements existants.
"""

import os
import sys
import django
import json
import requests
from datetime import datetime, date

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

# Configuration de l'API
BASE_URL = "http://localhost:8000/mobile/api"
LOGIN_URL = f"{BASE_URL}/auth/jwt-login/"
COUNTING_DETAIL_URL = f"{BASE_URL}/counting-detail/"

class MobileCountingDetailBatchTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        
    def login(self, username="testuser_api", password="testpass123"):
        """Connexion et récupération du token JWT."""
        print("🔐 Connexion...")
        
        login_data = {
            "username": username,
            "password": password
        }
        
        try:
            response = requests.post(LOGIN_URL, json=login_data)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data['access']
                    self.headers = {
                        'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json'
                    }
                    print("✅ Connexion réussie")
                    return True
                else:
                    print(f"❌ Erreur de connexion: {data.get('error')}")
                    return False
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {str(e)}")
            return False
    
    def test_validation_batch(self):
        """Test de validation en lot."""
        print("\n📋 Test de validation en lot...")
        
        # Données de test pour la validation
        validation_data = {
            "data": [
                {
                    "counting_id": 1,
                    "location_id": 1,
                    "quantity_inventoried": 10,
                    "assignment_id": 1,
                    "product_id": 1,
                    "dlc": "2024-12-31",
                    "n_lot": "LOT123",
                    "numeros_serie": [{"n_serie": "NS001"}]
                },
                {
                    "counting_id": 1,
                    "location_id": 2,
                    "quantity_inventoried": 5,
                    "assignment_id": 1,
                    "product_id": 2,
                    "dlc": "2024-11-30",
                    "n_lot": "LOT456"
                },
                {
                    "counting_id": 1,
                    "location_id": 3,
                    "quantity_inventoried": 3,
                    "assignment_id": 1,
                    "product_id": 3,
                    "numeros_serie": [
                        {"n_serie": "NS002"},
                        {"n_serie": "NS003"}
                    ]
                }
            ]
        }
        
        try:
            response = requests.put(COUNTING_DETAIL_URL, json=validation_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data['data']
                    print(f"✅ Validation réussie:")
                    print(f"   - Total traité: {result['total_processed']}")
                    print(f"   - Valides: {result['valid']}")
                    print(f"   - Invalides: {result['invalid']}")
                    
                    # Afficher les détails
                    for item in result['results']:
                        print(f"   - Index {item['index']}: {'✅ Valide' if item['valid'] else '❌ Invalide'}")
                        print(f"     Existe: {'Oui' if item['exists'] else 'Non'}")
                        print(f"     Action: {item['action_needed']}")
                        if item['existing_id']:
                            print(f"     ID existant: {item['existing_id']}")
                    
                    if result['errors']:
                        print(f"❌ Erreurs détectées:")
                        for error in result['errors']:
                            print(f"   - Index {error['index']}: {error['error']}")
                    
                    return True
                else:
                    print(f"❌ Échec de validation: {data.get('error')}")
                    return False
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la validation: {str(e)}")
            return False
    
    def test_creation_batch(self):
        """Test de création en lot."""
        print("\n📝 Test de création en lot...")
        
        # Données de test pour la création
        creation_data = {
            "batch": True,
            "data": [
                {
                    "counting_id": 1,
                    "location_id": 1,
                    "quantity_inventoried": 15,
                    "assignment_id": 1,
                    "product_id": 1,
                    "dlc": "2024-12-31",
                    "n_lot": "LOT123",
                    "numeros_serie": [{"n_serie": "NS001"}]
                },
                {
                    "counting_id": 1,
                    "location_id": 2,
                    "quantity_inventoried": 8,
                    "assignment_id": 1,
                    "product_id": 2,
                    "dlc": "2024-11-30",
                    "n_lot": "LOT456"
                },
                {
                    "counting_id": 1,
                    "location_id": 4,
                    "quantity_inventoried": 7,
                    "assignment_id": 1,
                    "product_id": 4,
                    "numeros_serie": [
                        {"n_serie": "NS004"},
                        {"n_serie": "NS005"}
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(COUNTING_DETAIL_URL, json=creation_data, headers=self.headers)
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    result = data['data']
                    print(f"✅ Création réussie:")
                    print(f"   - Total traité: {result['total_processed']}")
                    print(f"   - Réussis: {result['successful']}")
                    print(f"   - Échecs: {result['failed']}")
                    
                    # Afficher les détails des résultats
                    for item in result['results']:
                        print(f"   - Index {item['index']}: {item['result']['action']}")
                        cd = item['result']['counting_detail']
                        print(f"     ID: {cd['id']}, Référence: {cd['reference']}")
                        print(f"     Quantité: {cd['quantity_inventoried']}")
                        if item['result'].get('numeros_serie'):
                            print(f"     Numéros de série: {len(item['result']['numeros_serie'])}")
                    
                    if result['errors']:
                        print(f"❌ Erreurs détectées:")
                        for error in result['errors']:
                            print(f"   - Index {error['index']}: {error['error']}")
                    
                    return True
                else:
                    print(f"❌ Échec de création: {data.get('error')}")
                    return False
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la création: {str(e)}")
            return False
    
    def test_creation_single(self):
        """Test de création d'un seul enregistrement."""
        print("\n📝 Test de création d'un seul enregistrement...")
        
        # Données de test pour un seul enregistrement
        single_data = {
            "counting_id": 1,
            "location_id": 5,
            "quantity_inventoried": 12,
            "assignment_id": 1,
            "product_id": 5,
            "dlc": "2024-10-15",
            "n_lot": "LOT789",
            "numeros_serie": [{"n_serie": "NS006"}]
        }
        
        try:
            response = requests.post(COUNTING_DETAIL_URL, json=single_data, headers=self.headers)
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    result = data['data']
                    print(f"✅ Création réussie:")
                    cd = result['counting_detail']
                    print(f"   - ID: {cd['id']}")
                    print(f"   - Référence: {cd['reference']}")
                    print(f"   - Quantité: {cd['quantity_inventoried']}")
                    print(f"   - Produit: {cd['product_id']}")
                    print(f"   - Emplacement: {cd['location_id']}")
                    
                    if result.get('numeros_serie'):
                        print(f"   - Numéros de série: {len(result['numeros_serie'])}")
                        for ns in result['numeros_serie']:
                            print(f"     * {ns['n_serie']} (ID: {ns['id']})")
                    
                    return True
                else:
                    print(f"❌ Échec de création: {data.get('error')}")
                    return False
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la création: {str(e)}")
            return False
    
    def test_service_import(self):
        """Test d'importation du service mobile."""
        print("\n🔧 Test d'importation du service mobile...")
        
        try:
            from apps.mobile.services.counting_detail_service import CountingDetailService
            from apps.mobile.exceptions import CountingDetailValidationError
            
            service = CountingDetailService()
            print("✅ Service mobile importé avec succès")
            print("✅ Exceptions mobiles importées avec succès")
            
            return True
        except ImportError as e:
            print(f"❌ Erreur d'importation: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Erreur inattendue: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests."""
        print("🚀 Démarrage des tests de l'API CountingDetail Mobile avec support des lots")
        print("=" * 70)
        
        # Test de connexion
        if not self.login():
            print("❌ Impossible de se connecter. Arrêt des tests.")
            return False
        
        # Tests
        tests = [
            ("Import du service mobile", self.test_service_import),
            ("Validation en lot", self.test_validation_batch),
            ("Création d'un seul enregistrement", self.test_creation_single),
            ("Création en lot", self.test_creation_batch)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"🧪 {test_name}")
            print('='*50)
            
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                print(f"❌ Erreur inattendue: {str(e)}")
                results.append((test_name, False))
        
        # Résumé
        print(f"\n{'='*70}")
        print("📊 RÉSUMÉ DES TESTS")
        print('='*70)
        
        passed = 0
        for test_name, success in results:
            status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
            print(f"{status} - {test_name}")
            if success:
                passed += 1
        
        print(f"\nRésultat: {passed}/{len(results)} tests réussis")
        
        if passed == len(results):
            print("🎉 Tous les tests sont passés avec succès!")
            return True
        else:
            print("⚠️  Certains tests ont échoué.")
            return False

def main():
    """Fonction principale."""
    tester = MobileCountingDetailBatchTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ L'API CountingDetail Mobile avec support des lots fonctionne correctement!")
        sys.exit(0)
    else:
        print("\n❌ Des problèmes ont été détectés avec l'API.")
        sys.exit(1)

if __name__ == "__main__":
    main()
