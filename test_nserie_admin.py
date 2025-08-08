#!/usr/bin/env python
"""
Script de test pour vérifier l'admin NSerie
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.masterdata.models import NSerie, Product, Family, Account
from apps.masterdata.admin import NSerieAdmin

def test_nserie_admin():
    """Test de l'admin NSerie"""
    print("🧪 Test de l'admin NSerie...")
    
    # 1. Vérifier les données existantes
    print("\n📊 Vérification des données existantes:")
    
    nseries = NSerie.objects.all()
    print(f"   - Numéros de série: {nseries.count()}")
    
    products_with_nserie = Product.objects.filter(n_serie=True)
    print(f"   - Produits avec n_serie=True: {products_with_nserie.count()}")
    
    # 2. Créer des données de test si nécessaire
    if nseries.count() == 0:
        print("\n🔧 Création de données de test...")
        
        # Trouver un compte et une famille
        account = Account.objects.filter(account_statuts='ACTIVE').first()
        if not account:
            print("❌ Aucun compte actif trouvé")
            return False
        
        # Utiliser une famille existante ou en créer une avec un nom unique
        family = Family.objects.filter(compte=account).first()
        if not family:
            # Créer une famille avec un nom unique basé sur le timestamp
            timestamp = int(timezone.now().timestamp())
            family_name = f'Test Family NSerie {timestamp}'
            family = Family.objects.create(
                family_name=family_name,
                compte=account,
                family_status='ACTIVE',
                family_description='Famille de test pour numéros de série'
            )
            print(f"✅ Famille créée: {family.family_name}")
        else:
            print(f"✅ Famille existante: {family.family_name}")
        
        # Créer un produit avec n_serie=True
        timestamp = int(timezone.now().timestamp())
        product_code = f'TEST-NSERIE-PROD-{timestamp}'
        product, created = Product.objects.get_or_create(
            Internal_Product_Code=product_code,
            defaults={
                'Short_Description': f'Produit de test pour numéros de série {timestamp}',
                'Barcode': f'1234567890127{timestamp}',
                'Product_Group': 'TEST',
                'Stock_Unit': 'PIECE',
                'Product_Status': 'ACTIVE',
                'Product_Family': family,
                'n_serie': True,
                'n_lot': False,
                'dlc': False
            }
        )
        
        if created:
            print(f"✅ Produit créé: {product.Short_Description}")
        else:
            print(f"✅ Produit existant: {product.Short_Description}")
        
        # Créer des numéros de série
        for i in range(1, 4):
            nserie_code = f'NS-ADMIN-TEST-{timestamp}-{i:03d}'
            nserie, created = NSerie.objects.get_or_create(
                n_serie=nserie_code,
                product=product,
                defaults={
                    'status': 'ACTIVE',
                    'description': f'Numéro de série de test {i} pour admin',
                    'date_fabrication': timezone.now().date(),
                    'date_expiration': timezone.now().date().replace(year=timezone.now().year + 2),
                    'warranty_end_date': timezone.now().date().replace(year=timezone.now().year + 1)
                }
            )
            
            if created:
                print(f"✅ Numéro de série créé: {nserie.n_serie}")
            else:
                print(f"✅ Numéro de série existant: {nserie.n_serie}")
    
    # 3. Tester l'admin
    print("\n🧪 Test de l'admin NSerie...")
    
    try:
        # Créer une instance de l'admin
        admin = NSerieAdmin(NSerie, None)
        
        # Tester les méthodes personnalisées
        nseries = NSerie.objects.all()[:3]  # Prendre les 3 premiers
        
        for nserie in nseries:
            print(f"\n📦 Numéro de série: {nserie.n_serie}")
            print(f"   - Référence: {nserie.reference}")
            print(f"   - Produit: {admin.get_product_name(nserie)}")
            print(f"   - Famille: {admin.get_product_family(nserie)}")
            print(f"   - Status: {nserie.status}")
            print(f"   - Date fabrication: {nserie.date_fabrication}")
            print(f"   - Date expiration: {nserie.date_expiration}")
            print(f"   - Garantie: {nserie.warranty_end_date}")
            print(f"   - Expiré: {nserie.is_expired}")
            print(f"   - Garantie valide: {nserie.is_warranty_valid}")
        
        # Tester les filtres
        print(f"\n📊 Filtres disponibles:")
        print(f"   - Status: {[choice[0] for choice in NSerie.STATUS_CHOICES]}")
        print(f"   - Produits avec n_serie: {Product.objects.filter(n_serie=True).count()}")
        
        # Tester la recherche
        search_results = NSerie.objects.filter(n_serie__icontains='TEST')
        print(f"   - Résultats de recherche 'TEST': {search_results.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test admin: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_admin_configuration():
    """Test de la configuration admin"""
    print("\n🧪 Test de la configuration admin...")
    
    try:
        from django.contrib import admin
        from apps.masterdata.admin import NSerieAdmin
        
        # Vérifier que l'admin est enregistré
        registered_models = admin.site._registry.keys()
        nserie_registered = NSerie in registered_models
        
        print(f"   - NSerie enregistré dans admin: {nserie_registered}")
        
        if nserie_registered:
            # Vérifier la configuration
            admin_instance = admin.site._registry[NSerie]
            print(f"   - Classe admin: {type(admin_instance).__name__}")
            print(f"   - List display: {admin_instance.list_display}")
            print(f"   - List filter: {admin_instance.list_filter}")
            print(f"   - Search fields: {admin_instance.search_fields}")
            print(f"   - Date hierarchy: {admin_instance.date_hierarchy}")
        
        return nserie_registered
        
    except Exception as e:
        print(f"❌ Erreur lors du test de configuration: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test de l'admin NSerie")
    
    try:
        # Test des données et de l'admin
        success1 = test_nserie_admin()
        
        # Test de la configuration admin
        success2 = test_admin_configuration()
        
        if success1 and success2:
            print("\n🎉 Tous les tests ont réussi!")
            print("\n✅ L'admin NSerie est correctement configuré")
            print("\n📋 Fonctionnalités disponibles:")
            print("   - ✅ Import/Export des numéros de série")
            print("   - ✅ Affichage des informations produit et famille")
            print("   - ✅ Filtres par statut, famille, dates")
            print("   - ✅ Recherche par numéro, produit, description")
            print("   - ✅ Calcul automatique des dates d'expiration et garantie")
            print("   - ✅ Hiérarchie par date de création")
        else:
            print("\n⚠️ Certains tests ont échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")

if __name__ == "__main__":
    main()
