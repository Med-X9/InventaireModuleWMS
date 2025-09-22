#!/usr/bin/env python
"""
Test de l'API CountingDetail avec cURL et authentification.
Ce script génère des commandes cURL pour tester l'API.

Usage:
    python test_curl_1000.py --count 50

Auteur: Assistant IA
Date: 2024-12-15
"""

import subprocess
import json
import time
import random
from datetime import datetime, timedelta
import os


class CurlAPITest:
    """Test de l'API CountingDetail avec cURL."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/mobile/api"
        self.token = None
        
    def authenticate_with_curl(self):
        """Authentification avec cURL."""
        print("🔑 Authentification avec cURL...")
        
        # Essayer différents utilisateurs
        users_to_try = [
            {'username': 'admin', 'password': 'admin'},
            {'username': 'test', 'password': 'test'},
            {'username': 'user', 'password': 'user'},
        ]
        
        for user in users_to_try:
            print(f"  Tentative avec {user['username']}/{user['password']}...")
            
            auth_data = json.dumps(user)
            
            curl_cmd = [
                'curl', '-s', '-X', 'POST',
                f"{self.api_base}/auth/jwt-login/",
                '-H', 'Content-Type: application/json',
                '-d', auth_data
            ]
            
            try:
                result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    try:
                        response = json.loads(result.stdout)
                        if 'access_token' in response:
                            self.token = response['access_token']
                            print(f"  ✅ Authentification réussie avec {user['username']}")
                            return True
                        else:
                            print(f"  ❌ Pas de token dans la réponse: {result.stdout[:100]}...")
                    except json.JSONDecodeError:
                        print(f"  ❌ Réponse non-JSON: {result.stdout[:100]}...")
                else:
                    print(f"  ❌ Erreur cURL: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("  ❌ Timeout lors de l'authentification")
            except Exception as e:
                print(f"  ❌ Exception: {e}")
        
        print("⚠️ Authentification échouée avec tous les utilisateurs testés")
        print("💡 Continuons sans authentification (peut échouer si l'API l'exige)")
        return False
    
    def get_test_data(self):
        """Génère des données de test."""
        return {
            'counting_ids': [1, 2, 3],
            'location_ids': [1, 2, 3, 4, 5],
            'product_ids': [1, 2, 3, 4, 5],
            'assignment_ids': [1, 2, 3]
        }
    
    def generate_counting_detail_data(self, index, existing_data):
        """Génère des données pour un CountingDetail."""
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
        
        return data
    
    def create_counting_detail_curl(self, data, index):
        """Crée un CountingDetail avec cURL."""
        json_data = json.dumps(data)
        
        # Préparer les headers
        headers = ['-H', 'Content-Type: application/json']
        if self.token:
            headers.extend(['-H', f'Authorization: Bearer {self.token}'])
        
        curl_cmd = [
            'curl', '-s', '-w', '\\n%{http_code}',
            '-X', 'POST',
            f"{self.api_base}/counting-detail/",
            *headers,
            '-d', json_data
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
            response_time = time.time() - start_time
            
            if result.returncode == 0:
                # Séparer la réponse du code HTTP
                output_lines = result.stdout.strip().split('\\n')
                if len(output_lines) >= 2:
                    response_body = '\\n'.join(output_lines[:-1])
                    status_code = output_lines[-1]
                else:
                    response_body = result.stdout
                    status_code = "200"  # Défaut
                
                try:
                    status_code = int(status_code)
                except ValueError:
                    status_code = 500
                
                return {
                    'index': index,
                    'status_code': status_code,
                    'response_time': response_time,
                    'success': status_code == 201,
                    'response_body': response_body,
                    'data': data
                }
            else:
                return {
                    'index': index,
                    'status_code': 500,
                    'response_time': response_time,
                    'success': False,
                    'error': result.stderr,
                    'data': data
                }
                
        except subprocess.TimeoutExpired:
            return {
                'index': index,
                'status_code': 408,
                'response_time': time.time() - start_time,
                'success': False,
                'error': 'Timeout',
                'data': data
            }
        except Exception as e:
            return {
                'index': index,
                'status_code': 500,
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e),
                'data': data
            }
    
    def test_creation_batch(self, existing_data, count=10):
        """Teste la création de plusieurs CountingDetail."""
        print(f"\\n🧪 Test de création de {count} CountingDetail avec cURL...")
        
        results = []
        for i in range(count):
            data = self.generate_counting_detail_data(i + 1, existing_data)
            result = self.create_counting_detail_curl(data, i + 1)
            results.append(result)
            
            if result['success']:
                print(f"  ✅ CountingDetail {i+1}: Créé en {result['response_time']:.3f}s")
            else:
                print(f"  ❌ CountingDetail {i+1}: Erreur {result['status_code']} en {result['response_time']:.3f}s")
                if result.get('error'):
                    print(f"     Détail: {result['error'][:100]}...")
                elif result.get('response_body'):
                    try:
                        error_data = json.loads(result['response_body'])
                        print(f"     Détail: {error_data.get('error', 'Erreur inconnue')}")
                    except:
                        print(f"     Détail: {result['response_body'][:100]}...")
            
            # Petite pause pour éviter de surcharger le serveur
            if i > 0 and i % 10 == 0:
                time.sleep(0.5)
        
        return results
    
    def test_retrieval_curl(self, existing_data):
        """Teste la récupération des données avec cURL."""
        print(f"\\n📥 Test de récupération des données avec cURL...")
        
        tests = [
            {
                'name': 'Par comptage',
                'url': f"{self.api_base}/counting-detail/?counting_id={existing_data['counting_ids'][0]}"
            },
            {
                'name': 'Par emplacement',
                'url': f"{self.api_base}/counting-detail/?location_id={existing_data['location_ids'][0]}"
            }
        ]
        
        results = []
        for test in tests:
            print(f"  🔍 Test: {test['name']}")
            
            # Préparer les headers
            headers = []
            if self.token:
                headers.extend(['-H', f'Authorization: Bearer {self.token}'])
            
            curl_cmd = [
                'curl', '-s', '-w', '\\n%{http_code}',
                *headers,
                test['url']
            ]
            
            try:
                start_time = time.time()
                result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=15)
                response_time = time.time() - start_time
                
                if result.returncode == 0:
                    output_lines = result.stdout.strip().split('\\n')
                    if len(output_lines) >= 2:
                        response_body = '\\n'.join(output_lines[:-1])
                        status_code = int(output_lines[-1])
                    else:
                        response_body = result.stdout
                        status_code = 200
                    
                    if status_code == 200:
                        try:
                            data = json.loads(response_body)
                            count = len(data.get('data', {}).get('counting_details', []))
                            print(f"    ✅ {count} éléments récupérés en {response_time:.3f}s")
                            results.append({
                                'test_name': test['name'],
                                'success': True,
                                'count': count,
                                'response_time': response_time
                            })
                        except json.JSONDecodeError:
                            print(f"    ❌ Réponse non-JSON: {response_body[:100]}...")
                            results.append({
                                'test_name': test['name'],
                                'success': False,
                                'error': 'Invalid JSON'
                            })
                    else:
                        print(f"    ❌ Erreur {status_code}: {response_body[:100]}...")
                        results.append({
                            'test_name': test['name'],
                            'success': False,
                            'error': f"HTTP {status_code}"
                        })
                else:
                    print(f"    ❌ Erreur cURL: {result.stderr}")
                    results.append({
                        'test_name': test['name'],
                        'success': False,
                        'error': result.stderr
                    })
                    
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                results.append({
                    'test_name': test['name'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def generate_report(self, creation_results, retrieval_results):
        """Génère un rapport de test."""
        print(f"\\n📊 RAPPORT DE TEST AVEC CURL")
        print("=" * 60)
        
        # Statistiques de création
        if creation_results:
            total_creation = len(creation_results)
            success_creation = sum(1 for r in creation_results if r['success'])
            response_times = [r['response_time'] for r in creation_results if 'response_time' in r]
            
            print(f"🔧 CRÉATION ({total_creation} tests):")
            print(f"  • Succès: {success_creation}/{total_creation} ({success_creation/total_creation*100:.1f}%)")
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                print(f"  • Temps moyen: {avg_time:.3f}s")
                print(f"  • Temps min/max: {min(response_times):.3f}s / {max(response_times):.3f}s")
            
            # Analyse des erreurs
            errors = [r for r in creation_results if not r['success']]
            if errors:
                error_codes = {}
                for error in errors:
                    code = error['status_code']
                    error_codes[code] = error_codes.get(code, 0) + 1
                
                print(f"  • Erreurs:")
                for code, count in sorted(error_codes.items()):
                    print(f"    - Status {code}: {count} occurrences")
        
        # Statistiques de récupération
        if retrieval_results:
            total_retrieval = len(retrieval_results)
            success_retrieval = sum(1 for r in retrieval_results if r['success'])
            
            print(f"\\n📥 RÉCUPÉRATION ({total_retrieval} tests):")
            print(f"  • Succès: {success_retrieval}/{total_retrieval}")
            
            for result in retrieval_results:
                if result['success']:
                    print(f"  • {result['test_name']}: {result['count']} éléments")
                else:
                    print(f"  • {result['test_name']}: Échec")
        
        # Résultat global
        all_results = creation_results + retrieval_results
        total_success = sum(1 for r in all_results if r['success'])
        total_tests = len(all_results)
        
        print(f"\\n🎯 RÉSULTAT GLOBAL:")
        print(f"  • Tests totaux: {total_tests}")
        print(f"  • Succès: {total_success}/{total_tests} ({total_success/max(1,total_tests)*100:.1f}%)")
        
        if total_success/max(1,total_tests) > 0.8:
            print("  🚀 API fonctionne très bien!")
        elif total_success/max(1,total_tests) > 0.5:
            print("  ⚡ API fonctionne avec quelques problèmes")
        else:
            print("  ⚠️ Des problèmes significatifs ont été détectés")
        
        # Recommandations
        if creation_results and response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time > 1.0:
                print("\\n💡 RECOMMANDATIONS:")
                print("  • Temps de réponse élevé - considérer l'optimisation")
            elif avg_time < 0.2:
                print("\\n💡 EXCELLENT:")
                print("  • Très bon temps de réponse!")
    
    def run_test(self, count=50):
        """Exécute le test complet."""
        print("🚀 TEST DE L'API COUNTING DETAIL AVEC CURL")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objectif: Tester l'API avec {count} créations")
        print(f"🌐 URL de base: {self.api_base}")
        print("=" * 70)
        
        # Vérifier que cURL est disponible
        try:
            subprocess.run(['curl', '--version'], capture_output=True, check=True)
            print("✅ cURL disponible")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ cURL non disponible. Installez cURL pour utiliser ce script.")
            return
        
        try:
            # Vérifier que le serveur est accessible
            result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', self.base_url], 
                                  capture_output=True, text=True, timeout=10)
            if result.stdout == '200':
                print("✅ Serveur accessible")
            else:
                print(f"⚠️ Serveur répond avec le code: {result.stdout}")
            
            # Authentification
            self.authenticate_with_curl()
            
            # Données de test
            existing_data = self.get_test_data()
            print(f"\\n📦 Utilisation des données de test:")
            print(f"  • Comptages: {existing_data['counting_ids']}")
            print(f"  • Emplacements: {existing_data['location_ids']}")
            print(f"  • Assignments: {existing_data['assignment_ids']}")
            
            # Tests de création
            creation_results = self.test_creation_batch(existing_data, count)
            
            # Tests de récupération
            retrieval_results = self.test_retrieval_curl(existing_data)
            
            # Rapport final
            self.generate_report(creation_results, retrieval_results)
            
            print(f"\\n🏁 TESTS TERMINÉS!")
            
        except Exception as e:
            print(f"\\n❌ ERREUR FATALE: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test de l'API CountingDetail avec cURL")
    parser.add_argument('--count', type=int, default=20, help='Nombre de CountingDetail à créer (défaut: 20)')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='URL de base du serveur')
    
    args = parser.parse_args()
    
    print(f"🧪 TEST AVEC CURL - API COUNTING DETAIL")
    print(f"📊 Nombre d'éléments à tester: {args.count}")
    print(f"🌐 URL du serveur: {args.url}")
    print()
    
    # Exécuter le test
    test = CurlAPITest()
    test.base_url = args.url
    test.api_base = f"{args.url}/mobile/api"
    test.run_test(args.count)


if __name__ == "__main__":
    main()
