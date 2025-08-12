#!/usr/bin/env python
"""
Script pour configurer les données de test pour l'API mobile avec numéros de série
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.masterdata.models import Account, Family, Product, NSerie, Warehouse, ZoneType, Zone, SousZone, LocationType, Location
from apps.users.models import UserApp

def setup_test_data():
    """Configure les données de test nécessaires"""
    print("🔧 Configuration des données de test...")
    
    # 1. Créer ou récupérer un compte
    account, created = Account.objects.get_or_create(
        account_name='Mobile Test Account',
        defaults={
            'account_statuts': 'ACTIVE',
            'description': 'Compte de test pour l\'API mobile'
        }
    )
    
    if created:
        print(f"✅ Compte créé: {account.account_name}")
    else:
        print(f"✅ Compte existant: {account.account_name}")
    
    # 2. Créer une famille de produits
    family, created = Family.objects.get_or_create(
        family_name='Mobile Test Family',
        compte=account,
        defaults={
            'family_status': 'ACTIVE',
            'family_description': 'Famille de test pour l\'API mobile'
        }
    )
    
    if created:
        print(f"✅ Famille créée: {family.family_name}")
    else:
        print(f"✅ Famille existante: {family.family_name}")
    
    # 3. Créer un entrepôt
    warehouse, created = Warehouse.objects.get_or_create(
        warehouse_name='Mobile Test Warehouse',
        defaults={
            'warehouse_type': 'CENTRAL',
            'status': 'ACTIVE',
            'description': 'Entrepôt de test pour l\'API mobile'
        }
    )
    
    if created:
        print(f"✅ Entrepôt créé: {warehouse.warehouse_name}")
    else:
        print(f"✅ Entrepôt existant: {warehouse.warehouse_name}")
    
    # 4. Créer un type de zone
    zone_type, created = ZoneType.objects.get_or_create(
        type_name='Mobile Test Zone Type',
        defaults={
            'status': 'ACTIVE',
            'description': 'Type de zone de test'
        }
    )
    
    if created:
        print(f"✅ Type de zone créé: {zone_type.type_name}")
    else:
        print(f"✅ Type de zone existant: {zone_type.type_name}")
    
    # 5. Créer une zone
    zone, created = Zone.objects.get_or_create(
        zone_name='Mobile Test Zone',
        warehouse=warehouse,
        defaults={
            'zone_type': zone_type,
            'zone_status': 'ACTIVE',
            'description': 'Zone de test'
        }
    )
    
    if created:
        print(f"✅ Zone créée: {zone.zone_name}")
    else:
        print(f"✅ Zone existante: {zone.zone_name}")
    
    # 6. Créer une sous-zone
    sous_zone, created = SousZone.objects.get_or_create(
        sous_zone_name='Mobile Test Sous-Zone',
        zone=zone,
        defaults={
            'sous_zone_status': 'ACTIVE',
            'description': 'Sous-zone de test'
        }
    )
    
    if created:
        print(f"✅ Sous-zone créée: {sous_zone.sous_zone_name}")
    else:
        print(f"✅ Sous-zone existante: {sous_zone.sous_zone_name}")
    
    # 7. Créer un type d'emplacement
    location_type, created = LocationType.objects.get_or_create(
        name='Mobile Test Location Type',
        defaults={
            'is_active': True,
            'description': 'Type d\'emplacement de test'
        }
    )
    
    if created:
        print(f"✅ Type d'emplacement créé: {location_type.name}")
    else:
        print(f"✅ Type d'emplacement existant: {location_type.name}")
    
    # 8. Créer un emplacement
    location, created = Location.objects.get_or_create(
        location_reference='MOBILE-TEST-LOC-001',
        defaults={
            'sous_zone': sous_zone,
            'location_type': location_type,
            'is_active': True,
            'description': 'Emplacement de test'
        }
    )
    
    if created:
        print(f"✅ Emplacement créé: {location.location_reference}")
    else:
        print(f"✅ Emplacement existant: {location.location_reference}")
    
    # 9. Créer un produit avec numéros de série
    product, created = Product.objects.get_or_create(
        Internal_Product_Code='MOBILE-TEST-PROD-001',
        defaults={
            'Short_Description': 'Produit de test avec numéros de série',
            'Barcode': '1234567890123',
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
    
    # 10. Créer des numéros de série pour le produit
    for i in range(1, 4):
        nserie, created = NSerie.objects.get_or_create(
            n_serie=f'NS-MOBILE-TEST-{i:03d}',
            product=product,
            defaults={
                'status': 'ACTIVE',
                'description': f'Numéro de série de test {i}',
                'date_fabrication': timezone.now().date(),
                'date_expiration': timezone.now().date().replace(year=timezone.now().year + 2),
                'warranty_end_date': timezone.now().date().replace(year=timezone.now().year + 1)
            }
        )
        
        if created:
            print(f"✅ Numéro de série créé: {nserie.n_serie}")
        else:
            print(f"✅ Numéro de série existant: {nserie.n_serie}")
    
    # 11. Créer un produit sans numéros de série pour comparaison
    product_no_nserie, created = Product.objects.get_or_create(
        Internal_Product_Code='MOBILE-TEST-PROD-002',
        defaults={
            'Short_Description': 'Produit de test sans numéros de série',
            'Barcode': '1234567890124',
            'Product_Group': 'TEST',
            'Stock_Unit': 'PIECE',
            'Product_Status': 'ACTIVE',
            'Product_Family': family,
            'n_serie': False,
            'n_lot': True,
            'dlc': False
        }
    )
    
    if created:
        print(f"✅ Produit sans n_serie créé: {product_no_nserie.Short_Description}")
    else:
        print(f"✅ Produit sans n_serie existant: {product_no_nserie.Short_Description}")
    
    # 12. Associer un compte à l'utilisateur admin
    try:
        admin_user = UserApp.objects.get(username='admin')
        admin_user.compte = account
        admin_user.save()
        print(f"✅ Compte associé à l'utilisateur admin")
    except UserApp.DoesNotExist:
        print("⚠️ Utilisateur admin non trouvé")
    
    print("\n🎉 Configuration des données de test terminée!")
    return True

def main():
    """Fonction principale"""
    print("🚀 Configuration des données de test pour l'API mobile")
    
    try:
        success = setup_test_data()
        
        if success:
            print("\n✅ Configuration réussie!")
            print("\n📋 Données créées:")
            print("   - Compte: Mobile Test Account")
            print("   - Famille: Mobile Test Family")
            print("   - Entrepôt: Mobile Test Warehouse")
            print("   - Zone: Mobile Test Zone")
            print("   - Sous-zone: Mobile Test Sous-Zone")
            print("   - Emplacement: MOBILE-TEST-LOC-001")
            print("   - Produit avec n_serie: MOBILE-TEST-PROD-001")
            print("   - Produit sans n_serie: MOBILE-TEST-PROD-002")
            print("   - 3 numéros de série: NS-MOBILE-TEST-001, NS-MOBILE-TEST-002, NS-MOBILE-TEST-003")
        else:
            print("\n❌ Configuration échouée")
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
