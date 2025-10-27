"""
Script pour vérifier et diagnostiquer pourquoi l'API retourne une liste vide de produits
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.users.models import UserApp
from apps.masterdata.models import Product, Family, Account


def verify_user_products_data():
    """Vérifie les données pour l'utilisateur 8"""
    
    print("\n" + "="*80)
    print("🔍 DIAGNOSTIC: Produits pour l'utilisateur 8")
    print("="*80)
    
    # 1. Vérifier l'utilisateur
    print("\n📱 Étape 1: Vérification de l'utilisateur...")
    try:
        user = UserApp.objects.get(id=8)
        print(f"✓ Utilisateur trouvé: {user.username} ({user.prenom} {user.nom})")
    except UserApp.DoesNotExist:
        print("❌ Utilisateur 8 non trouvé")
        return
    
    # 2. Vérifier le compte
    print("\n🏢 Étape 2: Vérification du compte...")
    account = user.compte
    if not account:
        print("❌ Aucun compte associé à l'utilisateur")
        return
    
    print(f"✓ Compte trouvé: {account.account_name} ({account.reference})")
    print(f"  Statut: {account.account_statuts}")
    
    # 3. Vérifier les familles du compte
    print("\n📂 Étape 3: Vérification des familles du compte...")
    families = Family.objects.filter(compte=account)
    print(f"Nombre de familles pour ce compte: {families.count()}")
    
    if families.exists():
        for family in families[:5]:  # Afficher les 5 premières
            print(f"  • {family.family_name} ({family.reference}) - Statut: {family.family_status}")
    else:
        print("⚠️  Aucune famille trouvée pour ce compte")
    
    # 4. Vérifier les produits liés aux familles
    print("\n📦 Étape 4: Vérification des produits...")
    products = Product.objects.filter(
        Product_Family__compte=account,
        Product_Status='ACTIVE'
    )
    
    print(f"Nombre de produits ACTIFS pour ce compte: {products.count()}")
    
    if products.exists():
        print("\n✅ Produits trouvés:")
        for product in products[:10]:  # Afficher les 10 premiers
            print(f"  • {product.Short_Description} ({product.Internal_Product_Code})")
            print(f"    Famille: {product.Product_Family.family_name if product.Product_Family else 'Aucune'}")
    else:
        print("\n❌ Aucun produit trouvé pour ce compte")
        
        # Diagnostic approfondi
        print("\n🔍 Diagnostic approfondi...")
        
        # Vérifier les produits sans filtre de compte
        all_products = Product.objects.filter(Product_Status='ACTIVE').count()
        print(f"  Total de produits ACTIFS dans la base: {all_products}")
        
        # Vérifier les produits avec famille
        products_with_family = Product.objects.filter(
            Product_Status='ACTIVE',
            Product_Family__isnull=False
        ).count()
        print(f"  Produits ACTIFS avec famille: {products_with_family}")
        
        # Vérifier les comptes des familles
        print("\n  Répartition des produits par compte:")
        all_families = Family.objects.all()
        for family in all_families[:10]:
            count = Product.objects.filter(
                Product_Family=family,
                Product_Status='ACTIVE'
            ).count()
            if count > 0:
                print(f"    • {family.compte.account_name if family.compte else 'Sans compte'}: {count} produits")
    
    # 5. Recommandations
    print("\n" + "="*80)
    print("💡 RECOMMANDATIONS")
    print("="*80)
    
    if not families.exists():
        print("\n⚠️  Problème: Aucune famille liée au compte de l'utilisateur")
        print("Solutions possibles:")
        print("  1. Créer des familles pour le compte")
        print("  2. Lier des familles existantes au compte")
        print("\nExemple:")
        print(f"  Family.objects.filter(id=X).update(compte={account})")
    
    elif not products.exists():
        print("\n⚠️  Problème: Aucun produit lié aux familles du compte")
        print("Solutions possibles:")
        print("  1. Créer des produits pour les familles")
        print("  2. Assigner des produits existants aux familles du compte")
        print("\nExemple:")
        print(f"  family = Family.objects.filter(compte={account}).first()")
        print(f"  Product.objects.filter(id=X).update(Product_Family=family)")
    
    else:
        print("\n✅ Configuration correcte! Les produits sont disponibles.")
    
    print("\n" + "="*80)


def test_api_call():
    """Teste l'appel API"""
    print("\n" + "="*80)
    print("🌐 TEST DE L'API")
    print("="*80)
    
    from apps.mobile.repositories.user_repository import UserRepository
    
    repository = UserRepository()
    
    try:
        products = repository.get_products_by_user_account(8)
        print(f"\n✅ API retourne: {len(list(products))} produits")
        
        for product in list(products)[:5]:
            print(f"  • {product.Short_Description}")
    
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    verify_user_products_data()
    test_api_call()

