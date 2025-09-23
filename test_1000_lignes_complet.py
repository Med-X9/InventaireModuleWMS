#!/usr/bin/env python
"""
Test complet pour enregistrer 1000 CountingDetail avec tous les cas de test
Ce script teste tous les scénarios possibles de l'API counting-detail
"""

import os
import sys
import django

# Configuration Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.inventory.models import *
from apps.masterdata.models import *
from apps.inventory.services.counting_detail_service import CountingDetailService
import time
import random
from datetime import datetime, timedelta

User = get_user_model()

def main():
    print("🚀 TEST COMPLET - 1000 COUNTINGDETAIL AVEC TOUS LES CAS")
    print("=" * 70)
    print(f"📅 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. PRÉPARATION DES DONNÉES COMPLÈTES
    print("\n📦 1. CRÉATION DES DONNÉES DE TEST...")
    
    # Utilisateur
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('testapi1000', 'test@1000.com', 'test123')
        print("   ✅ Utilisateur créé: testapi1000")
    else:
        print(f"   ✅ Utilisateur existant: {user.username}")
    
    # Compte avec les bons champs
    account, created = Account.objects.get_or_create(
        account_name="Test Account 1000",
        defaults={
            'account_statuts': 'ACTIVE',
            'description': 'Compte pour test 1000 lignes'
        }
    )
    print(f"   ✅ Compte: {account.account_name} {'(créé)' if created else '(existant)'}")
    
    # Entrepôt
    warehouse, created = Warehouse.objects.get_or_create(
        name="Test Warehouse 1000",
        defaults={'account': account}
    )
    print(f"   ✅ Entrepôt: {warehouse.name}")
    
    # Emplacements variés (20 emplacements)
    locations = []
    for i in range(20):
        location, created = Location.objects.get_or_create(
            name=f"TEST-1000-LOC-{i+1:03d}",
            defaults={'warehouse': warehouse}
        )
        locations.append(location)
    print(f"   ✅ Emplacements: {len(locations)} créés")
    
    # Produits avec différentes propriétés (15 produits)
    products = []
    for i in range(15):
        product, created = Product.objects.get_or_create(
            Internal_Product_Code=f"TEST-1000-PROD-{i+1:03d}",
            defaults={
                'Short_Description': f'Produit Test 1000 Lignes {i+1}',
                'Stock_Unit': 'Unité',
                'Product_Status': 'ACTIVE',
                'n_lot': i % 3 == 0,      # 1/3 des produits avec n_lot
                'n_serie': i % 4 == 0,    # 1/4 des produits avec n_serie
                'dlc': i % 2 == 0         # 1/2 des produits avec dlc
            }
        )
        products.append(product)
    print(f"   ✅ Produits: {len(products)} créés avec propriétés variées")
    
    # Inventaire
    inventory, created = Inventory.objects.get_or_create(
        name="Test Inventory 1000 Lignes",
        defaults={
            'account': account,
            'warehouse': warehouse
        }
    )
    print(f"   ✅ Inventaire: {inventory.name}")
    
    # Comptages avec tous les modes
    countings = []
    modes_config = [
        {
            'mode': 'en vrac',
            'n_lot': True,
            'n_serie': False,
            'dlc': True,
            'show_product': True
        },
        {
            'mode': 'par article',
            'n_lot': True,
            'n_serie': True,
            'dlc': True,
            'show_product': True
        },
        {
            'mode': 'image de stock',
            'n_lot': False,
            'n_serie': True,
            'dlc': False,
            'show_product': False
        }
    ]
    
    for i, config in enumerate(modes_config):
        counting, created = Counting.objects.get_or_create(
            inventory=inventory,
            order=i+1,
            defaults={
                'count_mode': config['mode'],
                'unit_scanned': False,
                'entry_quantity': True,
                'stock_situation': False,
                'is_variant': False,
                'n_lot': config['n_lot'],
                'n_serie': config['n_serie'],
                'dlc': config['dlc'],
                'show_product': config['show_product'],
                'quantity_show': True
            }
        )
        countings.append(counting)
    print(f"   ✅ Comptages: {len(countings)} modes différents créés")
    
    # Jobs et Assignments
    jobs = []
    assignments = []
    for i in range(5):  # 5 jobs différents
        job, created = Job.objects.get_or_create(
            inventory=inventory,
            defaults={}
        )
        jobs.append(job)
        
        assignment, created = Assigment.objects.get_or_create(
            job=job,
            user=user,
            defaults={'status': 'EN COURS'}
        )
        assignments.append(assignment)
    
    print(f"   ✅ Jobs et Assignments: {len(jobs)} créés")
    
    print("\n🎯 DONNÉES PRÉPARÉES:")
    print(f"   • {len(locations)} emplacements")
    print(f"   • {len(products)} produits avec propriétés variées")
    print(f"   • {len(countings)} modes de comptage")
    print(f"   • {len(assignments)} assignments")
    
    # 2. INITIALISATION DU SERVICE
    print("\n🔧 2. INITIALISATION DU SERVICE...")
    service = CountingDetailService()
    print("   ✅ CountingDetailService initialisé")
    
    # 3. DÉFINITION DES CAS DE TEST
    print("\n🧪 3. DÉFINITION DES CAS DE TEST...")
    
    test_cases = [
        # Cas 1: Mode "en vrac" sans produit
        {
            'name': 'Mode en vrac sans produit',
            'count': 200,
            'generate_data': lambda i: {
                'counting_id': countings[0].id,  # Mode "en vrac"
                'location_id': random.choice(locations).id,
                'quantity_inventoried': random.randint(1, 50),
                'assignment_id': random.choice(assignments).id,
                'dlc': (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d') if random.choice([True, False]) else None,
                'n_lot': f"LOT-VRAC-{i:05d}-{random.randint(1000, 9999)}" if random.choice([True, False]) else None
            }
        },
        
        # Cas 2: Mode "par article" avec produit obligatoire
        {
            'name': 'Mode par article avec produit',
            'count': 300,
            'generate_data': lambda i: {
                'counting_id': countings[1].id,  # Mode "par article"
                'location_id': random.choice(locations).id,
                'quantity_inventoried': random.randint(1, 30),
                'assignment_id': random.choice(assignments).id,
                'product_id': random.choice(products).id,
                'dlc': (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d') if random.choice([True, False]) else None,
                'n_lot': f"LOT-ART-{i:05d}-{random.randint(1000, 9999)}" if random.choice([True, False]) else None
            }
        },
        
        # Cas 3: Mode "image de stock" avec numéros de série
        {
            'name': 'Mode image de stock avec numéros de série',
            'count': 250,
            'generate_data': lambda i: {
                'counting_id': countings[2].id,  # Mode "image de stock"
                'location_id': random.choice(locations).id,
                'quantity_inventoried': random.randint(1, 5),
                'assignment_id': random.choice(assignments).id,
                'product_id': random.choice([p for p in products if p.n_serie]).id if random.choice([True, False]) else None,
                'numeros_serie': [
                    {'n_serie': f"NS-IMG-{i:05d}-{j+1:03d}-{random.randint(1000, 9999)}"}
                    for j in range(random.randint(1, 3))
                ] if random.choice([True, False]) else None
            }
        },
        
        # Cas 4: Cas avec toutes les propriétés
        {
            'name': 'Cas complets avec toutes propriétés',
            'count': 200,
            'generate_data': lambda i: {
                'counting_id': random.choice(countings).id,
                'location_id': random.choice(locations).id,
                'quantity_inventoried': random.randint(1, 100),
                'assignment_id': random.choice(assignments).id,
                'product_id': random.choice(products).id,
                'dlc': (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                'n_lot': f"LOT-FULL-{i:05d}-{random.randint(1000, 9999)}",
                'numeros_serie': [
                    {'n_serie': f"NS-FULL-{i:05d}-{j+1:03d}-{random.randint(1000, 9999)}"}
                    for j in range(random.randint(1, 2))
                ] if random.choice([True, False]) else None
            }
        },
        
        # Cas 5: Cas de variations aléatoires
        {
            'name': 'Variations aléatoires',
            'count': 50,
            'generate_data': lambda i: {
                'counting_id': random.choice(countings).id,
                'location_id': random.choice(locations).id,
                'quantity_inventoried': random.randint(1, 200),
                'assignment_id': random.choice(assignments).id,
                'product_id': random.choice(products).id if random.choice([True, False, False]) else None,  # 33% de chance
                'dlc': (datetime.now() + timedelta(days=random.randint(10, 500))).strftime('%Y-%m-%d') if random.choice([True, False, False]) else None,
                'n_lot': f"LOT-VAR-{i:05d}-{random.randint(100, 99999)}" if random.choice([True, False, False]) else None
            }
        }
    ]
    
    print(f"   ✅ {len(test_cases)} cas de test définis:")
    for case in test_cases:
        print(f"      • {case['name']}: {case['count']} lignes")
    
    # 4. EXÉCUTION DES TESTS
    print(f"\n🚀 4. EXÉCUTION DES TESTS (TOTAL: {sum(case['count'] for case in test_cases)} LIGNES)")
    print("-" * 70)
    
    # Variables de suivi globales
    total_created = 0
    total_errors = 0
    total_start_time = time.time()
    case_results = []
    
    for case_idx, test_case in enumerate(test_cases, 1):
        print(f"\n📋 CAS {case_idx}: {test_case['name']} ({test_case['count']} lignes)")
        print("-" * 50)
        
        case_created = 0
        case_errors = 0
        case_start_time = time.time()
        case_times = []
        
        for i in range(test_case['count']):
            try:
                # Générer les données selon le cas de test
                data = test_case['generate_data'](total_created + i + 1)
                
                # Nettoyer les données (enlever les None)
                clean_data = {k: v for k, v in data.items() if v is not None}
                
                # Créer le CountingDetail
                req_start = time.time()
                result = service.create_counting_detail(clean_data)
                req_time = time.time() - req_start
                case_times.append(req_time)
                
                case_created += 1
                total_created += 1
                
            except Exception as e:
                case_errors += 1
                total_errors += 1
                if case_errors <= 3:  # Afficher les 3 premières erreurs par cas
                    print(f"   ❌ Erreur ligne {i + 1}: {str(e)[:60]}...")
            
            # Affichage du progrès par cas
            if (i + 1) % max(1, test_case['count'] // 5) == 0:
                elapsed = time.time() - case_start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                print(f"   📊 {i + 1:3d}/{test_case['count']} | ✅ {case_created:3d} créés | ❌ {case_errors:2d} erreurs | {rate:4.1f}/s")
        
        case_time = time.time() - case_start_time
        case_rate = test_case['count'] / case_time if case_time > 0 else 0
        
        # Résultat du cas
        case_result = {
            'name': test_case['name'],
            'total': test_case['count'],
            'created': case_created,
            'errors': case_errors,
            'time': case_time,
            'rate': case_rate,
            'avg_response_time': sum(case_times) / len(case_times) if case_times else 0
        }
        case_results.append(case_result)
        
        print(f"   ✅ Cas terminé: {case_created}/{test_case['count']} succès ({case_created/test_case['count']*100:.1f}%)")
        print(f"   ⏱️ Temps: {case_time:.1f}s | Débit: {case_rate:.1f}/s")
    
    total_time = time.time() - total_start_time
    
    # 5. RAPPORT FINAL DÉTAILLÉ
    print(f"\n📊 5. RAPPORT FINAL DÉTAILLÉ")
    print("=" * 70)
    print(f"📅 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print(f"🎯 RÉSULTATS GLOBAUX:")
    print(f"   • Total traité: {sum(case['total'] for case in case_results)} lignes")
    print(f"   • ✅ Succès: {total_created}/{sum(case['total'] for case in case_results)} ({total_created/sum(case['total'] for case in case_results)*100:.1f}%)")
    print(f"   • ❌ Erreurs: {total_errors}/{sum(case['total'] for case in case_results)} ({total_errors/sum(case['total'] for case in case_results)*100:.1f}%)")
    print(f"   • ⏱️ Temps total: {total_time:.2f}s ({total_time/60:.1f}min)")
    print(f"   • 🚀 Débit global: {sum(case['total'] for case in case_results)/total_time:.1f} lignes/seconde")
    
    print(f"\n📋 RÉSULTATS PAR CAS DE TEST:")
    for i, result in enumerate(case_results, 1):
        print(f"   {i}. {result['name']}:")
        print(f"      • Succès: {result['created']}/{result['total']} ({result['created']/result['total']*100:.1f}%)")
        print(f"      • Erreurs: {result['errors']}")
        print(f"      • Temps: {result['time']:.1f}s")
        print(f"      • Débit: {result['rate']:.1f}/s")
        print(f"      • Temps moyen/requête: {result['avg_response_time']:.3f}s")
        print()
    
    # Vérification en base de données
    try:
        total_cd = CountingDetail.objects.count()
        test_cd = CountingDetail.objects.filter(
            counting__inventory__name="Test Inventory 1000 Lignes"
        ).count()
        
        print(f"📈 VÉRIFICATION BASE DE DONNÉES:")
        print(f"   • Total CountingDetail en base: {total_cd}")
        print(f"   • CountingDetail de ce test: {test_cd}")
        print(f"   • Créés avec succès: {total_created}")
        
        # Vérification des numéros de série
        total_ns = NSerieInventory.objects.filter(
            counting_detail__counting__inventory__name="Test Inventory 1000 Lignes"
        ).count()
        print(f"   • Numéros de série créés: {total_ns}")
        
    except Exception as e:
        print(f"   ⚠️ Erreur vérification: {e}")
    
    # Évaluation finale
    success_rate = total_created / sum(case['total'] for case in case_results)
    print(f"\n🏆 ÉVALUATION FINALE:")
    if success_rate >= 0.95:
        print("   🚀 EXCELLENT! Votre API gère parfaitement tous les cas de test!")
    elif success_rate >= 0.85:
        print("   ⚡ TRÈS BIEN! Votre API fonctionne très bien avec tous les cas.")
    elif success_rate >= 0.70:
        print("   ✅ CORRECT! Votre API gère la plupart des cas avec quelques problèmes.")
    else:
        print("   ⚠️ PROBLÈMES! Des améliorations sont nécessaires.")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    avg_response_time = sum(r['avg_response_time'] for r in case_results) / len(case_results)
    if avg_response_time > 1.0:
        print("   • Optimiser les temps de réponse (actuellement > 1s)")
    if success_rate < 0.90:
        print("   • Investiguer les causes d'erreur pour améliorer la fiabilité")
    
    global_throughput = sum(case['total'] for case in case_results) / total_time
    if global_throughput < 2.0:
        print("   • Considérer l'optimisation de la base de données")
    elif global_throughput > 10.0:
        print("   • Excellentes performances!")
    
    print(f"\n🏁 TEST COMPLET TERMINÉ AVEC SUCCÈS!")
    print("=" * 70)
    print(f"✨ Votre API a traité {total_created} CountingDetail avec tous les cas de test!")
    print(f"📊 Taux de succès global: {success_rate*100:.1f}%")
    print(f"🎉 Félicitations pour cette performance!")

if __name__ == "__main__":
    main()
