#!/usr/bin/env python3
"""
Vérification détaillée de l'utilisation du numéro de série
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

def check_nserie_usage_detailed():
    """Vérification détaillée de l'utilisation du numéro de série"""
    
    print("🔍 Vérification détaillée de l'utilisation du numéro de série")
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
    except Product.DoesNotExist:
        print(f"❌ Produit {product_id} non trouvé")
        return
    except Exception as e:
        print(f"❌ Erreur: {e}")
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
            print(f"   ✅ Trouvé dans masterdata.NSerie")
            print(f"   📍 ID: {master_nserie.id}")
            print(f"   🏷️  Référence: {master_nserie.reference}")
            print(f"   📅 Créé le: {master_nserie.created_at}")
            print(f"   📊 Statut: {master_nserie.status}")
        else:
            print(f"   ❌ NON trouvé dans masterdata.NSerie")
            return
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
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
            print(f"   📅 Créé le: {inventory_nserie.created_at}")
            
            # Récupérer le CountingDetail associé
            counting_detail = inventory_nserie.counting_detail
            if counting_detail:
                print(f"   📊 CountingDetail ID: {counting_detail.id}")
                print(f"   🏷️  Référence: {counting_detail.reference}")
                print(f"   📅 Créé le: {counting_detail.created_at}")
                print(f"   📍 Location: {counting_detail.location_id}")
                print(f"   🔢 Quantité: {counting_detail.quantity_inventoried}")
                
                # Récupérer le Counting associé
                if counting_detail.counting:
                    print(f"   📋 Counting ID: {counting_detail.counting.id}")
                    print(f"   🎯 Mode: {counting_detail.counting.count_mode}")
                    
        else:
            print(f"   ✅ NON utilisé dans inventory.NSerie")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print()
    
    # 4. Vérifier tous les CountingDetail pour ce produit
    print("4. Tous les CountingDetail pour ce produit...")
    try:
        counting_details = CountingDetail.objects.filter(product_id=product_id)
        print(f"   📊 Total: {counting_details.count()} CountingDetail")
        
        if counting_details.exists():
            print("   📋 Liste des CountingDetail:")
            for cd in counting_details:
                print(f"      - ID: {cd.id}, Réf: {cd.reference}, Créé: {cd.created_at}")
                
                # Vérifier les numéros de série associés
                nseries = cd.nserie_set.all()
                if nseries.exists():
                    print(f"        📱 Numéros de série: {[ns.n_serie for ns in nseries]}")
                else:
                    print(f"        📱 Aucun numéro de série")
                    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print()
    
    # 5. Suggestions
    print("5. Suggestions...")
    try:
        # Trouver des numéros de série non utilisés
        master_nseries = MasterNSerie.objects.filter(product_id=product_id)
        used_nseries = NSerie.objects.filter(
            counting_detail__product_id=product_id
        ).values_list('n_serie', flat=True)
        
        available_nseries = [ns.n_serie for ns in master_nseries if ns.n_serie not in used_nseries]
        
        if available_nseries:
            print(f"   💡 Numéros de série disponibles (non utilisés):")
            for ns in available_nseries:
                print(f"      - {ns}")
        else:
            print(f"   ⚠️  Tous les numéros de série de masterdata sont déjà utilisés")
            print(f"   💡 Vous devez ajouter de nouveaux numéros de série dans masterdata")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Vérification terminée")

if __name__ == "__main__":
    check_nserie_usage_detailed()
