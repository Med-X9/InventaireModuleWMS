#!/usr/bin/env python
"""
Script de test pour vérifier que l'API mobile retourne les numéros de série avec les produits
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.mobile.repositories.user_repository import UserRepository
from apps.masterdata.models import Product, NSerie, Family, Account
from apps.users.models import UserApp

def test_products_with_nserie():
    """Test de récupération des produits avec numéros de série"""
    print("🧪 Test de récupération des produits avec numéros de série...")
    
    repository = UserRepository()
    
    # Trouver un utilisateur existant
    users = UserApp.objects.all()
    if users.count() == 0:
        print("❌ Aucun utilisateur trouvé dans la base de données")
        return False
    
    user = users.first()
    print(f"✅ Utilisateur trouvé: {user.username} (ID: {user.id})")
    
    try:
        # Récupérer les produits via le repository
        products = repository.get_products_by_user_account(user.id)
        print(f"✅ Nombre de produits trouvés: {len(products)}")
        
        if len(products) == 0:
            print("⚠️ Aucun produit trouvé pour cet utilisateur")
            return True
        
        # Tester le formatage des données
        products_with_nserie = 0
        total_nserie_count = 0
        
        for product in products:
            try:
                product_data = repository.format_product_data(product)
                
                # Vérifier si le produit a des numéros de série
                if product.n_serie:
                    print(f"\n📦 Produit avec numéros de série: {product.Short_Description}")
                    print(f"   - ID: {product.id}")
                    print(f"   - Support n_serie: {product.n_serie}")
                    
                    if 'numeros_serie' in product_data:
                        numeros_serie = product_data['numeros_serie']
                        print(f"   - Nombre de numéros de série: {len(numeros_serie)}")
                        
                        if len(numeros_serie) > 0:
                            products_with_nserie += 1
                            total_nserie_count += len(numeros_serie)
                            
                            # Afficher les premiers numéros de série
                            for i, nserie in enumerate(numeros_serie[:3]):  # Limiter à 3 pour l'affichage
                                print(f"     {i+1}. {nserie['n_serie']} (Status: {nserie['status']})")
                            
                            if len(numeros_serie) > 3:
                                print(f"     ... et {len(numeros_serie) - 3} autres")
                        else:
                            print(f"   - ⚠️ Aucun numéro de série trouvé malgré n_serie=True")
                    else:
                        print(f"   - ❌ Champ 'numeros_serie' manquant dans la réponse")
                else:
                    print(f"\n📦 Produit sans numéros de série: {product.Short_Description}")
                    print(f"   - Support n_serie: {product.n_serie}")
                    
                    # Vérifier que le champ est présent mais vide
                    if 'numeros_serie' in product_data:
                        numeros_serie = product_data['numeros_serie']
                        if len(numeros_serie) == 0:
                            print(f"   - ✅ Champ 'numeros_serie' présent et vide (correct)")
                        else:
                            print(f"   - ❌ Champ 'numeros_serie' non vide alors que n_serie=False")
                    else:
                        print(f"   - ❌ Champ 'numeros_serie' manquant dans la réponse")
                
            except Exception as e:
                print(f"❌ Erreur lors du formatage du produit {product.id}: {str(e)}")
                continue
        
        print(f"\n📊 Résumé:")
        print(f"   - Produits avec numéros de série: {products_with_nserie}")
        print(f"   - Total de numéros de série: {total_nserie_count}")
        print(f"   - Produits testés: {len(products)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_create_sample_data():
    """Crée des données de test si nécessaire"""
    print("\n🔧 Création de données de test...")
    
    # Vérifier s'il y a des comptes
    accounts = Account.objects.all()
    if accounts.count() == 0:
        print("❌ Aucun compte trouvé. Impossible de créer des données de test.")
        return False
    
    account = accounts.first()
    print(f"✅ Compte trouvé: {account.account_name}")
    
    # Vérifier s'il y a des familles
    families = Family.objects.filter(compte=account)
    if families.count() == 0:
        print("❌ Aucune famille trouvée pour ce compte.")
        return False
    
    family = families.first()
    print(f"✅ Famille trouvée: {family.family_name}")
    
    # Créer un produit de test avec numéros de série
    try:
        product, created = Product.objects.get_or_create(
            Internal_Product_Code='TEST-PROD-001',
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
            print(f"✅ Produit de test créé: {product.Short_Description}")
        else:
            print(f"✅ Produit de test existant: {product.Short_Description}")
        
        # Créer quelques numéros de série de test
        for i in range(1, 4):
            nserie, created = NSerie.objects.get_or_create(
                n_serie=f'NS-TEST-{i:03d}',
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
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données de test: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de l'API mobile avec numéros de série")
    
    try:
        # Créer des données de test si nécessaire
        test_create_sample_data()
        
        # Tester la récupération des produits avec numéros de série
        success = test_products_with_nserie()
        
        if success:
            print("\n🎉 Test réussi!")
        else:
            print("\n⚠️ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")

if __name__ == "__main__":
    main()
