#!/usr/bin/env python
"""
Test simple pour l'API CountingDetail.
Ce script teste l'API en créant des CountingDetail avec des données existantes.

Usage:
    python test_counting_detail_simple.py

Auteur: Assistant IA
Date: 2024-12-15
"""

import os
import sys
import django
import requests
import json
import time
from datetime import datetime, timedelta

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.inventory.models import Inventory, Counting, CountingDetail, Job, JobDetail, Assigment
from apps.masterdata.models import Product, Location, Warehouse, Account

User = get_user_model()


class SimpleCountingDetailTest:
    """Test simple pour l'API CountingDetail avec des données existantes."""
    
    def __init__(self):
        self.api_client = APIClient()
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/mobile/api"
        self.test_user = None
        self.test_token = None
        
    def setup_test_user(self):
        """Crée ou récupère un utilisateur de test."""
        try:
            self.test_user = User.objects.get(username='test_api_user')
            print("✅ Utilisateur de test existant récupéré")
        except User.DoesNotExist:
            self.test_user = User.objects.create_user(
                username='test_api_user',
                email='test_api@example.com',
                password='testpass123'
            )
            print("✅ Nouvel utilisateur de test créé")
        
        # Authentifier avec le client API Django
        self.api_client.force_authenticate(user=self.test_user)
    
    def get_test_data(self):
        """Récupère des données existantes pour les tests."""
        print("📦 Récupération des données existantes...")
        
        # Récupérer des données existantes
        accounts = list(Account.objects.all()[:5])
        warehouses = list(Warehouse.objects.all()[:5])
        locations = list(Location.objects.all()[:20])
        products = list(Product.objects.all()[:20])
        inventories = list(Inventory.objects.all()[:5])
        countings = list(Counting.objects.all()[:10])
        assignments = list(Assigment.objects.filter(user=self.test_user)[:5])
        
        print(f"  • Comptes: {len(accounts)}")
        print(f"  • Entrepôts: {len(warehouses)}")
        print(f"  • Emplacements: {len(locations)}")
        print(f"  • Produits: {len(products)}")
        print(f"  • Inventaires: {len(inventories)}")
        print(f"  • Comptages: {len(countings)}")
        print(f"  • Assignments: {len(assignments)}")
        
        return {
            'accounts': accounts,
            'warehouses': warehouses,
            'locations': locations,
            'products': products,
            'inventories': inventories,
            'countings': countings,
            'assignments': assignments
        }
    
    def create_minimal_test_data(self):
        """Crée le minimum de données nécessaires si elles n'existent pas."""
        print("🔧 Création des données minimales...")
        
        # Créer un compte si nécessaire
        account, created = Account.objects.get_or_create(
            name="Test Account API",
            defaults={'description': 'Compte pour tests API'}
        )
        if created:
            print("✅ Compte de test créé")
        
        # Créer un entrepôt si nécessaire
        warehouse, created = Warehouse.objects.get_or_create(
            name="Test Warehouse API",
            defaults={'account': account}
        )
        if created:
            print("✅ Entrepôt de test créé")
        
        # Créer quelques emplacements
        locations = []
        for i in range(5):
            location, created = Location.objects.get_or_create(
                name=f"TEST-LOC-{i+1:03d}",
                defaults={'warehouse': warehouse}
            )
            locations.append(location)
            if created:
                print(f"✅ Emplacement {location.name} créé")
        
        # Créer quelques produits
        products = []
        for i in range(5):
            product, created = Product.objects.get_or_create(
                Internal_Product_Code=f"TEST-PROD-{i+1:03d}",
                defaults={
                    'Short_Description': f'Produit Test API {i+1}',
                    'Stock_Unit': 'Unité',
                    'Product_Status': 'ACTIVE',
                    'n_lot': i % 2 == 0,  # Alternance True/False
                    'n_serie': i % 3 == 0,  # Quelques produits avec n_serie
                    'dlc': i % 2 == 1  # Alternance True/False
                }
            )
            products.append(product)
            if created:
                print(f"✅ Produit {product.Internal_Product_Code} créé")
        
        # Créer un inventaire
        inventory, created = Inventory.objects.get_or_create(
            name="Test Inventory API",
            defaults={
                'account': account,
                'warehouse': warehouse
            }
        )
        if created:
            print("✅ Inventaire de test créé")
        
        # Créer des comptages
        countings = []
        count_modes = ["en vrac", "par article", "image de stock"]
        for i, mode in enumerate(count_modes):
            counting, created = Counting.objects.get_or_create(
                inventory=inventory,
                order=i+1,
                defaults={
                    'count_mode': mode,
                    'unit_scanned': False,
                    'entry_quantity': True,
                    'stock_situation': False,
                    'is_variant': False,
                    'n_lot': i % 2 == 0,
                    'n_serie': i % 3 == 0,
                    'dlc': i % 2 == 1,
                    'show_product': True,
                    'quantity_show': True
                }
            )
            countings.append(counting)
            if created:
                print(f"✅ Comptage {mode} créé")
        
        # Créer un job et assignment
        job, created = Job.objects.get_or_create(
            inventory=inventory,
            defaults={}
        )
        if created:
            print("✅ Job de test créé")
        
        assignment, created = Assigment.objects.get_or_create(
            job=job,
            user=self.test_user,
            defaults={'status': 'EN COURS'}
        )
        if created:
            print("✅ Assignment de test créé")
        
        return {
            'account': account,
            'warehouse': warehouse,
            'locations': locations,
            'products': products,
            'inventory': inventory,
            'countings': countings,
            'job': job,
            'assignment': assignment
        }
    
    def test_api_creation(self, test_data, count=10):
        """Teste la création de CountingDetail via l'API."""
        print(f"\n🧪 Test de création de {count} CountingDetail...")
        
        results = []
        for i in range(count):
            # Générer des données de test
            counting = test_data['countings'][i % len(test_data['countings'])]
            location = test_data['locations'][i % len(test_data['locations'])]
            
            data = {
                'counting_id': counting.id,
                'location_id': location.id,
                'quantity_inventoried': (i % 20) + 1,  # Quantité entre 1 et 20
                'assignment_id': test_data['assignment'].id
            }
            
            # Ajouter product_id selon le mode de comptage
            if counting.count_mode == "par article":
                data['product_id'] = test_data['products'][i % len(test_data['products'])].id
            elif i % 2 == 0:  # 50% de chance pour les autres modes
                data['product_id'] = test_data['products'][i % len(test_data['products'])].id
            
            # Ajouter DLC si le comptage le permet
            if counting.dlc:
                future_date = datetime.now() + timedelta(days=30 + (i * 10))
                data['dlc'] = future_date.strftime('%Y-%m-%d')
            
            # Ajouter numéro de lot si le comptage le permet
            if counting.n_lot:
                data['n_lot'] = f"LOT-TEST-{i+1:05d}"
            
            # Test de l'API
            start_time = time.time()
            
            try:
                response = self.api_client.post(
                    '/mobile/api/counting-detail/',
                    data,
                    format='json'
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
                    result['response_data'] = response.data
                    print(f"  ✅ CountingDetail {i+1}: Créé en {response_time:.3f}s")
                else:
                    result['error'] = str(response.data) if hasattr(response, 'data') else str(response.content)
                    print(f"  ❌ CountingDetail {i+1}: Erreur {response.status_code}")
                    print(f"     Détail: {result['error'][:100]}...")
                
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
    
    def test_api_retrieval(self, test_data):
        """Teste la récupération des données via l'API."""
        print(f"\n📥 Test de récupération des données...")
        
        retrieval_tests = [
            {
                'name': 'Par comptage',
                'params': {'counting_id': test_data['countings'][0].id}
            },
            {
                'name': 'Par emplacement',
                'params': {'location_id': test_data['locations'][0].id}
            }
        ]
        
        if test_data['products']:
            retrieval_tests.append({
                'name': 'Par produit',
                'params': {'product_id': test_data['products'][0].id}
            })
        
        results = []
        for test in retrieval_tests:
            print(f"  🔍 Test: {test['name']}")
            
            try:
                start_time = time.time()
                response = self.api_client.get(
                    '/mobile/api/counting-detail/',
                    test['params']
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.data
                    count = len(data.get('data', {}).get('counting_details', []))
                    print(f"    ✅ {count} éléments récupérés en {response_time:.3f}s")
                    results.append({
                        'test_name': test['name'],
                        'success': True,
                        'count': count,
                        'response_time': response_time
                    })
                else:
                    print(f"    ❌ Erreur {response.status_code}: {response.data}")
                    results.append({
                        'test_name': test['name'],
                        'success': False,
                        'error': str(response.data)
                    })
                    
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                results.append({
                    'test_name': test['name'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def generate_simple_report(self, creation_results, retrieval_results):
        """Génère un rapport simple."""
        print(f"\n📊 RAPPORT DE TEST")
        print("=" * 50)
        
        # Statistiques de création
        total_creation = len(creation_results)
        success_creation = sum(1 for r in creation_results if r['success'])
        
        if creation_results:
            response_times = [r['response_time'] for r in creation_results]
            avg_time = sum(response_times) / len(response_times)
            
            print(f"🔧 CRÉATION:")
            print(f"  • Total: {total_creation}")
            print(f"  • Succès: {success_creation} ({success_creation/total_creation*100:.1f}%)")
            print(f"  • Temps moyen: {avg_time:.3f}s")
            print(f"  • Temps min: {min(response_times):.3f}s")
            print(f"  • Temps max: {max(response_times):.3f}s")
        
        # Statistiques de récupération
        total_retrieval = len(retrieval_results)
        success_retrieval = sum(1 for r in retrieval_results if r['success'])
        
        print(f"\n📥 RÉCUPÉRATION:")
        print(f"  • Total: {total_retrieval}")
        print(f"  • Succès: {success_retrieval}/{total_retrieval}")
        
        for result in retrieval_results:
            if result['success']:
                print(f"  • {result['test_name']}: {result['count']} éléments")
            else:
                print(f"  • {result['test_name']}: Échec")
        
        # Conclusion
        overall_success = success_creation + success_retrieval
        overall_total = total_creation + total_retrieval
        
        print(f"\n🎯 RÉSULTAT GLOBAL:")
        print(f"  • Taux de succès: {overall_success}/{overall_total} ({overall_success/max(1,overall_total)*100:.1f}%)")
        
        if overall_success/max(1,overall_total) > 0.8:
            print("  ✅ API fonctionne correctement!")
        else:
            print("  ⚠️ Des problèmes ont été détectés")
    
    def cleanup_test_data(self):
        """Nettoie les données de test créées."""
        print("\n🧹 Nettoyage des données de test...")
        
        try:
            # Supprimer les CountingDetail créés pendant le test
            CountingDetail.objects.filter(
                counting__inventory__name="Test Inventory API"
            ).delete()
            print("✅ CountingDetail de test supprimés")
            
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    def run_test(self, count=50):
        """Exécute le test complet."""
        print("🚀 TEST SIMPLE DE L'API COUNTING DETAIL")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objectif: Tester {count} créations de CountingDetail")
        print("=" * 60)
        
        try:
            # Configuration
            self.setup_test_user()
            
            # Récupérer ou créer les données de test
            existing_data = self.get_test_data()
            
            if not existing_data['countings']:
                print("⚠️ Aucune donnée existante trouvée, création des données minimales...")
                test_data = self.create_minimal_test_data()
            else:
                print("✅ Utilisation des données existantes")
                test_data = existing_data
            
            # Tests de création
            creation_results = self.test_api_creation(test_data, count)
            
            # Tests de récupération
            retrieval_results = self.test_api_retrieval(test_data)
            
            # Rapport
            self.generate_simple_report(creation_results, retrieval_results)
            
            print(f"\n🏁 TEST TERMINÉ!")
            
        except Exception as e:
            print(f"\n❌ ERREUR FATALE: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Nettoyage
            self.cleanup_test_data()


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test simple de l'API CountingDetail")
    parser.add_argument('--count', type=int, default=10, help='Nombre de CountingDetail à créer (défaut: 10)')
    
    args = parser.parse_args()
    
    print(f"🧪 TEST SIMPLE - API COUNTING DETAIL")
    print(f"📊 Nombre d'éléments à tester: {args.count}")
    print()
    
    # Exécuter le test
    test = SimpleCountingDetailTest()
    test.run_test(args.count)


if __name__ == "__main__":
    main()
