#!/usr/bin/env python3
"""
Diagnostic de l'utilisation des numéros de série
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

def diagnostic_nserie_usage():
    """Diagnostic de l'utilisation des numéros de série"""
    
    print("🔍 Diagnostic de l'utilisation des numéros de série")
    print("=" * 70)
    
    # 1. Vérifier le produit
    product_id = 13118
    print(f"\n1. Vérification du produit {product_id}...")
    
    try:
        product = Product.objects.get(id=product_id)
        print(f"   ✅ Produit trouvé: {product.Short_Description}")
        print(f"   📋 Propriétés: DLC={product.dlc}, n_lot={product.n_lot}, n_serie={product.n_serie}")
    except Product.DoesNotExist:
        print(f"   ❌ Produit {product_id} non trouvé")
        return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 2. Vérifier les numéros de série dans masterdata
    print(f"\n2. Numéros de série dans masterdata.NSerie pour le produit {product_id}...")
    
    try:
        master_nseries = MasterNSerie.objects.filter(product_id=product_id)
        print(f"   📊 Total: {master_nseries.count()} numéro(s) de série")
        
        if master_nseries.exists():
            print("   📋 Liste des numéros de série:")
            for ns in master_nseries[:10]:  # Afficher les 10 premiers
                print(f"      - {ns.n_serie}")
            if master_nseries.count() > 10:
                print(f"      ... et {master_nseries.count() - 10} autres")
        else:
            print("   ❌ Aucun numéro de série trouvé dans masterdata")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 3. Vérifier l'utilisation dans CountingDetail
    print(f"\n3. Utilisation dans CountingDetail...")
    
    try:
        # Vérifier si le numéro de série 1234567iuytr est utilisé
        nserie_test = "1234567iuytr"
        
        # Chercher dans les CountingDetail existants
        counting_details = CountingDetail.objects.filter(product_id=product_id)
        print(f"   📊 Total CountingDetail pour ce produit: {counting_details.count()}")
        
        # Chercher spécifiquement le numéro de série
        nseries_used = NSerie.objects.filter(
            counting_detail__product_id=product_id
        ).values_list('n_serie', flat=True)
        
        print(f"   📊 Total numéros de série utilisés: {nseries_used.count()}")
        
        if nserie_test in nseries_used:
            print(f"   ❌ Le numéro de série '{nserie_test}' est DÉJÀ UTILISÉ")
            
            # Trouver dans quel CountingDetail
            counting_detail_used = CountingDetail.objects.filter(
                product_id=product_id,
                nserie__n_serie=nserie_test
            ).first()
            
            if counting_detail_used:
                print(f"   📍 Utilisé dans CountingDetail ID: {counting_detail_used.id}")
                print(f"   📅 Créé le: {counting_detail_used.created_at}")
                print(f"   🏷️  Référence: {counting_detail_used.reference}")
        else:
            print(f"   ✅ Le numéro de série '{nserie_test}' n'est PAS encore utilisé")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 4. Suggestions
    print(f"\n4. Suggestions...")
    
    try:
        # Trouver un numéro de série non utilisé
        master_nseries_list = list(master_nseries.values_list('n_serie', flat=True))
        used_nseries_list = list(nseries_used)
        
        available_nseries = [ns for ns in master_nseries_list if ns not in used_nseries_list]
        
        if available_nseries:
            print(f"   💡 Numéros de série disponibles (non utilisés):")
            for ns in available_nseries[:5]:  # Afficher les 5 premiers
                print(f"      - {ns}")
            if len(available_nseries) > 5:
                print(f"      ... et {len(available_nseries) - 5} autres")
        else:
            print(f"   ⚠️  Tous les numéros de série de masterdata sont déjà utilisés")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Diagnostic terminé")

if __name__ == "__main__":
    diagnostic_nserie_usage()
