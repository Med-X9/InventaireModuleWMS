# Test direct pour le shell Django - Copiez-collez ce code
print("TEST COMPLET 1000 LIGNES - VERSION SHELL")
print("=" * 60)

from django.contrib.auth import get_user_model
from apps.inventory.models import *
from apps.masterdata.models import *
from apps.mobile.services.counting_detail_service import CountingDetailService
import time, random
from datetime import datetime, timedelta

User = get_user_model()

# Préparation rapide
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.create_superuser('testapi', 'test@api.com', 'test123')

# Compte avec le bon champ
account, _ = Account.objects.get_or_create(
    account_name="TestAPI1000",
    defaults={'account_statuts': 'ACTIVE', 'description': 'Test'}
)

warehouse, _ = Warehouse.objects.get_or_create(
    name="TestWarehouse1000", 
    defaults={'account': account}
)

# Emplacements
locations = []
for i in range(10):
    loc, _ = Location.objects.get_or_create(
        name=f"LOC1000-{i+1:02d}",
        defaults={'warehouse': warehouse}
    )
    locations.append(loc)

# Produits avec propriétés variées
products = []
for i in range(8):
    prod, _ = Product.objects.get_or_create(
        Internal_Product_Code=f"PROD1000-{i+1:02d}",
        defaults={
            'Short_Description': f'Produit 1000 {i+1}',
            'Stock_Unit': 'Unité',
            'Product_Status': 'ACTIVE',
            'n_lot': i % 2 == 0,
            'n_serie': i % 3 == 0,
            'dlc': i % 2 == 1
        }
    )
    products.append(prod)

# Inventaire et comptages
inventory, _ = Inventory.objects.get_or_create(
    name="TestInv1000",
    defaults={'account': account, 'warehouse': warehouse}
)

countings = []
modes = [
    {'mode': 'en vrac', 'n_lot': True, 'n_serie': False, 'dlc': True},
    {'mode': 'par article', 'n_lot': True, 'n_serie': True, 'dlc': True},
    {'mode': 'image de stock', 'n_lot': False, 'n_serie': True, 'dlc': False}
]

for i, config in enumerate(modes):
    counting, _ = Counting.objects.get_or_create(
        inventory=inventory,
        order=i+1,
        defaults={
            'count_mode': config['mode'],
            'entry_quantity': True,
            'n_lot': config['n_lot'],
            'n_serie': config['n_serie'],
            'dlc': config['dlc'],
            'show_product': True
        }
    )
    countings.append(counting)

# Job et assignment
job, _ = Job.objects.get_or_create(inventory=inventory)
assignment, _ = Assigment.objects.get_or_create(
    job=job, user=user, defaults={'status': 'EN COURS'}
)

print(f"✅ Données prêtes:")
print(f"   • {len(locations)} emplacements")
print(f"   • {len(products)} produits")
print(f"   • {len(countings)} modes de comptage")

# Service et variables
service = CountingDetailService()
created = 0
errors = 0
start_time = time.time()

print(f"\n🧪 CRÉATION DE 1000 COUNTINGDETAIL...")
print("-" * 60)

# Cas de test
test_cases = [
    # 250 en vrac
    {'name': 'En vrac', 'count': 250, 'counting': countings[0], 'need_product': False},
    # 400 par article  
    {'name': 'Par article', 'count': 400, 'counting': countings[1], 'need_product': True},
    # 200 image stock
    {'name': 'Image stock', 'count': 200, 'counting': countings[2], 'need_product': False},
    # 150 mixtes
    {'name': 'Mixte', 'count': 150, 'counting': None, 'need_product': False}
]

for case in test_cases:
    print(f"\n📋 CAS: {case['name']} ({case['count']} lignes)")
    case_created = 0
    case_start = time.time()
    
    for i in range(case['count']):
        try:
            # Choisir le comptage
            if case['counting']:
                counting = case['counting']
            else:
                counting = random.choice(countings)
            
            data = {
                'counting_id': counting.id,
                'location_id': random.choice(locations).id,
                'quantity_inventoried': random.randint(1, 50),
                'assignment_id': assignment.id
            }
            
            # Ajouter produit selon le cas
            if case['need_product'] or (counting.count_mode == "par article"):
                data['product_id'] = random.choice(products).id
            elif random.choice([True, False]):
                data['product_id'] = random.choice(products).id
            
            # Ajouter DLC si possible
            if counting.dlc and random.choice([True, False]):
                future_date = datetime.now() + timedelta(days=random.randint(30, 365))
                data['dlc'] = future_date.strftime('%Y-%m-%d')
            
            # Ajouter lot si possible
            if counting.n_lot and random.choice([True, False]):
                data['n_lot'] = f"LOT-{case['name'][:3].upper()}-{created+i+1:05d}-{random.randint(1000, 9999)}"
            
            # Ajouter numéros de série si possible
            if counting.n_serie and random.choice([True, False]) and data.get('product_id'):
                num_series = random.randint(1, 3)
                data['numeros_serie'] = []
                for j in range(num_series):
                    data['numeros_serie'].append({
                        'n_serie': f"NS-{case['name'][:3].upper()}-{created+i+1:05d}-{j+1:02d}-{random.randint(1000, 9999)}"
                    })
            
            # Créer
            service.create_counting_detail(data)
            case_created += 1
            created += 1
            
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"   ❌ Erreur {created+i+1}: {str(e)[:50]}...")
        
        # Progrès du cas
        if (i + 1) % max(1, case['count'] // 4) == 0:
            elapsed = time.time() - case_start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"   📊 {i + 1:3d}/{case['count']} | ✅ {case_created:3d} | {rate:4.1f}/s")
    
    case_time = time.time() - case_start
    print(f"   ✅ {case['name']}: {case_created}/{case['count']} succès en {case_time:.1f}s")

total_time = time.time() - start_time

# Rapport final
print(f"\nRAPPORT FINAL")
print("=" * 40)
print(f"RESULTATS:")
print(f"   • Succes: {created}/1000 ({created/10:.1f}%)")
print(f"   • Erreurs: {errors}/1000 ({errors/10:.1f}%)")
print(f"   • Temps: {total_time:.1f}s ({total_time/60:.1f}min)")
print(f"   • Debit: {1000/total_time:.1f} lignes/sec")

# Vérification
try:
    total_cd = CountingDetail.objects.count()
    test_cd = CountingDetail.objects.filter(
        counting__inventory__name="TestInv1000"
    ).count()
    ns_count = NSerieInventory.objects.filter(
        counting_detail__counting__inventory__name="TestInv1000"
    ).count()
    
    print(f"\nVERIFICATION:")
    print(f"   • Total CountingDetail en base: {total_cd}")
    print(f"   • CountingDetail de ce test: {test_cd}")
    print(f"   • Numéros de série créés: {ns_count}")
    print(f"   • Créés avec succès: {created}")
except Exception as e:
    print(f"   Erreur verification: {e}")

# Évaluation
if created >= 950:
    print("\nEXCELLENT! Votre API est tres performante!")
elif created >= 850:
    print("\nTRES BIEN! Votre API fonctionne tres bien!")
elif created >= 700:
    print("\nCORRECT! Votre API fonctionne correctement!")
else:
    print("\nQuelques ameliorations necessaires.")

print(f"\n{created} CountingDetail crees avec tous les cas de test!")
print("TEST COMPLET TERMINE!")
