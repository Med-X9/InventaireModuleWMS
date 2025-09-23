#!/usr/bin/env python
"""
Script simplifié pour configurer Postman avec les données existantes
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
    print("🔧 CONFIGURATION POSTMAN AVEC DONNÉES EXISTANTES")
    print("=" * 60)
    
    try:
        # Récupérer les données existantes
        print("📊 Analyse des données existantes...")
        
        # Comptes
        accounts = Account.objects.all()[:5]
        print(f"✅ Comptes trouvés: {len(accounts)}")
        
        # Entrepôts
        warehouses = Warehouse.objects.all()[:5]
        print(f"✅ Entrepôts trouvés: {len(warehouses)}")
        
        # Emplacements
        locations = Location.objects.all()[:10]
        print(f"✅ Emplacements trouvés: {len(locations)}")
        
        # Produits
        products = Product.objects.all()[:10]
        print(f"✅ Produits trouvés: {len(products)}")
        
        # Inventaires
        inventories = Inventory.objects.all()[:5]
        print(f"✅ Inventaires trouvés: {len(inventories)}")
        
        # Comptages
        countings = Counting.objects.all()[:10]
        print(f"✅ Comptages trouvés: {len(countings)}")
        
        # Assignments
        assignments = Assigment.objects.all()[:5]
        print(f"✅ Assignments trouvés: {len(assignments)}")
        
        # Utilisateurs
        users = User.objects.filter(is_superuser=True)
        print(f"✅ Utilisateurs admin trouvés: {len(users)}")
        
        print(f"\n📋 CONFIGURATION POSTMAN")
        print("=" * 40)
        
        if not (locations and products and countings and assignments and users):
            print("❌ DONNÉES MANQUANTES!")
            print("Créons le minimum nécessaire...")
            create_minimal_data()
            return
        
        # Trouver des comptages par mode
        counting_vrac = countings.filter(count_mode='en vrac').first()
        counting_article = countings.filter(count_mode='par article').first()
        counting_stock = countings.filter(count_mode='image de stock').first()
        
        # Si pas de comptages par mode, prendre les premiers
        if not counting_vrac:
            counting_vrac = countings[0] if countings else None
        if not counting_article:
            counting_article = countings[1] if len(countings) > 1 else countings[0] if countings else None
        if not counting_stock:
            counting_stock = countings[2] if len(countings) > 2 else countings[0] if countings else None
        
        print("🔧 Variables pour Postman :")
        print(f"   base_url: http://localhost:8000")
        print(f"   counting_id_vrac: {counting_vrac.id if counting_vrac else 'N/A'}")
        print(f"   counting_id_article: {counting_article.id if counting_article else 'N/A'}")
        print(f"   counting_id_stock: {counting_stock.id if counting_stock else 'N/A'}")
        print(f"   location_id: {locations[0].id if locations else 'N/A'}")
        print(f"   product_id: {products[0].id if products else 'N/A'}")
        print(f"   assignment_id: {assignments[0].id if assignments else 'N/A'}")
        print()
        print("👤 Authentification :")
        if users:
            print(f"   username: {users[0].username}")
            print("   password: [votre mot de passe]")
        else:
            print("   username: admin")
            print("   password: admin")
        
        print(f"\n📊 DÉTAILS DES DONNÉES :")
        
        if locations:
            print(f"📍 Emplacements disponibles :")
            for i, loc in enumerate(locations[:5], 1):
                print(f"   {i}. {loc.name} (ID: {loc.id})")
        
        if products:
            print(f"\n📦 Produits disponibles :")
            for i, prod in enumerate(products[:5], 1):
                print(f"   {i}. {prod.Internal_Product_Code} - {prod.Short_Description} (ID: {prod.id})")
        
        if countings:
            print(f"\n📋 Comptages disponibles :")
            for i, counting in enumerate(countings[:5], 1):
                print(f"   {i}. {counting.count_mode} (ID: {counting.id})")
                print(f"      - Inventaire: {counting.inventory.name if counting.inventory else 'N/A'}")
        
        if assignments:
            print(f"\n👥 Assignments disponibles :")
            for i, assignment in enumerate(assignments[:3], 1):
                print(f"   {i}. Job {assignment.job.id} - User {assignment.user.username} (ID: {assignment.id})")
        
        print(f"\n✅ CONFIGURATION POSTMAN PRÊTE !")
        print("=" * 50)
        print("📋 ÉTAPES SUIVANTES :")
        print("1. Importez le fichier Postman_CountingDetail_Collection.json dans Postman")
        print("2. Éditez la collection → Variables")
        print("3. Copiez les valeurs ci-dessus dans les variables")
        print("4. Ajustez le nom d'utilisateur/mot de passe")
        print("5. Lancez les tests !")
        print()
        print("🚀 POUR TESTER 1000 LIGNES :")
        print("   - Sélectionnez les 4 tests de création")
        print("   - Configurez 250 iterations")
        print("   - Delay: 50ms")
        print("   - Run collection")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n💡 Essayons de créer le minimum nécessaire...")
        create_minimal_data()

def create_minimal_data():
    """Crée le minimum de données nécessaires pour Postman"""
    print("\n🔧 CRÉATION DU MINIMUM NÉCESSAIRE...")
    
    try:
        # Utilisateur admin
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_superuser('admin', 'admin@test.com', 'admin')
            print("✅ Utilisateur admin créé")
        
        # Utiliser un compte existant ou en créer un simple
        account = Account.objects.first()
        if not account:
            # Créer manuellement sans get_or_create
            account = Account(
                account_name="Test Postman",
                account_statuts='ACTIVE',
                description='Compte pour tests Postman'
            )
            account.save()
            print("✅ Compte créé")
        
        # Entrepôt
        warehouse = Warehouse.objects.first()
        if not warehouse:
            warehouse = Warehouse.objects.create(
                name="Test Warehouse",
                account=account
            )
            print("✅ Entrepôt créé")
        
        # Emplacement
        location = Location.objects.first()
        if not location:
            location = Location.objects.create(
                name="TEST-LOC-01",
                warehouse=warehouse
            )
            print("✅ Emplacement créé")
        
        # Produit
        product = Product.objects.first()
        if not product:
            product = Product.objects.create(
                Internal_Product_Code="TEST-PROD-01",
                Short_Description='Produit Test Postman',
                Stock_Unit='Unité',
                Product_Status='ACTIVE'
            )
            print("✅ Produit créé")
        
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
                count_mode='en vrac',
                entry_quantity=True
            )
            print("✅ Comptage créé")
        
        # Job et Assignment
        job = Job.objects.first()
        if not job:
            job = Job.objects.create(inventory=inventory)
            print("✅ Job créé")
        
        assignment = Assigment.objects.first()
        if not assignment:
            assignment = Assigment.objects.create(
                job=job,
                user=user,
                status='EN COURS'
            )
            print("✅ Assignment créé")
        
        print(f"\n✅ DONNÉES MINIMALES CRÉÉES !")
        print(f"📋 Configuration Postman :")
        print(f"   counting_id_vrac: {counting.id}")
        print(f"   counting_id_article: {counting.id}")
        print(f"   counting_id_stock: {counting.id}")
        print(f"   location_id: {location.id}")
        print(f"   product_id: {product.id}")
        print(f"   assignment_id: {assignment.id}")
        print(f"   username: admin")
        print(f"   password: admin")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        print("💡 Utilisez les IDs existants dans votre base de données")

if __name__ == "__main__":
    main()
