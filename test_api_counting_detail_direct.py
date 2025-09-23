#!/usr/bin/env python
"""
Test direct de l'API CountingDetail avec requests.
Ce script teste l'API en utilisant des requêtes HTTP directes.

Usage:
    python test_api_counting_detail_direct.py

Prérequis:
    - Serveur Django en cours d'exécution (python manage.py runserver)
    - Données existantes dans la base (comptages, emplacements, etc.)

Auteur: Assistant IA
Date: 2024-12-15
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random


class DirectAPITest:
    """Test direct de l'API CountingDetail avec requests."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/mobile/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        
    def authenticate(self):
        """Authentification JWT (optionnelle)."""
        print("🔑 Tentative d'authentification...")
        
        # Données d'authentification par défaut (à adapter selon vos utilisateurs)
        auth_data = {
            'username': 'admin',  # Changez selon votre utilisateur
            'password': 'admin'   # Changez selon votre mot de passe
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/auth/jwt-login/",
                json=auth_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.token = response.json().get('access_token')
                self.headers['Authorization'] = f'Bearer {self.token}'
                print("✅ Authentification réussie")
                return True
            else:
                print(f"⚠️ Authentification échouée: {response.status_code}")
                print("   Continuons sans authentification...")
                return False
                
        except Exception as e:
            print(f"⚠️ Erreur d'authentification: {e}")
            print("   Continuons sans authentification...")
            return False
    
    def get_existing_data(self):
        """Récupère des données existantes via l'API ou utilise des IDs par défaut."""
        print("📦 Récupération des données existantes...")
        
        # IDs par défaut (à adapter selon votre base de données)
        default_data = {
            'counting_ids': [1, 2, 3],
            'location_ids': [1, 2, 3, 4, 5],
            'product_ids': [1, 2, 3, 4, 5],
            'assignment_ids': [1, 2, 3]
        }
        
        print(f"  • Comptages disponibles: {default_data['counting_ids']}")
        print(f"  • Emplacements disponibles: {default_data['location_ids']}")
        print(f"  • Produits disponibles: {default_data['product_ids']}")
        print(f"  • Assignments disponibles: {default_data['assignment_ids']}")
        
        return default_data
    
    def generate_test_data(self, index, existing_data):
        """Génère des données de test pour un CountingDetail."""
        counting_id = random.choice(existing_data['counting_ids'])
        location_id = random.choice(existing_data['location_ids'])
        assignment_id = random.choice(existing_data['assignment_ids'])
        
        data = {
            'counting_id': counting_id,
            'location_id': location_id,
            'quantity_inventoried': random.randint(1, 50),
            'assignment_id': assignment_id
        }
        
        # Ajouter un produit parfois
        if random.choice([True, False]):
            data['product_id'] = random.choice(existing_data['product_ids'])
        
        # Ajouter une DLC parfois
        if random.choice([True, False]):
            future_date = datetime.now() + timedelta(days=random.randint(30, 365))
            data['dlc'] = future_date.strftime('%Y-%m-%d')
        
        # Ajouter un numéro de lot parfois
        if random.choice([True, False]):
            data['n_lot'] = f"LOT-{index:05d}-{random.randint(1000, 9999)}"
        
        # Ajouter des numéros de série parfois
        if random.choice([True, False]) and data.get('product_id'):
            num_series = random.randint(1, 3)
            data['numeros_serie'] = []
            for j in range(num_series):
                data['numeros_serie'].append({
                    'n_serie': f"NS-{index:05d}-{j+1:03d}-{random.randint(1000, 9999)}"
                })
        
        return data
    
    def test_creation(self, existing_data, count=10):
        """Teste la création de CountingDetail."""
        print(f"\n🧪 Test de création de {count} CountingDetail...")
        
        results = []
        for i in range(count):
            data = self.generate_test_data(i + 1, existing_data)
            
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.api_base}/counting-detail/",
                    json=data,
                    headers=self.headers
                )
                
                response_time = time.time() - start_time
                
                result = {
                    'index': i + 1,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 201,
                    'data': data
                }
                
                if response.status_code == 201:
                    result['response_data'] = response.json()
                    print(f"  ✅ CountingDetail {i+1}: Créé en {response_time:.3f}s")
                else:
                    result['error'] = response.text
                    print(f"  ❌ CountingDetail {i+1}: Erreur {response.status_code}")
                    if response.status_code == 400:
                        try:
                            error_data = response.json()
                            print(f"     Détail: {error_data.get('error', 'Erreur de validation')}")
                        except:
                            print(f"     Détail: {response.text[:100]}...")
                    elif response.status_code == 401:
                        print("     Détail: Authentification requise")
                    elif response.status_code == 500:
                        print("     Détail: Erreur serveur interne")
                
                results.append(result)
                
            except Exception as e:
                response_time = time.time() - start_time
                print(f"  ❌ CountingDetail {i+1}: Exception {str(e)}")
                results.append({
                    'index': i + 1,
                    'status_code': 500,
                    'response_time': response_time,
                    'success': False,
                    'error': str(e),
                    'data': data
                })
        
        return results
    
    def test_retrieval(self, existing_data):
        """Teste la récupération des données."""
        print(f"\n📥 Test de récupération des données...")
        
        tests = [
            {
                'name': 'Par comptage',
                'url': f"{self.api_base}/counting-detail/?counting_id={existing_data['counting_ids'][0]}"
            },
            {
                'name': 'Par emplacement',
                'url': f"{self.api_base}/counting-detail/?location_id={existing_data['location_ids'][0]}"
            },
            {
                'name': 'Par produit',
                'url': f"{self.api_base}/counting-detail/?product_id={existing_data['product_ids'][0]}"
            }
        ]
        
        results = []
        for test in tests:
            print(f"  🔍 Test: {test['name']}")
            
            try:
                start_time = time.time()
                response = requests.get(test['url'], headers=self.headers)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get('data', {}).get('counting_details', []))
                    print(f"    ✅ {count} éléments récupérés en {response_time:.3f}s")
                    results.append({
                        'test_name': test['name'],
                        'success': True,
                        'count': count,
                        'response_time': response_time
                    })
                else:
                    print(f"    ❌ Erreur {response.status_code}: {response.text[:100]}...")
                    results.append({
                        'test_name': test['name'],
                        'success': False,
                        'error': response.text
                    })
                    
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                results.append({
                    'test_name': test['name'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_validation_scenarios(self, existing_data):
        """Teste différents scénarios de validation."""
        print(f"\n🧪 Test des scénarios de validation...")
        
        validation_tests = [
            {
                'name': 'Données manquantes - counting_id',
                'data': {
                    'location_id': existing_data['location_ids'][0],
                    'quantity_inventoried': 10,
                    'assignment_id': existing_data['assignment_ids'][0]
                },
                'expected_status': 400
            },
            {
                'name': 'Données manquantes - location_id',
                'data': {
                    'counting_id': existing_data['counting_ids'][0],
                    'quantity_inventoried': 10,
                    'assignment_id': existing_data['assignment_ids'][0]
                },
                'expected_status': 400
            },
            {
                'name': 'Quantité négative',
                'data': {
                    'counting_id': existing_data['counting_ids'][0],
                    'location_id': existing_data['location_ids'][0],
                    'quantity_inventoried': -5,
                    'assignment_id': existing_data['assignment_ids'][0]
                },
                'expected_status': 400
            },
            {
                'name': 'ID inexistant - counting_id',
                'data': {
                    'counting_id': 99999,
                    'location_id': existing_data['location_ids'][0],
                    'quantity_inventoried': 10,
                    'assignment_id': existing_data['assignment_ids'][0]
                },
                'expected_status': 400
            }
        ]
        
        results = []
        for test in validation_tests:
            print(f"  🧪 Test: {test['name']}")
            
            try:
                response = requests.post(
                    f"{self.api_base}/counting-detail/",
                    json=test['data'],
                    headers=self.headers
                )
                
                success = response.status_code == test['expected_status']
                
                if success:
                    print(f"    ✅ Validation correcte (Status: {response.status_code})")
                else:
                    print(f"    ❌ Validation incorrecte (Attendu: {test['expected_status']}, Reçu: {response.status_code})")
                
                results.append({
                    'test_name': test['name'],
                    'expected_status': test['expected_status'],
                    'actual_status': response.status_code,
                    'success': success
                })
                
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                results.append({
                    'test_name': test['name'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def generate_report(self, creation_results, retrieval_results, validation_results):
        """Génère un rapport complet."""
        print(f"\n📊 RAPPORT DE TEST COMPLET")
        print("=" * 60)
        
        # Statistiques de création
        if creation_results:
            total_creation = len(creation_results)
            success_creation = sum(1 for r in creation_results if r['success'])
            response_times = [r['response_time'] for r in creation_results]
            
            print(f"🔧 CRÉATION ({total_creation} tests):")
            print(f"  • Succès: {success_creation}/{total_creation} ({success_creation/total_creation*100:.1f}%)")
            print(f"  • Temps moyen: {sum(response_times)/len(response_times):.3f}s")
            print(f"  • Temps min/max: {min(response_times):.3f}s / {max(response_times):.3f}s")
            
            # Détail des erreurs
            errors = [r for r in creation_results if not r['success']]
            if errors:
                print(f"  • Erreurs principales:")
                error_codes = {}
                for error in errors:
                    code = error['status_code']
                    error_codes[code] = error_codes.get(code, 0) + 1
                for code, count in error_codes.items():
                    print(f"    - Status {code}: {count} occurrences")
        
        # Statistiques de récupération
        if retrieval_results:
            total_retrieval = len(retrieval_results)
            success_retrieval = sum(1 for r in retrieval_results if r['success'])
            
            print(f"\n📥 RÉCUPÉRATION ({total_retrieval} tests):")
            print(f"  • Succès: {success_retrieval}/{total_retrieval}")
            
            for result in retrieval_results:
                if result['success']:
                    print(f"  • {result['test_name']}: {result['count']} éléments")
                else:
                    print(f"  • {result['test_name']}: Échec")
        
        # Statistiques de validation
        if validation_results:
            total_validation = len(validation_results)
            success_validation = sum(1 for r in validation_results if r['success'])
            
            print(f"\n🧪 VALIDATION ({total_validation} tests):")
            print(f"  • Succès: {success_validation}/{total_validation}")
            
            for result in validation_results:
                status = "✅" if result['success'] else "❌"
                print(f"  • {status} {result['test_name']}")
        
        # Résultat global
        all_results = creation_results + retrieval_results + validation_results
        total_success = sum(1 for r in all_results if r['success'])
        total_tests = len(all_results)
        
        print(f"\n🎯 RÉSULTAT GLOBAL:")
        print(f"  • Tests totaux: {total_tests}")
        print(f"  • Succès: {total_success}/{total_tests} ({total_success/max(1,total_tests)*100:.1f}%)")
        
        if total_success/max(1,total_tests) > 0.8:
            print("  🚀 API fonctionne très bien!")
        elif total_success/max(1,total_tests) > 0.6:
            print("  ⚡ API fonctionne correctement avec quelques problèmes")
        else:
            print("  ⚠️ Des problèmes significatifs ont été détectés")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        if creation_results:
            avg_time = sum(r['response_time'] for r in creation_results) / len(creation_results)
            if avg_time > 1.0:
                print("  • Temps de réponse élevé - considérer l'optimisation")
            elif avg_time < 0.2:
                print("  • Excellent temps de réponse!")
        
        error_rate = (len(all_results) - total_success) / max(1, len(all_results))
        if error_rate > 0.2:
            print("  • Taux d'erreur élevé - vérifier la configuration")
        elif error_rate < 0.1:
            print("  • Faible taux d'erreur - très bien!")
    
    def run_full_test(self, count=20):
        """Exécute tous les tests."""
        print("🚀 TEST COMPLET DE L'API COUNTING DETAIL")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objectif: Tester l'API avec {count} créations")
        print(f"🌐 URL de base: {self.api_base}")
        print("=" * 70)
        
        try:
            # Authentification
            self.authenticate()
            
            # Récupération des données
            existing_data = self.get_existing_data()
            
            # Tests de création
            creation_results = self.test_creation(existing_data, count)
            
            # Tests de récupération
            retrieval_results = self.test_retrieval(existing_data)
            
            # Tests de validation
            validation_results = self.test_validation_scenarios(existing_data)
            
            # Rapport final
            self.generate_report(creation_results, retrieval_results, validation_results)
            
            print(f"\n🏁 TOUS LES TESTS TERMINÉS!")
            
        except Exception as e:
            print(f"\n❌ ERREUR FATALE: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test direct de l'API CountingDetail")
    parser.add_argument('--count', type=int, default=10, help='Nombre de CountingDetail à créer (défaut: 10)')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='URL de base du serveur')
    
    args = parser.parse_args()
    
    print(f"🧪 TEST DIRECT - API COUNTING DETAIL")
    print(f"📊 Nombre d'éléments à tester: {args.count}")
    print(f"🌐 URL du serveur: {args.url}")
    print()
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get(args.url, timeout=5)
        print("✅ Serveur accessible")
    except Exception as e:
        print(f"❌ Serveur inaccessible: {e}")
        print("💡 Assurez-vous que le serveur Django fonctionne:")
        print("   python manage.py runserver")
        return
    
    # Exécuter le test
    test = DirectAPITest()
    test.base_url = args.url
    test.api_base = f"{args.url}/mobile/api"
    test.run_full_test(args.count)


if __name__ == "__main__":
    main()
