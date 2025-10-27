"""
Script pour assigner des produits aux familles des comptes utilisateurs
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.users.models import UserApp
from apps.masterdata.models import Product, Family, Account


def assign_products_to_user_accounts():
    """Assigne des produits aux familles des comptes utilisateurs mobiles"""
    
    print("\n" + "="*80)
    print("🔧 ASSIGNATION DES PRODUITS AUX COMPTES UTILISATEURS")
    print("="*80)
    
    # Récupérer tous les utilisateurs mobiles avec compte
    users = UserApp.objects.filter(type='Mobile', compte__isnull=False)
    print(f"\n👥 Utilisateurs mobiles trouvés: {users.count()}")
    
    total_assigned = 0
    
    for user in users:
        print(f"\n{'='*80}")
        print(f"Traitement de l'utilisateur: {user.username} ({user.prenom} {user.nom})")
        print(f"{'='*80}")
        
        account = user.compte
        print(f"Compte: {account.account_name} ({account.reference})")
        
        # Récupérer ou créer une famille pour ce compte
        families = Family.objects.filter(compte=account)
        
        if not families.exists():
            print("⚠️  Aucune famille trouvée, création d'une famille...")
            family = Family.objects.create(
                family_name=f"Famille {account.account_name}",
                compte=account,
                family_status='ACTIVE',
                family_description=f"Famille pour le compte {account.account_name}"
            )
            print(f"✓ Famille créée: {family.family_name}")
        else:
            family = families.first()
            print(f"✓ Famille existante: {family.family_name}")
        
        # Vérifier combien de produits sont déjà liés
        existing_products = Product.objects.filter(
            Product_Family=family,
            Product_Status='ACTIVE'
        ).count()
        
        print(f"Produits actuellement liés: {existing_products}")
        
        # Si moins de 50 produits, en assigner plus
        if existing_products < 50:
            needed = 50 - existing_products
            print(f"🔄 Assignation de {needed} produits supplémentaires...")
            
            # Récupérer des produits actifs non encore assignés ou d'autres comptes
            available_products = Product.objects.filter(
                Product_Status='ACTIVE'
            ).exclude(
                Product_Family=family
            )[:needed]
            
            assigned_count = 0
            for product in available_products:
                old_family = product.Product_Family
                product.Product_Family = family
                product.save()
                assigned_count += 1
                
                if assigned_count <= 5:  # Afficher les 5 premiers
                    print(f"  ✓ {product.Short_Description} ({product.Internal_Product_Code})")
                    if old_family:
                        print(f"    De: {old_family.family_name} → À: {family.family_name}")
            
            if assigned_count > 5:
                print(f"  ... et {assigned_count - 5} autres produits")
            
            total_assigned += assigned_count
            print(f"✅ {assigned_count} produits assignés")
        else:
            print(f"✅ Suffisamment de produits déjà assignés ({existing_products})")
    
    print("\n" + "="*80)
    print(f"✅ TOTAL: {total_assigned} produits assignés")
    print("="*80)
    
    return total_assigned


def verify_assignments():
    """Vérifie que tous les utilisateurs mobiles ont des produits"""
    
    print("\n" + "="*80)
    print("🔍 VÉRIFICATION DES ASSIGNATIONS")
    print("="*80)
    
    users = UserApp.objects.filter(type='Mobile', compte__isnull=False)
    
    all_ok = True
    
    for user in users:
        account = user.compte
        families = Family.objects.filter(compte=account)
        
        if not families.exists():
            print(f"❌ {user.username}: Aucune famille")
            all_ok = False
            continue
        
        products_count = Product.objects.filter(
            Product_Family__in=families,
            Product_Status='ACTIVE'
        ).count()
        
        if products_count == 0:
            print(f"❌ {user.username} ({account.account_name}): 0 produits")
            all_ok = False
        else:
            print(f"✅ {user.username} ({account.account_name}): {products_count} produits")
    
    print("\n" + "="*80)
    if all_ok:
        print("✅ TOUS LES UTILISATEURS ONT DES PRODUITS")
    else:
        print("⚠️  CERTAINS UTILISATEURS N'ONT PAS DE PRODUITS")
    print("="*80)
    
    return all_ok


def test_api_for_user_8():
    """Teste l'API pour l'utilisateur 8"""
    
    print("\n" + "="*80)
    print("🧪 TEST DE L'API POUR L'UTILISATEUR 8")
    print("="*80)
    
    from apps.mobile.repositories.user_repository import UserRepository
    
    repository = UserRepository()
    
    try:
        products = repository.get_products_by_user_account(8)
        products_list = list(products)
        
        print(f"\n✅ API retourne: {len(products_list)} produits")
        
        if products_list:
            print("\n📦 Exemples de produits retournés:")
            for product in products_list[:10]:
                print(f"  • {product.Short_Description} ({product.Internal_Product_Code})")
                print(f"    Famille: {product.Product_Family.family_name}")
        else:
            print("\n❌ Liste vide - le problème persiste")
    
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)


def main():
    """Fonction principale"""
    
    print("\n🚀 DÉMARRAGE DU SCRIPT DE CORRECTION DES PRODUITS")
    
    try:
        # Étape 1: Assigner les produits
        assign_products_to_user_accounts()
        
        # Étape 2: Vérifier les assignations
        verify_assignments()
        
        # Étape 3: Tester l'API
        test_api_for_user_8()
        
        print("\n💡 L'API devrait maintenant retourner des produits pour l'utilisateur 8!")
        print("   Testez avec: GET /api/mobile/user/8/products/")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

