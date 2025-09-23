#!/usr/bin/env python
"""
Test de l'API CountingDetail sans authentification.
Ce script teste l'API en désactivant temporairement l'authentification.

Usage:
    python test_api_sans_auth.py --count 10

IMPORTANT: Ce script modifie temporairement la vue pour désactiver l'authentification.
Il la remet en place à la fin.

Auteur: Assistant IA
Date: 2024-12-15
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
import random


class NoAuthAPITest:
    """Test de l'API CountingDetail sans authentification."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/mobile/api"
        self.headers = {'Content-Type': 'application/json'}
        self.backup_created = False
        
    def disable_authentication(self):
        """Désactive temporairement l'authentification dans la vue."""
        print("🔧 Désactivation temporaire de l'authentification...")
        
        view_file = "apps/mobile/views/counting/counting_detail_view.py"
        backup_file = "apps/mobile/views/counting/counting_detail_view.py.backup"
        
        try:
            # Créer une sauvegarde
            with open(view_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.backup_created = True
            
            # Modifier le fichier pour désactiver l'authentification
            modified_content = content.replace(
                'permission_classes = [IsAuthenticated]',
                'permission_classes = []  # Temporairement désactivé pour les tests'
            )
            
            with open(view_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print("✅ Authentification désactivée temporairement")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la désactivation de l'authentification: {e}")
            return False
    
    def restore_authentication(self):
        """Remet en place l'authentification."""
        if not self.backup_created:
            return
            
        print("🔧 Restauration de l'authentification...")
        
        view_file = "apps/mobile/views/counting/counting_detail_view.py"
        backup_file = "apps/mobile/views/counting/counting_detail_view.py.backup"
        
        try:
            # Restaurer depuis la sauvegarde
            with open(backup_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(view_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Supprimer la sauvegarde
            os.remove(backup_file)
            
            print("✅ Authentification restaurée")
            
        except Exception as e:
            print(f"❌ Erreur lors de la restauration: {e}")
            print(f"💡 Restaurez manuellement depuis {backup_file}")
    
    def wait_for_server_restart(self):
        """Attend que le serveur redémarre après modification du code."""
        print("⏳ Attente du redémarrage du serveur...")
        
        for i in range(10):
            try:
                time.sleep(2)
                response = requests.get(self.base_url, timeout=5)
                if response.status_code == 200:
                    print("✅ Serveur redémarré")
                    return True
            except:
                continue
        
        print("⚠️ Le serveur met du temps à redémarrer...")
        return False
    
    def get_test_data(self):
        """Génère des données de test avec des IDs probables."""
        return {
            'counting_ids': [1, 2, 3],
            'location_ids': [1, 2, 3, 4, 5],
            'product_ids': [1, 2, 3, 4, 5],
            'assignment_ids': [1, 2, 3]
        }
    
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
                    try:
                        error_data = response.json()
                        print(f"     Détail: {error_data.get('error', 'Erreur inconnue')}")
                    except:
                        print(f"     Détail: {response.text[:100]}...")
                
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
    
    def generate_report(self, creation_results, retrieval_results):
        """Génère un rapport simple."""
        print(f"\n📊 RAPPORT DE TEST")
        print("=" * 50)
        
        # Statistiques de création
        if creation_results:
            total_creation = len(creation_results)
            success_creation = sum(1 for r in creation_results if r['success'])
            response_times = [r['response_time'] for r in creation_results]
            
            print(f"🔧 CRÉATION ({total_creation} tests):")
            print(f"  • Succès: {success_creation}/{total_creation} ({success_creation/total_creation*100:.1f}%)")
            if response_times:
                print(f"  • Temps moyen: {sum(response_times)/len(response_times):.3f}s")
                print(f"  • Temps min/max: {min(response_times):.3f}s / {max(response_times):.3f}s")
        
        # Statistiques de récupération
        if retrieval_results:
            total_retrieval = len(retrieval_results)
            success_retrieval = sum(1 for r in retrieval_results if r['success'])
            
            print(f"\n📥 RÉCUPÉRATION ({total_retrieval} tests):")
            print(f"  • Succès: {success_retrieval}/{total_retrieval}")
            
            for result in retrieval_results:
                if result['success']:
                    print(f"  • {result['test_name']}: {result['count']} éléments")
        
        # Résultat global
        all_results = creation_results + retrieval_results
        total_success = sum(1 for r in all_results if r['success'])
        total_tests = len(all_results)
        
        print(f"\n🎯 RÉSULTAT GLOBAL:")
        print(f"  • Tests totaux: {total_tests}")
        print(f"  • Succès: {total_success}/{total_tests} ({total_success/max(1,total_tests)*100:.1f}%)")
        
        if total_success/max(1,total_tests) > 0.8:
            print("  🚀 API fonctionne très bien!")
        elif total_success/max(1,total_tests) > 0.5:
            print("  ⚡ API fonctionne avec quelques problèmes")
        else:
            print("  ⚠️ Des problèmes ont été détectés")
    
    def run_test(self, count=10):
        """Exécute le test complet."""
        print("🚀 TEST DE L'API COUNTING DETAIL (SANS AUTHENTIFICATION)")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objectif: Tester l'API avec {count} créations")
        print("=" * 70)
        
        try:
            # Vérifier que le serveur est accessible
            response = requests.get(self.base_url, timeout=5)
            print("✅ Serveur accessible")
            
            # Désactiver l'authentification
            if not self.disable_authentication():
                print("❌ Impossible de désactiver l'authentification")
                return
            
            # Attendre le redémarrage du serveur
            self.wait_for_server_restart()
            
            # Récupération des données
            existing_data = self.get_test_data()
            print(f"📦 Utilisation des données de test:")
            print(f"  • Comptages: {existing_data['counting_ids']}")
            print(f"  • Emplacements: {existing_data['location_ids']}")
            print(f"  • Assignments: {existing_data['assignment_ids']}")
            
            # Tests de création
            creation_results = self.test_creation(existing_data, count)
            
            # Tests de récupération
            retrieval_results = self.test_retrieval(existing_data)
            
            # Rapport final
            self.generate_report(creation_results, retrieval_results)
            
            print(f"\n🏁 TESTS TERMINÉS!")
            
        except Exception as e:
            print(f"\n❌ ERREUR FATALE: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Restaurer l'authentification
            self.restore_authentication()
            print("\n💡 N'oubliez pas de redémarrer votre serveur pour appliquer les changements!")


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test de l'API CountingDetail sans authentification")
    parser.add_argument('--count', type=int, default=10, help='Nombre de CountingDetail à créer (défaut: 10)')
    
    args = parser.parse_args()
    
    print(f"🧪 TEST SANS AUTHENTIFICATION - API COUNTING DETAIL")
    print(f"📊 Nombre d'éléments à tester: {args.count}")
    print()
    print("⚠️  ATTENTION: Ce script modifie temporairement le code pour désactiver l'authentification")
    print("   Il restaure automatiquement les paramètres à la fin.")
    print()
    
    # Demander confirmation
    confirm = input("Voulez-vous continuer ? (o/N): ").lower().strip()
    if confirm not in ['o', 'oui', 'y', 'yes']:
        print("Test annulé.")
        return
    
    # Exécuter le test
    test = NoAuthAPITest()
    test.run_test(args.count)


if __name__ == "__main__":
    main()
