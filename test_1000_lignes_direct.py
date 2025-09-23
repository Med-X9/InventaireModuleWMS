#!/usr/bin/env python
"""
Test Direct pour Enregistrer 1000 CountingDetail
Ce script teste l'enregistrement de 1000 lignes dans votre API counting-detail.

Usage:
    python test_1000_lignes_direct.py

Auteur: Assistant IA
Date: 2024-12-15
"""

import os
import sys
import django
import time
import random
from datetime import datetime, timedelta

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from apps.inventory.models import Inventory, Counting, CountingDetail, Job, JobDetail, Assigment
from apps.masterdata.models import Product, Location, Warehouse, Account
import json

User = get_user_model()


class Test1000Lignes:
    """Test pour enregistrer 1000 CountingDetail directement."""
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.test_data = {}
        self.results = {
            'created': 0,
            'errors': 0,
            'times': [],
            'error_details': []
        }
    
    def setup_test_user(self):
        """Crée ou récupère un utilisateur de test."""
        try:
            # Essayer de récupérer un utilisateur existant
            self.test_user = User.objects.filter(is_superuser=True).first()
            if not self.test_user:
                # Créer un nouvel utilisateur
                self.test_user = User.objects.create_user(
                    username='testapi1000',
                    email='testapi1000@example.com',
                    password='testapi123',
                    is_superuser=True,
                    is_staff=True
                )
                print("✅ Nouvel utilisateur de test créé")
            else:
                print(f"✅ Utilisateur existant utilisé: {self.test_user.username}")
            
            # Se connecter
            self.client.force_login(self.test_user)
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
            return False
    
    def get_or_create_test_data(self):
        """Récupère ou crée les données nécessaires pour les tests."""
        print("📦 Préparation des données de test...")
        
        # Récupérer ou créer un compte
        account, created = Account.objects.get_or_create(
            name="Test Account 1000",
            defaults={'description': 'Compte pour test 1000 lignes'}
        )
        if created:
            print("✅ Compte de test créé")
        
        # Récupérer ou créer un entrepôt
        warehouse, created = Warehouse.objects.get_or_create(
            name="Test Warehouse 1000",
            defaults={'account': account}
        )
        if created:
            print("✅ Entrepôt de test créé")
        
        # Créer plusieurs emplacements si nécessaire
        locations = []
        for i in range(20):  # 20 emplacements
            location, created = Location.objects.get_or_create(
                name=f"TEST-1000-LOC-{i+1:03d}",
                defaults={'warehouse': warehouse}
            )
            locations.append(location)
            if created:
                print(f"✅ Emplacement {location.name} créé")
        
        # Créer quelques produits si nécessaire
        products = []
        for i in range(10):  # 10 produits
            product, created = Product.objects.get_or_create(
                Internal_Product_Code=f"TEST-1000-PROD-{i+1:03d}",
                defaults={
                    'Short_Description': f'Produit Test 1000 Lignes {i+1}',
                    'Stock_Unit': 'Unité',
                    'Product_Status': 'ACTIVE',
                    'n_lot': i % 2 == 0,
                    'n_serie': i % 3 == 0,
                    'dlc': i % 2 == 1
                }
            )
            products.append(product)
            if created:
                print(f"✅ Produit {product.Internal_Product_Code} créé")
        
        # Créer un inventaire
        inventory, created = Inventory.objects.get_or_create(
            name="Test Inventory 1000 Lignes",
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
        
        self.test_data = {
            'account': account,
            'warehouse': warehouse,
            'locations': locations,
            'products': products,
            'inventory': inventory,
            'countings': countings,
            'job': job,
            'assignment': assignment
        }
        
        print(f"📊 Données préparées:")
        print(f"  • {len(locations)} emplacements")
        print(f"  • {len(products)} produits")
        print(f"  • {len(countings)} comptages")
        
        return True
    
    def generate_counting_detail_data(self, index):
        """Génère les données pour un CountingDetail."""
        counting = random.choice(self.test_data['countings'])
        location = random.choice(self.test_data['locations'])
        
        data = {
            'counting_id': counting.id,
            'location_id': location.id,
            'quantity_inventoried': random.randint(1, 100),
            'assignment_id': self.test_data['assignment'].id
        }
        
        # Ajouter product_id selon le mode de comptage
        if counting.count_mode == "par article":
            data['product_id'] = random.choice(self.test_data['products']).id
        elif random.choice([True, False]):  # 50% de chance pour les autres modes
            data['product_id'] = random.choice(self.test_data['products']).id
        
        # Ajouter DLC si le comptage le permet
        if counting.dlc and random.choice([True, False]):
            future_date = datetime.now() + timedelta(days=random.randint(30, 365))
            data['dlc'] = future_date.strftime('%Y-%m-%d')
        
        # Ajouter numéro de lot si le comptage le permet
        if counting.n_lot and random.choice([True, False]):
            data['n_lot'] = f"LOT-1000-{index:05d}-{random.randint(1000, 9999)}"
        
        # Ajouter numéros de série si le comptage le permet
        if counting.n_serie and random.choice([True, False]) and data.get('product_id'):
            num_series = random.randint(1, 3)
            data['numeros_serie'] = []
            for j in range(num_series):
                data['numeros_serie'].append({
                    'n_serie': f"NS-1000-{index:05d}-{j+1:03d}-{random.randint(1000, 9999)}"
                })
        
        return data
    
    def create_counting_detail(self, data, index):
        """Crée un CountingDetail via l'API Django."""
        start_time = time.time()
        
        try:
            response = self.client.post(
                reverse('mobile:mobile_counting_detail'),
                data=json.dumps(data),
                content_type='application/json'
            )
            
            response_time = time.time() - start_time
            self.results['times'].append(response_time)
            
            if response.status_code == 201:
                self.results['created'] += 1
                return {
                    'success': True,
                    'index': index,
                    'response_time': response_time,
                    'status_code': response.status_code
                }
            else:
                self.results['errors'] += 1
                error_detail = {
                    'index': index,
                    'status_code': response.status_code,
                    'error': str(response.content),
                    'data': data
                }
                self.results['error_details'].append(error_detail)
                
                return {
                    'success': False,
                    'index': index,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'error': str(response.content)
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            self.results['times'].append(response_time)
            self.results['errors'] += 1
            
            error_detail = {
                'index': index,
                'status_code': 500,
                'error': str(e),
                'data': data
            }
            self.results['error_details'].append(error_detail)
            
            return {
                'success': False,
                'index': index,
                'response_time': response_time,
                'status_code': 500,
                'error': str(e)
            }
    
    def test_1000_lignes(self):
        """Teste l'enregistrement de 1000 CountingDetail."""
        print("\n🚀 DÉMARRAGE DU TEST 1000 LIGNES")
        print("=" * 60)
        print(f"📅 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        start_time = time.time()
        
        for i in range(1000):
            # Générer les données
            data = self.generate_counting_detail_data(i + 1)
            
            # Créer le CountingDetail
            result = self.create_counting_detail(data, i + 1)
            
            # Affichage du progrès
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (1000 - (i + 1)) / rate if rate > 0 else 0
                
                print(f"  📊 Progrès: {i + 1}/1000 ({(i + 1)/10:.1f}%)")
                print(f"     ✅ Créés: {self.results['created']}")
                print(f"     ❌ Erreurs: {self.results['errors']}")
                print(f"     ⏱️ Vitesse: {rate:.1f} req/sec")
                print(f"     ⏳ Temps restant estimé: {remaining/60:.1f} min")
                print()
            elif (i + 1) % 10 == 0:
                if result['success']:
                    print(f"  ✅ {i + 1}: Créé en {result['response_time']:.3f}s")
                else:
                    print(f"  ❌ {i + 1}: Erreur {result['status_code']} en {result['response_time']:.3f}s")
        
        total_time = time.time() - start_time
        
        # Rapport final
        self.generate_final_report(total_time)
    
    def generate_final_report(self, total_time):
        """Génère le rapport final."""
        print("\n📊 RAPPORT FINAL - TEST 1000 LIGNES")
        print("=" * 70)
        
        # Statistiques générales
        print(f"🎯 RÉSULTATS GLOBAUX:")
        print(f"  • Total traité: 1000 lignes")
        print(f"  • Succès: {self.results['created']}/1000 ({self.results['created']/10:.1f}%)")
        print(f"  • Erreurs: {self.results['errors']}/1000 ({self.results['errors']/10:.1f}%)")
        print(f"  • Temps total: {total_time:.2f} secondes ({total_time/60:.1f} minutes)")
        
        # Statistiques de performance
        if self.results['times']:
            avg_time = sum(self.results['times']) / len(self.results['times'])
            min_time = min(self.results['times'])
            max_time = max(self.results['times'])
            throughput = 1000 / total_time
            
            print(f"\n⏱️ PERFORMANCE:")
            print(f"  • Temps moyen par requête: {avg_time:.3f}s")
            print(f"  • Temps min/max: {min_time:.3f}s / {max_time:.3f}s")
            print(f"  • Débit: {throughput:.2f} lignes/seconde")
            print(f"  • Débit: {throughput * 60:.0f} lignes/minute")
        
        # Analyse des erreurs
        if self.results['error_details']:
            print(f"\n❌ ANALYSE DES ERREURS:")
            error_codes = {}
            for error in self.results['error_details'][:10]:  # Limiter à 10 erreurs
                code = error['status_code']
                error_codes[code] = error_codes.get(code, 0) + 1
            
            for code, count in sorted(error_codes.items()):
                print(f"  • Status {code}: {count} occurrences")
            
            if len(self.results['error_details']) > 10:
                print(f"  • ... et {len(self.results['error_details']) - 10} autres erreurs")
        
        # Évaluation finale
        success_rate = self.results['created'] / 1000
        
        print(f"\n🏆 ÉVALUATION:")
        if success_rate >= 0.95:
            print("  🚀 EXCELLENT! Votre API gère parfaitement 1000 lignes!")
        elif success_rate >= 0.85:
            print("  ⚡ TRÈS BIEN! Votre API fonctionne bien avec 1000 lignes.")
        elif success_rate >= 0.70:
            print("  ✅ CORRECT! Votre API gère 1000 lignes avec quelques problèmes.")
        else:
            print("  ⚠️ PROBLÈMES DÉTECTÉS! Des améliorations sont nécessaires.")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        if self.results['times'] and avg_time > 1.0:
            print("  • Optimiser les temps de réponse (actuellement > 1s)")
        if success_rate < 0.90:
            print("  • Investiguer les causes d'erreur pour améliorer la fiabilité")
        if throughput < 2.0:
            print("  • Considérer l'optimisation de la base de données")
        
        print(f"\n🏁 TEST TERMINÉ!")
        print(f"📅 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def cleanup_test_data(self):
        """Nettoie les données de test."""
        print("\n🧹 Nettoyage des données de test...")
        
        try:
            # Supprimer les CountingDetail créés
            deleted_count = CountingDetail.objects.filter(
                counting__inventory__name="Test Inventory 1000 Lignes"
            ).delete()[0]
            
            print(f"✅ {deleted_count} CountingDetail supprimés")
            
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    def run_full_test(self):
        """Exécute le test complet."""
        try:
            print("🧪 TEST D'ENREGISTREMENT DE 1000 LIGNES")
            print("=" * 80)
            print("🎯 Objectif: Enregistrer 1000 CountingDetail dans votre API")
            print("=" * 80)
            
            # Configuration
            if not self.setup_test_user():
                print("❌ Impossible de configurer l'utilisateur de test")
                return
            
            # Préparation des données
            if not self.get_or_create_test_data():
                print("❌ Impossible de préparer les données de test")
                return
            
            # Test principal
            self.test_1000_lignes()
            
            # Nettoyage (optionnel)
            cleanup = input("\n🧹 Voulez-vous nettoyer les données de test ? (o/N): ").lower().strip()
            if cleanup in ['o', 'oui', 'y', 'yes']:
                self.cleanup_test_data()
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Test interrompu par l'utilisateur")
            print(f"📊 Résultats partiels:")
            print(f"  • Créés: {self.results['created']}")
            print(f"  • Erreurs: {self.results['errors']}")
        except Exception as e:
            print(f"\n❌ ERREUR FATALE: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Fonction principale."""
    print("🚀 LANCEMENT DU TEST 1000 LIGNES")
    print()
    print("Ce script va:")
    print("  ✅ Créer les données de test nécessaires")
    print("  ✅ Enregistrer 1000 CountingDetail via votre API")
    print("  ✅ Mesurer les performances")
    print("  ✅ Générer un rapport détaillé")
    print()
    
    confirm = input("Voulez-vous continuer ? (O/n): ").lower().strip()
    if confirm in ['n', 'non', 'no']:
        print("Test annulé.")
        return
    
    # Exécuter le test
    test = Test1000Lignes()
    test.run_full_test()


if __name__ == "__main__":
    main()
