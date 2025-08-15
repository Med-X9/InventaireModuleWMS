#!/usr/bin/env python3
"""
Debug simple pour identifier le problème avec NSerie
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

def debug_nserie_simple():
    """Debug simple pour identifier le problème avec NSerie"""
    
    print("🔍 Debug simple pour identifier le problème avec NSerie")
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
    
    # Test simple d'abord
    print("   🔍 Test simple: compter tous les NSerie...")
    try:
        total_nserie = NSerie.objects.count()
        print(f"      📊 Total NSerie dans inventory: {total_nserie}")
    except Exception as e:
        print(f"      ❌ Erreur comptage total: {e}")
        return
    
    # Test avec filtre simple
    print("   🔍 Test avec filtre simple...")
    try:
        nserie_with_nserie = NSerie.objects.filter(n_serie=nserie_test).count()
        print(f"      📊 NSerie avec n_serie='{nserie_test}': {nserie_with_nserie}")
    except Exception as e:
        print(f"      ❌ Erreur filtre simple: {e}")
        return
    
    # Test avec filtre sur le produit
    print("   🔍 Test avec filtre sur le produit...")
    try:
        nserie_with_product = NSerie.objects.filter(
            counting_detail__product_id=product_id
        ).count()
        print(f"      📊 NSerie avec product_id={product_id}: {nserie_with_product}")
    except Exception as e:
        print(f"      ❌ Erreur filtre produit: {e}")
        return
    
    # Test avec filtre combiné
    print("   🔍 Test avec filtre combiné...")
    try:
        nserie_combined = NSerie.objects.filter(
            counting_detail__product_id=product_id,
            n_serie=nserie_test
        ).count()
        print(f"      📊 NSerie combiné: {nserie_combined}")
        
        if nserie_combined > 0:
            print(f"      ❌ CONFLIT DÉTECTÉ! Le numéro de série est déjà utilisé")
        else:
            print(f"      ✅ Pas de conflit détecté")
            
    except Exception as e:
        print(f"      ❌ Erreur filtre combiné: {e}")
        return
    
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
    print("🏁 Debug terminé")

if __name__ == "__main__":
    debug_nserie_simple()
