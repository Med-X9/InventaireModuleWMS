"""
Test du formatage des stocks pour identifier les erreurs
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.mobile.repositories.user_repository import UserRepository
from apps.masterdata.models import Stock


def test_stock_formatting():
    """Test le formatage d'un stock"""
    
    print("\n" + "="*80)
    print("🧪 TEST DU FORMATAGE DES STOCKS")
    print("="*80)
    
    repository = UserRepository()
    
    # Récupérer quelques stocks
    stocks = Stock.objects.all()[:5]
    
    print(f"\n📦 Test avec {stocks.count()} stocks...")
    
    success_count = 0
    error_count = 0
    
    for stock in stocks:
        print(f"\n{'='*80}")
        print(f"Stock: {stock.reference}")
        print(f"{'='*80}")
        
        # Informations du stock
        print(f"ID: {stock.id}")
        print(f"Produit: {stock.product.Short_Description if stock.product else 'Aucun'}")
        print(f"Emplacement: {stock.location.location_reference if stock.location else 'Aucun'}")
        print(f"Quantité: {stock.quantity_available}")
        print(f"Unité: {stock.unit_of_measure if hasattr(stock, 'unit_of_measure') and stock.unit_of_measure else 'Aucune'}")
        print(f"Inventaire: {stock.inventory.reference if stock.inventory else 'Aucun'}")
        
        # Tester le formatage
        try:
            formatted = repository.format_stock_data(stock)
            print("\n✅ Formatage réussi")
            print(f"   Keys: {list(formatted.keys())}")
            success_count += 1
        except Exception as e:
            print(f"\n❌ Erreur de formatage: {str(e)}")
            error_count += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print(f"📊 RÉSULTAT")
    print("="*80)
    print(f"✅ Réussis: {success_count}")
    print(f"❌ Erreurs: {error_count}")
    
    if error_count > 0:
        print("\n⚠️  Des erreurs de formatage ont été détectées!")
        print("Cela explique pourquoi la liste est vide dans l'API.")
    else:
        print("\n✅ Tous les formatages réussissent")
        print("Le problème est ailleurs...")


def test_unit_of_measure_field():
    """Vérifie si le champ unit_of_measure existe sur Stock"""
    
    print("\n" + "="*80)
    print("🔍 VÉRIFICATION DU MODÈLE STOCK")
    print("="*80)
    
    stock = Stock.objects.first()
    
    if not stock:
        print("❌ Aucun stock dans la base")
        return
    
    print(f"\n📦 Stock: {stock.reference}")
    print(f"\nChamps du modèle Stock:")
    
    # Lister tous les champs
    for field in stock._meta.get_fields():
        field_name = field.name
        try:
            value = getattr(stock, field_name)
            print(f"  • {field_name}: {value}")
        except Exception as e:
            print(f"  • {field_name}: Erreur - {e}")
    
    # Vérifier spécifiquement unit_of_measure
    print("\n🔍 Vérification de unit_of_measure:")
    if hasattr(stock, 'unit_of_measure'):
        print(f"  ✅ Champ existe")
        try:
            uom = stock.unit_of_measure
            print(f"  Valeur: {uom}")
            if uom:
                print(f"  Type: {type(uom)}")
                if hasattr(uom, 'name'):
                    print(f"  Nom: {uom.name}")
        except Exception as e:
            print(f"  ❌ Erreur d'accès: {e}")
    else:
        print(f"  ❌ Champ n'existe pas sur le modèle")


if __name__ == '__main__':
    test_unit_of_measure_field()
    test_stock_formatting()


