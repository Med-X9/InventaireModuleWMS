#!/usr/bin/env python3
"""
Vérification simple de l'utilisation du numéro de série
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import CountingDetail, NSerie
from apps.masterdata.models import NSerie as MasterNSerie
from apps.masterdata.models import Product

def simple_nserie_check():
    """Vérification simple de l'utilisation du numéro de série"""
    
    print("🔍 Vérification simple de l'utilisation du numéro de série")
    print("=" * 70)
    
    product_id = 13118
    nserie_test = "1234567iuytr"
    
    print(f"📋 Produit: {product_id}")
    print(f"🔢 Numéro de série: {nserie_test}")
    print()
    
    # 1. Vérifier le produit
    try:
        product = Product.objects.get(id=product_id)
        print(f"✅ Produit: {product.Short_Description}")
        print(f"📋 Propriétés: DLC={product.dlc}, n_lot={product.n_lot}, n_serie={product.n_serie}")
    except Exception as e:
        print(f"❌ Erreur produit: {e}")
        return
    
    print()
    
    # 2. Vérifier dans masterdata.NSerie
    print("2. Vérification dans masterdata.NSerie...")
    try:
        master_nserie = MasterNSerie.objects.filter(
            product_id=product_id,
            n_serie=nserie_test
        ).first()
        
        if master_nserie:
            print(f"   ✅ Trouvé dans masterdata.NSerie (ID: {master_nserie.id})")
        else:
            print(f"   ❌ NON trouvé dans masterdata.NSerie")
            return
            
    except Exception as e:
        print(f"   ❌ Erreur masterdata: {e}")
        return
    
    print()
    
    # 3. Vérifier dans inventory.NSerie (CountingDetail)
    print("3. Vérification dans inventory.NSerie (CountingDetail)...")
    try:
        inventory_nserie = NSerie.objects.filter(
            counting_detail__product_id=product_id,
            n_serie=nserie_test
        ).first()
        
        if inventory_nserie:
            print(f"   ❌ DÉJÀ UTILISÉ dans inventory.NSerie")
            print(f"   📍 ID: {inventory_nserie.id}")
            print(f"   🏷️  Référence: {inventory_nserie.reference}")
            
            # Récupérer le CountingDetail associé
            counting_detail = inventory_nserie.counting_detail
            if counting_detail:
                print(f"   📊 CountingDetail ID: {counting_detail.id}")
                print(f"   🏷️  Référence: {counting_detail.reference}")
                
        else:
            print(f"   ✅ NON utilisé dans inventory.NSerie")
            
    except Exception as e:
        print(f"   ❌ Erreur inventory: {e}")
    
    print()
    
    # 4. Compter les CountingDetail pour ce produit
    print("4. Compter les CountingDetail pour ce produit...")
    try:
        count = CountingDetail.objects.filter(product_id=product_id).count()
        print(f"   📊 Total CountingDetail: {count}")
        
        if count > 0:
            print("   📋 IDs des CountingDetail:")
            for cd in CountingDetail.objects.filter(product_id=product_id)[:5]:
                print(f"      - ID: {cd.id}, Réf: {cd.reference}")
                
    except Exception as e:
        print(f"   ❌ Erreur comptage: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Vérification terminée")

if __name__ == "__main__":
    simple_nserie_check()
