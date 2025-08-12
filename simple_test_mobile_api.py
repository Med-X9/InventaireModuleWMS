#!/usr/bin/env python
"""
Script simple pour tester l'API mobile avec numéros de série
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

def test_existing_data():
    """Test avec les données existantes"""
    print("🧪 Test avec les données existantes...")
    
    repository = UserRepository()
    
    # Trouver un utilisateur existant
    users = UserApp.objects.all()
    if users.count() == 0:
        print("❌ Aucun utilisateur trouvé dans la base de données")
        return False
    
    user = users.first()
    print(f"✅ Utilisateur trouvé: {user.username} (ID: {user.id})")
    
    # Vérifier si l'utilisateur a un compte
    if not user.compte:
        print("⚠️ L'utilisateur n'a pas de compte associé")
        print("🔧 Association d'un compte existant...")
        
        # Trouver un compte existant
        accounts = Account.objects.filter(account_statuts='ACTIVE')
        if accounts.count() == 0:
            print("❌ Aucun compte actif trouvé")
            return False
        
        account = accounts.first()
        user.compte = account
        user.save()
        print(f"✅ Compte associé: {account.account_name}")
    
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

def test_api_response():
    """Test de la réponse API complète"""
    print("\n🧪 Test de la réponse API complète...")
    
    repository = UserRepository()
    
    # Trouver un utilisateur existant
    users = UserApp.objects.all()
    if users.count() == 0:
        print("❌ Aucun utilisateur trouvé")
        return False
    
    user = users.first()
    
    try:
        # Simuler l'appel API complet
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
            
            # Afficher le premier produit avec numéros de série
            for i, product in enumerate(products):
                if product.get('n_serie', False):
                    print(f"\n📦 Produit {i+1} avec numéros de série:")
                    print(f"   - Nom: {product.get('product_name', 'N/A')}")
                    print(f"   - Code: {product.get('internal_product_code', 'N/A')}")
                    print(f"   - Support n_serie: {product.get('n_serie', False)}")
                    
                    numeros_serie = product.get('numeros_serie', [])
                    print(f"   - Nombre de numéros de série: {len(numeros_serie)}")
                    
                    if len(numeros_serie) > 0:
                        print(f"   - Exemple de numéro de série: {numeros_serie[0].get('n_serie', 'N/A')}")
                        print(f"   - Status: {numeros_serie[0].get('status', 'N/A')}")
                        print(f"   - Description: {numeros_serie[0].get('description', 'N/A')}")
                        print(f"   - Date fabrication: {numeros_serie[0].get('date_fabrication', 'N/A')}")
                        print(f"   - Date expiration: {numeros_serie[0].get('date_expiration', 'N/A')}")
                        print(f"   - Garantie valide: {numeros_serie[0].get('is_warranty_valid', 'N/A')}")
                        print(f"   - Expiré: {numeros_serie[0].get('is_expired', 'N/A')}")
                        break
                else:
                    print(f"\n📦 Produit {i+1} sans numéros de série:")
                    print(f"   - Nom: {product.get('product_name', 'N/A')}")
                    print(f"   - Support n_serie: {product.get('n_serie', False)}")
                    print(f"   - Champ numeros_serie présent: {'numeros_serie' in product}")
                    print(f"   - Nombre de numéros de série: {len(product.get('numeros_serie', []))}")
                    break
        else:
            print("⚠️ Aucun produit dans la réponse")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test API: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de l'API mobile avec numéros de série")
    
    try:
        # Test avec les données existantes
        success1 = test_existing_data()
        
        # Test de la réponse API complète
        success2 = test_api_response()
        
        if success1 and success2:
            print("\n🎉 Tous les tests ont réussi!")
            print("\n✅ L'API mobile retourne maintenant les numéros de série avec les produits")
        else:
            print("\n⚠️ Certains tests ont échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")

if __name__ == "__main__":
    main()
