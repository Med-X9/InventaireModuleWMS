"""
Script pour diagnostiquer pourquoi l'API retourne une liste vide de stocks
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.users.models import UserApp
from apps.masterdata.models import Stock, Warehouse, Location, Product
from apps.inventory.models import Inventory, Setting


def verify_user_stocks_data():
    """Vérifie les données de stocks pour l'utilisateur 8"""
    
    print("\n" + "="*80)
    print("🔍 DIAGNOSTIC: Stocks pour l'utilisateur 8")
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
    
    # 3. Vérifier les entrepôts liés au compte via Settings
    print("\n🏭 Étape 3: Vérification des entrepôts...")
    warehouses = Warehouse.objects.filter(awi_links__account=account).distinct()
    print(f"Nombre d'entrepôts liés au compte: {warehouses.count()}")
    
    if warehouses.exists():
        for warehouse in warehouses[:3]:
            print(f"  • {warehouse.warehouse_name} ({warehouse.reference})")
    else:
        print("⚠️  Aucun entrepôt lié au compte via Settings")
    
    # 4. Vérifier les emplacements
    print("\n📍 Étape 4: Vérification des emplacements...")
    if warehouses.exists():
        locations = Location.objects.filter(
            sous_zone__zone__warehouse__in=warehouses,
            is_active=True
        )
        print(f"Nombre d'emplacements actifs: {locations.count()}")
        
        if locations.exists():
            for location in locations[:5]:
                print(f"  • {location.location_reference}")
        else:
            print("⚠️  Aucun emplacement trouvé")
    else:
        locations = Location.objects.none()
        print("⚠️  Impossible de vérifier (pas d'entrepôts)")
    
    # 5. Vérifier les stocks
    print("\n📦 Étape 5: Vérification des stocks...")
    if warehouses.exists():
        stocks = Stock.objects.filter(
            location__sous_zone__zone__warehouse__in=warehouses
        )
        print(f"Nombre de stocks pour ce compte: {stocks.count()}")
        
        if stocks.exists():
            print("\n✅ Stocks trouvés:")
            for stock in stocks[:10]:
                print(f"  • {stock.reference}")
                if stock.product:
                    print(f"    Produit: {stock.product.Short_Description}")
                if stock.location:
                    print(f"    Emplacement: {stock.location.location_reference}")
                print(f"    Quantité: {stock.quantity_available}")
        else:
            print("\n❌ Aucun stock trouvé pour ce compte")
            
            # Diagnostic approfondi
            print("\n🔍 Diagnostic approfondi...")
            all_stocks = Stock.objects.all().count()
            print(f"  Total de stocks dans la base: {all_stocks}")
            
            if all_stocks > 0:
                print("\n  Exemples de stocks existants (autres comptes):")
                sample_stocks = Stock.objects.select_related('location', 'product')[:5]
                for stock in sample_stocks:
                    warehouse_name = "N/A"
                    if stock.location and stock.location.sous_zone and stock.location.sous_zone.zone:
                        warehouse_name = stock.location.sous_zone.zone.warehouse.warehouse_name
                    print(f"    • {stock.reference} - Entrepôt: {warehouse_name}")
    else:
        print("⚠️  Impossible de vérifier (pas d'entrepôts)")
    
    # 6. Vérifier les inventaires
    print("\n📋 Étape 6: Vérification des inventaires...")
    inventories = Inventory.objects.filter(awi_links__account=account)
    print(f"Nombre d'inventaires pour ce compte: {inventories.count()}")
    
    if inventories.exists():
        for inventory in inventories[:3]:
            print(f"  • {inventory.label} ({inventory.reference}) - Statut: {inventory.status}")
            
            # Vérifier les stocks de cet inventaire
            inventory_stocks = Stock.objects.filter(inventory=inventory)
            print(f"    Stocks: {inventory_stocks.count()}")
    
    # 7. Recommandations
    print("\n" + "="*80)
    print("💡 RECOMMANDATIONS")
    print("="*80)
    
    if not warehouses.exists():
        print("\n⚠️  Problème: Aucun entrepôt lié au compte")
        print("Solutions:")
        print("  1. Créer un Setting (lien compte-entrepôt-inventaire)")
        print("  2. Utiliser un inventaire existant")
    
    elif not stocks.exists():
        print("\n⚠️  Problème: Aucun stock pour ce compte")
        print("Solutions:")
        print("  1. Importer des stocks via Excel")
        print("  2. Créer des stocks de test")
        print("\nExemple de création de stock:")
        if warehouses.exists() and locations.exists():
            inventory = inventories.first() if inventories.exists() else None
            location = locations.first()
            print(f"  Stock.objects.create(")
            print(f"      location={location},")
            print(f"      product=Product.objects.first(),")
            print(f"      quantity_available=100,")
            print(f"      inventory={inventory},")
            print(f"      unit_of_measure=UnitOfMeasure.objects.first()")
            print(f"  )")
    else:
        print("\n✅ Configuration correcte! Les stocks sont disponibles.")
    
    print("\n" + "="*80)


def test_api_call():
    """Teste l'appel API des stocks"""
    print("\n" + "="*80)
    print("🌐 TEST DE L'API STOCKS")
    print("="*80)
    
    from apps.mobile.repositories.user_repository import UserRepository
    
    repository = UserRepository()
    
    try:
        stocks = repository.get_stocks_by_user_account(8)
        stocks_list = list(stocks)
        print(f"\n✅ API retourne: {len(stocks_list)} stocks")
        
        if stocks_list:
            for stock in stocks_list[:5]:
                print(f"  • {stock.reference} - Qté: {stock.quantity_available}")
        else:
            print("\n❌ Liste vide")
    
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)


if __name__ == '__main__':
    verify_user_stocks_data()
    test_api_call()


