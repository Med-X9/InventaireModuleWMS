#!/usr/bin/env python
"""
Test Simple pour 1000 CountingDetail
Script ultra-simple pour enregistrer 1000 lignes.
"""

import os
import sys
import django

# Configuration Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.inventory.models import Inventory, Counting, CountingDetail, Assigment
from apps.masterdata.models import Product, Location, Warehouse, Account
from apps.inventory.services.counting_detail_service import CountingDetailService
import time
import random
from datetime import datetime, timedelta

User = get_user_model()

def main():
    print("🚀 TEST SIMPLE - 1000 COUNTINGDETAIL")
    print("=" * 50)
    
    # Créer ou récupérer un utilisateur
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_superuser('testuser', 'test@test.com', 'test123')
            print("✅ Utilisateur créé")
        else:
            print(f"✅ Utilisateur existant: {user.username}")
    except Exception as e:
        print(f"❌ Erreur utilisateur: {e}")
        return
    
    # Récupérer ou créer les données de base
    try:
        # Compte
        account = Account.objects.first()
        if not account:
            account = Account.objects.create(name="Test Account", description="Test")
            print("✅ Compte créé")
        
        # Entrepôt
        warehouse = Warehouse.objects.first()
        if not warehouse:
            warehouse = Warehouse.objects.create(name="Test Warehouse", account=account)
            print("✅ Entrepôt créé")
        
        # Emplacements
        locations = list(Location.objects.all()[:10])
        if not locations:
            for i in range(10):
                loc = Location.objects.create(name=f"LOC-{i+1:03d}", warehouse=warehouse)
                locations.append(loc)
            print("✅ 10 emplacements créés")
        
        # Produits
        products = list(Product.objects.all()[:5])
        if not products:
            for i in range(5):
                prod = Product.objects.create(
                    Internal_Product_Code=f"PROD-{i+1:03d}",
                    Short_Description=f"Produit {i+1}",
                    Stock_Unit="Unité",
                    Product_Status="ACTIVE"
                )
                products.append(prod)
            print("✅ 5 produits créés")
        
        # Inventaire
        inventory = Inventory.objects.first()
        if not inventory:
            inventory = Inventory.objects.create(
                name="Test Inventory",
                account=account,
                warehouse=warehouse
            )
            print("✅ Inventaire créé")
        
        # Comptage
        counting = Counting.objects.first()
        if not counting:
            counting = Counting.objects.create(
                inventory=inventory,
                order=1,
                count_mode="en vrac",
                unit_scanned=False,
                entry_quantity=True,
                stock_situation=False,
                is_variant=False,
                n_lot=False,
                n_serie=False,
                dlc=False,
                show_product=True,
                quantity_show=True
            )
            print("✅ Comptage créé")
        
        # Assignment
        assignment = Assigment.objects.filter(user=user).first()
        if not assignment:
            from apps.inventory.models import Job
            job = Job.objects.first()
            if not job:
                job = Job.objects.create(inventory=inventory)
            assignment = Assigment.objects.create(
                job=job,
                user=user,
                status='EN COURS'
            )
            print("✅ Assignment créé")
        
        print(f"📦 Données disponibles:")
        print(f"  • Emplacements: {len(locations)}")
        print(f"  • Produits: {len(products)}")
        print(f"  • Comptage ID: {counting.id}")
        print(f"  • Assignment ID: {assignment.id}")
        
    except Exception as e:
        print(f"❌ Erreur préparation données: {e}")
        return
    
    # Service pour créer les CountingDetail
    service = CountingDetailService()
    
    # Variables de suivi
    created = 0
    errors = 0
    times = []
    start_time = time.time()
    
    print(f"\n🧪 CRÉATION DE 1000 COUNTINGDETAIL...")
    print(f"📅 Début: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    # Créer 1000 CountingDetail
    for i in range(1000):
        try:
            # Générer des données aléatoires
            data = {
                'counting_id': counting.id,
                'location_id': random.choice(locations).id,
                'quantity_inventoried': random.randint(1, 50),
                'assignment_id': assignment.id
            }
            
            # Ajouter un produit parfois
            if random.choice([True, False]):
                data['product_id'] = random.choice(products).id
            
            # Ajouter une DLC parfois
            if random.choice([True, False]):
                future_date = datetime.now() + timedelta(days=random.randint(30, 365))
                data['dlc'] = future_date.strftime('%Y-%m-%d')
            
            # Ajouter un lot parfois
            if random.choice([True, False]):
                data['n_lot'] = f"LOT-{i+1:05d}-{random.randint(1000, 9999)}"
            
            # Créer le CountingDetail
            req_start = time.time()
            result = service.create_counting_detail(data)
            req_time = time.time() - req_start
            times.append(req_time)
            
            created += 1
            
            # Affichage du progrès
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (1000 - (i + 1)) / rate if rate > 0 else 0
                
                print(f"  📊 {i + 1}/1000 ({(i + 1)/10:.1f}%) - "
                      f"✅ {created} créés, ❌ {errors} erreurs - "
                      f"{rate:.1f} req/s - "
                      f"ETA: {remaining/60:.1f}min")
            elif (i + 1) % 25 == 0:
                print(f"  ✅ {i + 1}/1000 - Temps: {req_time:.3f}s")
                
        except Exception as e:
            errors += 1
            if errors <= 5:  # Afficher seulement les 5 premières erreurs
                print(f"  ❌ Erreur {i + 1}: {str(e)[:100]}...")
    
    total_time = time.time() - start_time
    
    # Rapport final
    print(f"\n📊 RAPPORT FINAL")
    print("=" * 50)
    print(f"🎯 RÉSULTATS:")
    print(f"  • Total traité: 1000 lignes")
    print(f"  • ✅ Succès: {created}/1000 ({created/10:.1f}%)")
    print(f"  • ❌ Erreurs: {errors}/1000 ({errors/10:.1f}%)")
    print(f"  • ⏱️ Temps total: {total_time:.2f}s ({total_time/60:.1f}min)")
    
    if times:
        avg_time = sum(times) / len(times)
        throughput = 1000 / total_time
        
        print(f"\n⚡ PERFORMANCE:")
        print(f"  • Temps moyen/requête: {avg_time:.3f}s")
        print(f"  • Temps min/max: {min(times):.3f}s / {max(times):.3f}s")
        print(f"  • Débit: {throughput:.2f} lignes/seconde")
        print(f"  • Débit: {throughput * 60:.0f} lignes/minute")
        print(f"  • Débit: {throughput * 3600:.0f} lignes/heure")
    
    # Évaluation
    success_rate = created / 1000
    print(f"\n🏆 ÉVALUATION:")
    if success_rate >= 0.95:
        print("  🚀 EXCELLENT! Votre API gère parfaitement 1000 lignes!")
    elif success_rate >= 0.85:
        print("  ⚡ TRÈS BIEN! Votre API fonctionne bien avec 1000 lignes.")
    elif success_rate >= 0.70:
        print("  ✅ CORRECT! Votre API gère 1000 lignes avec quelques problèmes.")
    else:
        print("  ⚠️ PROBLÈMES! Des améliorations sont nécessaires.")
    
    # Vérification en base
    try:
        total_cd = CountingDetail.objects.count()
        print(f"\n📈 VÉRIFICATION BASE DE DONNÉES:")
        print(f"  • Total CountingDetail en base: {total_cd}")
        print(f"  • Créés dans ce test: {created}")
    except Exception as e:
        print(f"  ⚠️ Erreur vérification: {e}")
    
    print(f"\n🏁 TEST TERMINÉ!")
    print(f"📅 Fin: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
