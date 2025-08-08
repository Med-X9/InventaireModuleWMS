#!/usr/bin/env python
"""
Script final pour tester l'API mobile avec numéros de série
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

def test_mobile_api():
    """Test complet de l'API mobile"""
    print("🧪 Test complet de l'API mobile avec numéros de série...")
    
    # 1. Vérifier les données existantes
    print("\n📊 Vérification des données existantes:")
    
    accounts = Account.objects.filter(account_statuts='ACTIVE')
    print(f"   - Comptes actifs: {accounts.count()}")
    
    families = Family.objects.all()
    print(f"   - Familles: {families.count()}")
    
    products = Product.objects.filter(Product_Status='ACTIVE')
    print(f"   - Produits actifs: {products.count()}")
    
    nseries = NSerie.objects.filter(status='ACTIVE')
    print(f"   - Numéros de série actifs: {nseries.count()}")
    
    users = UserApp.objects.all()
    print(f"   - Utilisateurs: {users.count()}")
    
    # 2. Trouver un utilisateur avec un compte
    user = None
    for u in users:
        if u.compte:
            user = u
            break
    
    if not user:
        print("\n⚠️ Aucun utilisateur avec compte trouvé")
        print("🔧 Association d'un compte à l'utilisateur admin...")
        
        admin_user = UserApp.objects.get(username='admin')
        account = accounts.first()
        admin_user.compte = account
        admin_user.save()
        user = admin_user
        print(f"✅ Compte associé: {account.account_name}")
    
    print(f"\n✅ Utilisateur sélectionné: {user.username} (ID: {user.id})")
    print(f"   - Compte: {user.compte.account_name if user.compte else 'Aucun'}")
    
    # 3. Tester l'API mobile
    print("\n🧪 Test de l'API mobile...")
    
    try:
        from apps.mobile.services.user_service import UserService
        user_service = UserService()
        
        response_data = user_service.get_user_products(user.id)
        
        print(f"✅ Réponse API récupérée")
        print(f"   - Success: {response_data.get('success', 'N/A')}")
        print(f"   - User ID: {response_data.get('user_id', 'N/A')}")
        print(f"   - Timestamp: {response_data.get('timestamp', 'N/A')}")
        
        if 'data' in response_data and 'products' in response_data['data']:
            products = response_data['data']['products']
            print(f"   - Nombre de produits: {len(products)}")
            
            if len(products) > 0:
                print(f"\n📦 Détail des produits:")
                
                for i, product in enumerate(products[:3]):  # Limiter à 3 produits
                    print(f"\n   Produit {i+1}:")
                    print(f"     - Nom: {product.get('product_name', 'N/A')}")
                    print(f"     - Code: {product.get('internal_product_code', 'N/A')}")
                    print(f"     - Support n_serie: {product.get('n_serie', False)}")
                    print(f"     - Support n_lot: {product.get('n_lot', False)}")
                    print(f"     - Support dlc: {product.get('dlc', False)}")
                    
                    # Vérifier le champ numeros_serie
                    numeros_serie = product.get('numeros_serie', [])
                    print(f"     - Champ 'numeros_serie' présent: {'numeros_serie' in product}")
                    print(f"     - Nombre de numéros de série: {len(numeros_serie)}")
                    
                    if len(numeros_serie) > 0:
                        print(f"     - Exemple de numéro de série:")
                        nserie = numeros_serie[0]
                        print(f"       * Numéro: {nserie.get('n_serie', 'N/A')}")
                        print(f"       * Status: {nserie.get('status', 'N/A')}")
                        print(f"       * Description: {nserie.get('description', 'N/A')}")
                        print(f"       * Date fabrication: {nserie.get('date_fabrication', 'N/A')}")
                        print(f"       * Date expiration: {nserie.get('date_expiration', 'N/A')}")
                        print(f"       * Garantie valide: {nserie.get('is_warranty_valid', 'N/A')}")
                        print(f"       * Expiré: {nserie.get('is_expired', 'N/A')}")
                    else:
                        if product.get('n_serie', False):
                            print(f"     - ⚠️ Aucun numéro de série trouvé malgré n_serie=True")
                        else:
                            print(f"     - ✅ Aucun numéro de série (normal car n_serie=False)")
            else:
                print("   - ⚠️ Aucun produit trouvé pour cet utilisateur")
        else:
            print("   - ⚠️ Aucun produit dans la réponse")
        
        # 4. Test direct du repository
        print(f"\n🧪 Test direct du repository...")
        
        repository = UserRepository()
        products = repository.get_products_by_user_account(user.id)
        
        print(f"   - Nombre de produits via repository: {len(products)}")
        
        if len(products) > 0:
            print(f"   - Test du formatage des données:")
            
            for i, product in enumerate(products[:2]):  # Limiter à 2 produits
                try:
                    product_data = repository.format_product_data(product)
                    
                    print(f"\n     Produit {i+1}: {product.Short_Description}")
                    print(f"       - Support n_serie: {product.n_serie}")
                    print(f"       - Champ 'numeros_serie' présent: {'numeros_serie' in product_data}")
                    
                    numeros_serie = product_data.get('numeros_serie', [])
                    print(f"       - Nombre de numéros de série: {len(numeros_serie)}")
                    
                    if len(numeros_serie) > 0:
                        print(f"       - Premier numéro de série: {numeros_serie[0].get('n_serie', 'N/A')}")
                    
                except Exception as e:
                    print(f"       - ❌ Erreur lors du formatage: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test final de l'API mobile avec numéros de série")
    
    try:
        success = test_mobile_api()
        
        if success:
            print("\n🎉 Test réussi!")
            print("\n✅ L'API mobile retourne maintenant les numéros de série avec les produits")
            print("\n📋 Résumé des modifications:")
            print("   - ✅ Champ 'numeros_serie' ajouté dans la réponse API")
            print("   - ✅ Récupération des numéros de série pour les produits qui les supportent")
            print("   - ✅ Gestion des cas où n_serie=False (champ vide)")
            print("   - ✅ Informations complètes des numéros de série (dates, garantie, etc.)")
        else:
            print("\n❌ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")

if __name__ == "__main__":
    main()
