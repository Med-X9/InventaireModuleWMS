#!/usr/bin/env python3
"""
Script de test de performance pour l'API CountingDetail mobile avec 500 lignes.
"""

import os
import sys
import django
import json
import requests
import time
from datetime import datetime

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

# Configuration de l'API
BASE_URL = "http://localhost:8000/mobile/api"
LOGIN_URL = f"{BASE_URL}/auth/jwt-login/"
COUNTING_DETAIL_URL = f"{BASE_URL}/counting-detail/"

class Performance500LinesTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_data = None
        
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
    
    def load_test_data(self):
        """Charge les données de test depuis le fichier JSON."""
        print("📁 Chargement des données de test...")
        
        try:
            with open('test_data_500_lines.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'data' in data and len(data['data']) == 500:
                self.test_data = data['data']
                print(f"✅ {len(self.test_data)} enregistrements chargés")
                return True
            else:
                print("❌ Format de données invalide ou nombre d'enregistrements incorrect")
                return False
                
        except FileNotFoundError:
            print("❌ Fichier test_data_500_lines.json non trouvé")
            print("💡 Exécutez d'abord: python check_database_for_test.py")
            return False
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {str(e)}")
            return False
    
    def test_validation_500_lines(self):
        """Test de validation en lot pour 500 lignes."""
        print("\n📋 Test de validation en lot - 500 lignes...")
        
        validation_data = {
            "data": self.test_data
        }
        
        start_time = time.time()
        
        try:
            response = requests.put(COUNTING_DETAIL_URL, json=validation_data, headers=self.headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data['data']
                    print(f"✅ Validation réussie:")
                    print(f"   - Total traité: {result['total_processed']}")
                    print(f"   - Valides: {result['valid']}")
                    print(f"   - Invalides: {result['invalid']}")
                    print(f"   - Temps de réponse: {response_time:.2f} secondes")
                    print(f"   - Vitesse: {result['total_processed']/response_time:.2f} enregistrements/seconde")
                    
                    if result['errors']:
                        print(f"❌ Erreurs détectées: {len(result['errors'])}")
                        # Afficher les 5 premières erreurs
                        for error in result['errors'][:5]:
                            print(f"   - Index {error['index']}: {error['error']}")
                    
                    return {
                        'success': True,
                        'response_time': response_time,
                        'total_processed': result['total_processed'],
                        'valid': result['valid'],
                        'invalid': result['invalid'],
                        'errors_count': len(result['errors']) if result['errors'] else 0
                    }
                else:
                    print(f"❌ Échec de validation: {data.get('error')}")
                    return {'success': False, 'error': data.get('error')}
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ Erreur lors de la validation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def test_creation_500_lines(self):
        """Test de création en lot pour 500 lignes."""
        print("\n📝 Test de création en lot - 500 lignes...")
        
        creation_data = {
            "batch": True,
            "data": self.test_data
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(COUNTING_DETAIL_URL, json=creation_data, headers=self.headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    result = data['data']
                    print(f"✅ Création réussie:")
                    print(f"   - Total traité: {result['total_processed']}")
                    print(f"   - Réussis: {result['successful']}")
                    print(f"   - Échecs: {result['failed']}")
                    print(f"   - Temps de réponse: {response_time:.2f} secondes")
                    print(f"   - Vitesse: {result['total_processed']/response_time:.2f} enregistrements/seconde")
                    
                    # Statistiques des actions
                    actions = {}
                    for item in result['results']:
                        action = item['result']['action']
                        actions[action] = actions.get(action, 0) + 1
                    
                    print(f"   - Actions effectuées:")
                    for action, count in actions.items():
                        print(f"     * {action}: {count}")
                    
                    if result['errors']:
                        print(f"❌ Erreurs détectées: {len(result['errors'])}")
                        # Afficher les 5 premières erreurs
                        for error in result['errors'][:5]:
                            print(f"   - Index {error['index']}: {error['error']}")
                    
                    return {
                        'success': True,
                        'response_time': response_time,
                        'total_processed': result['total_processed'],
                        'successful': result['successful'],
                        'failed': result['failed'],
                        'actions': actions,
                        'errors_count': len(result['errors']) if result['errors'] else 0
                    }
                else:
                    print(f"❌ Échec de création: {data.get('error')}")
                    return {'success': False, 'error': data.get('error')}
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ Erreur lors de la création: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def test_update_existing_records(self):
        """Test de mise à jour d'enregistrements existants."""
        print("\n🔄 Test de mise à jour d'enregistrements existants...")
        
        # Prendre les 10 premiers enregistrements et modifier leurs quantités
        update_data = {
            "batch": True,
            "data": []
        }
        
        for i, record in enumerate(self.test_data[:10]):
            updated_record = record.copy()
            updated_record['quantity_inventoried'] = record['quantity_inventoried'] + 100  # Ajouter 100
            update_data['data'].append(updated_record)
        
        start_time = time.time()
        
        try:
            response = requests.post(COUNTING_DETAIL_URL, json=update_data, headers=self.headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    result = data['data']
                    print(f"✅ Mise à jour réussie:")
                    print(f"   - Total traité: {result['total_processed']}")
                    print(f"   - Réussis: {result['successful']}")
                    print(f"   - Échecs: {result['failed']}")
                    print(f"   - Temps de réponse: {response_time:.2f} secondes")
                    
                    # Statistiques des actions
                    actions = {}
                    for item in result['results']:
                        action = item['result']['action']
                        actions[action] = actions.get(action, 0) + 1
                    
                    print(f"   - Actions effectuées:")
                    for action, count in actions.items():
                        print(f"     * {action}: {count}")
                    
                    return {
                        'success': True,
                        'response_time': response_time,
                        'total_processed': result['total_processed'],
                        'successful': result['successful'],
                        'failed': result['failed'],
                        'actions': actions
                    }
                else:
                    print(f"❌ Échec de mise à jour: {data.get('error')}")
                    return {'success': False, 'error': data.get('error')}
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_performance_report(self, results):
        """Génère un rapport de performance."""
        print(f"\n📊 RAPPORT DE PERFORMANCE")
        print("=" * 50)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.get('success', False))
        
        print(f"Tests exécutés: {total_tests}")
        print(f"Tests réussis: {successful_tests}")
        print(f"Taux de réussite: {(successful_tests/total_tests)*100:.1f}%")
        
        if 'validation' in results and results['validation'].get('success'):
            val = results['validation']
            print(f"\n📋 Validation 500 lignes:")
            print(f"   - Temps: {val['response_time']:.2f}s")
            print(f"   - Vitesse: {val['total_processed']/val['response_time']:.2f} enregistrements/s")
            print(f"   - Valides: {val['valid']}")
            print(f"   - Invalides: {val['invalid']}")
        
        if 'creation' in results and results['creation'].get('success'):
            cre = results['creation']
            print(f"\n📝 Création 500 lignes:")
            print(f"   - Temps: {cre['response_time']:.2f}s")
            print(f"   - Vitesse: {cre['total_processed']/cre['response_time']:.2f} enregistrements/s")
            print(f"   - Réussis: {cre['successful']}")
            print(f"   - Échecs: {cre['failed']}")
            if 'actions' in cre:
                print(f"   - Actions: {cre['actions']}")
        
        if 'update' in results and results['update'].get('success'):
            upd = results['update']
            print(f"\n🔄 Mise à jour 10 lignes:")
            print(f"   - Temps: {upd['response_time']:.2f}s")
            print(f"   - Vitesse: {upd['total_processed']/upd['response_time']:.2f} enregistrements/s")
            print(f"   - Réussis: {upd['successful']}")
            print(f"   - Échecs: {upd['failed']}")
            if 'actions' in upd:
                print(f"   - Actions: {upd['actions']}")
        
        # Sauvegarder le rapport
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': (successful_tests/total_tests)*100
            },
            'results': results
        }
        
        with open('performance_report_500_lines.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Rapport sauvegardé dans performance_report_500_lines.json")
    
    def run_all_tests(self):
        """Exécute tous les tests de performance."""
        print("🚀 DÉMARRAGE DES TESTS DE PERFORMANCE - 500 LIGNES")
        print("=" * 70)
        
        # Connexion
        if not self.login():
            print("❌ Impossible de se connecter. Arrêt des tests.")
            return False
        
        # Chargement des données
        if not self.load_test_data():
            print("❌ Impossible de charger les données de test. Arrêt des tests.")
            return False
        
        # Tests
        results = {}
        
        # Test de validation
        print(f"\n{'='*50}")
        print("🧪 TEST DE VALIDATION - 500 LIGNES")
        print('='*50)
        results['validation'] = self.test_validation_500_lines()
        
        # Test de création
        print(f"\n{'='*50}")
        print("🧪 TEST DE CRÉATION - 500 LIGNES")
        print('='*50)
        results['creation'] = self.test_creation_500_lines()
        
        # Test de mise à jour
        print(f"\n{'='*50}")
        print("🧪 TEST DE MISE À JOUR - 10 LIGNES")
        print('='*50)
        results['update'] = self.test_update_existing_records()
        
        # Rapport de performance
        self.generate_performance_report(results)
        
        # Résumé final
        print(f"\n{'='*70}")
        print("📊 RÉSUMÉ FINAL")
        print('='*70)
        
        successful_tests = sum(1 for r in results.values() if r.get('success', False))
        total_tests = len(results)
        
        if successful_tests == total_tests:
            print("🎉 Tous les tests de performance sont passés avec succès!")
            print("✅ L'API CountingDetail mobile est prête pour la production!")
            return True
        else:
            print("⚠️  Certains tests de performance ont échoué.")
            return False

def main():
    """Fonction principale."""
    tester = Performance500LinesTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Tests de performance terminés avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Des problèmes ont été détectés lors des tests de performance.")
        sys.exit(1)

if __name__ == "__main__":
    main()
