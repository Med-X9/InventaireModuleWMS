#!/usr/bin/env python
"""
Script pour générer des données de test pour Postman
Ce script crée les données nécessaires et affiche les IDs pour Postman
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

User = get_user_model()

def main():
    print("🔧 GÉNÉRATION DES DONNÉES POUR POSTMAN")
    print("=" * 60)
    
    # Créer ou récupérer un utilisateur admin
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('admin', 'admin@postman.com', 'admin')
        print("✅ Utilisateur admin créé (admin/admin)")
    else:
        print(f"✅ Utilisateur admin existant: {user.username}")
    
    # Compte
    account, created = Account.objects.get_or_create(
        account_name="Postman Test Account",
        defaults={
            'account_statuts': 'ACTIVE',
            'description': 'Compte pour tests Postman'
        }
    )
    print(f"✅ Compte: {account.account_name} (ID: {account.id})")
    
    # Entrepôt
    warehouse, created = Warehouse.objects.get_or_create(
        name="Postman Warehouse",
        defaults={'account': account}
    )
    print(f"✅ Entrepôt: {warehouse.name} (ID: {warehouse.id})")
    
    # Emplacements
    locations = []
    for i in range(5):
        location, created = Location.objects.get_or_create(
            name=f"POSTMAN-LOC-{i+1:02d}",
            defaults={'warehouse': warehouse}
        )
        locations.append(location)
    print(f"✅ Emplacements créés: {len(locations)}")
    
    # Produits
    products = []
    for i in range(5):
        product, created = Product.objects.get_or_create(
            Internal_Product_Code=f"POSTMAN-PROD-{i+1:02d}",
            defaults={
                'Short_Description': f'Produit Postman {i+1}',
                'Stock_Unit': 'Unité',
                'Product_Status': 'ACTIVE',
                'n_lot': i % 2 == 0,
                'n_serie': i % 3 == 0,
                'dlc': i % 2 == 1
            }
        )
        products.append(product)
    print(f"✅ Produits créés: {len(products)}")
    
    # Inventaire
    inventory, created = Inventory.objects.get_or_create(
        name="Postman Inventory",
        defaults={
            'account': account,
            'warehouse': warehouse
        }
    )
    print(f"✅ Inventaire: {inventory.name} (ID: {inventory.id})")
    
    # Comptages avec différents modes
    countings = []
    modes_config = [
        {'mode': 'en vrac', 'n_lot': True, 'n_serie': False, 'dlc': True},
        {'mode': 'par article', 'n_lot': True, 'n_serie': True, 'dlc': True},
        {'mode': 'image de stock', 'n_lot': False, 'n_serie': True, 'dlc': False}
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
                'show_product': True,
                'quantity_show': True
            }
        )
        countings.append(counting)
    print(f"✅ Comptages créés: {len(countings)}")
    
    # Job et Assignment
    job, created = Job.objects.get_or_create(
        inventory=inventory,
        defaults={}
    )
    
    assignment, created = Assigment.objects.get_or_create(
        job=job,
        user=user,
        defaults={'status': 'EN COURS'}
    )
    print(f"✅ Job et Assignment créés")
    
    # Affichage des IDs pour Postman
    print(f"\n📋 CONFIGURATION POSTMAN")
    print("=" * 40)
    print("Copiez ces valeurs dans vos variables Postman :")
    print()
    print("🔧 Variables de Collection :")
    print(f"   base_url: http://localhost:8000")
    print(f"   counting_id_vrac: {countings[0].id}")
    print(f"   counting_id_article: {countings[1].id}")
    print(f"   counting_id_stock: {countings[2].id}")
    print(f"   location_id: {locations[0].id}")
    print(f"   product_id: {products[0].id}")
    print(f"   assignment_id: {assignment.id}")
    print()
    print("👤 Authentification :")
    print(f"   username: admin")
    print(f"   password: admin")
    print()
    
    # Détails des données créées
    print("📊 DÉTAILS DES DONNÉES CRÉÉES :")
    print(f"   • Compte: {account.account_name}")
    print(f"   • Entrepôt: {warehouse.name}")
    print(f"   • Emplacements: {', '.join([loc.name for loc in locations])}")
    print(f"   • Produits: {', '.join([prod.Internal_Product_Code for prod in products])}")
    print()
    print("📋 Comptages créés :")
    for i, counting in enumerate(countings, 1):
        print(f"   {i}. {counting.count_mode} (ID: {counting.id})")
        print(f"      - N°Lot: {'Oui' if counting.n_lot else 'Non'}")
        print(f"      - N°Série: {'Oui' if counting.n_serie else 'Non'}")
        print(f"      - DLC: {'Oui' if counting.dlc else 'Non'}")
    
    print(f"\n✅ DONNÉES PRÊTES POUR POSTMAN!")
    print("=" * 40)
    print("1. Importez la collection Postman_CountingDetail_Collection.json")
    print("2. Configurez les variables avec les IDs ci-dessus")
    print("3. Lancez les tests !")
    print()
    print("💡 Pour tester 1000 lignes :")
    print("   - Sélectionnez les tests de création")
    print("   - Configurez 250 iterations")
    print("   - Lancez la collection")

if __name__ == "__main__":
    main()
