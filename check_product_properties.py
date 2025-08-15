#!/usr/bin/env python3
"""
Vérifier les propriétés du produit 13118
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.masterdata.models import Product

def check_product():
    """Vérifier les propriétés du produit 13118"""
    
    print("🔍 Vérification des propriétés du produit 13118")
    print("=" * 50)
    
    try:
        product = Product.objects.get(id=13118)
        
        print(f"✅ Produit trouvé: {product.name if hasattr(product, 'name') else 'ID: 13118'}")
        print(f"   DLC requis: {getattr(product, 'dlc', 'Non défini')}")
        print(f"   N_LOT requis: {getattr(product, 'n_lot', 'Non défini')}")
        print(f"   N_SERIE requis: {getattr(product, 'n_serie', 'Non défini')}")
        
        # Vérifier si le produit a n_lot=True
        if hasattr(product, 'n_lot') and product.n_lot:
            print("   ⚠️  Ce produit nécessite un numéro de lot (n_lot=True)")
            print("   ❌ L'API devrait rejeter n_lot=null")
        else:
            print("   ✅ Ce produit n'a pas besoin de numéro de lot")
            print("   ✅ L'API devrait accepter n_lot=null")
            
    except Product.DoesNotExist:
        print("❌ Produit avec l'ID 13118 non trouvé")
        print("   Vérifiez que ce produit existe dans votre base de données")
        
        # Lister quelques produits existants
        print("\n📋 Produits disponibles (premiers 5):")
        products = Product.objects.all()[:5]
        for p in products:
            print(f"   - ID: {p.id}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    check_product()
