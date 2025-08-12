#!/usr/bin/env python
"""
Script pour ajouter des produits de test avec numéros de série
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.masterdata.models import Account, Family, Product, NSerie
from apps.users.models import UserApp

def add_test_products():
    """Ajoute des produits de test avec numéros de série"""
    print("🔧 Ajout de produits de test...")
    
    # Trouver un compte existant
    accounts = Account.objects.filter(account_statuts='ACTIVE')
    if accounts.count() == 0:
        print("❌ Aucun compte actif trouvé")
        return False
    
    account = accounts.first()
    print(f"✅ Compte trouvé: {account.account_name}")
    
    # Créer ou récupérer une famille
    family, created = Family.objects.get_or_create(
        family_name='Test Family',
        compte=account,
        defaults={
            'family_status': 'ACTIVE',
            'family_description': 'Famille de test'
        }
    )
    
    if created:
        print(f"✅ Famille créée: {family.family_name}")
    else:
        print(f"✅ Famille existante: {family.family_name}")
    
    # Créer un produit avec numéros de série
    product_with_nserie, created = Product.objects.get_or_create(
        Internal_Product_Code='TEST-PROD-NS-001',
        defaults={
            'Short_Description': 'Produit avec numéros de série',
            'Barcode': '1234567890125',
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
        print(f"✅ Produit avec n_serie créé: {product_with_nserie.Short_Description}")
    else:
        print(f"✅ Produit avec n_serie existant: {product_with_nserie.Short_Description}")
    
    # Créer des numéros de série pour ce produit
    for i in range(1, 4):
        nserie, created = NSerie.objects.get_or_create(
            n_serie=f'NS-TEST-{i:03d}',
            product=product_with_nserie,
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
    
    # Créer un produit sans numéros de série
    product_without_nserie, created = Product.objects.get_or_create(
        Internal_Product_Code='TEST-PROD-NO-NS-001',
        defaults={
            'Short_Description': 'Produit sans numéros de série',
            'Barcode': '1234567890126',
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
        print(f"✅ Produit sans n_serie créé: {product_without_nserie.Short_Description}")
    else:
        print(f"✅ Produit sans n_serie existant: {product_without_nserie.Short_Description}")
    
    print("\n🎉 Produits de test ajoutés avec succès!")
    return True

def main():
    """Fonction principale"""
    print("🚀 Ajout de produits de test avec numéros de série")
    
    try:
        success = add_test_products()
        
        if success:
            print("\n✅ Ajout réussi!")
            print("\n📋 Produits créés:")
            print("   - TEST-PROD-NS-001: Produit avec numéros de série")
            print("   - TEST-PROD-NO-NS-001: Produit sans numéros de série")
            print("   - 3 numéros de série: NS-TEST-001, NS-TEST-002, NS-TEST-003")
        else:
            print("\n❌ Ajout échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
