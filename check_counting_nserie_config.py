#!/usr/bin/env python3
"""
Vérification de la configuration n_serie du comptage
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Counting, CountingDetail

def check_counting_nserie_config():
    """Vérification de la configuration n_serie du comptage"""
    
    print("🔍 Vérification de la configuration n_serie du comptage")
    print("=" * 70)
    
    counting_id = 17
    
    print(f"📋 Comptage ID: {counting_id}")
    print()
    
    # 1. Vérifier le comptage
    try:
        counting = Counting.objects.get(id=counting_id)
        print(f"✅ Comptage trouvé: {counting.reference}")
        print(f"📋 Mode: {counting.count_mode}")
        print(f"📱 n_serie activé: {counting.n_serie}")
        print(f"📅 Créé le: {counting.created_at}")
        
        if not counting.n_serie:
            print("❌ PROBLÈME: n_serie est FALSE dans le comptage!")
            print("💡 C'est pourquoi les numéros de série ne sont pas créés")
        else:
            print("✅ n_serie est TRUE - la configuration est correcte")
            
    except Counting.DoesNotExist:
        print(f"❌ Comptage {counting_id} non trouvé")
        return
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    print()
    
    # 2. Vérifier le dernier CountingDetail créé
    print("2. Vérifier le dernier CountingDetail créé...")
    try:
        latest_counting_detail = CountingDetail.objects.filter(
            counting_id=counting_id
        ).order_by('-created_at').first()
        
        if latest_counting_detail:
            print(f"   📊 Dernier CountingDetail: {latest_counting_detail.reference}")
            print(f"   📅 Créé le: {latest_counting_detail.created_at}")
            print(f"   📱 Produit: {latest_counting_detail.product_id}")
            
            # Vérifier les numéros de série associés
            nseries = latest_counting_detail.nserie_set.all()
            print(f"   🔢 Numéros de série associés: {nseries.count()}")
            
            if nseries.exists():
                for ns in nseries:
                    print(f"      - {ns.n_serie} (ID: {ns.id})")
            else:
                print("      ❌ Aucun numéro de série créé!")
                
        else:
            print("   ❌ Aucun CountingDetail trouvé pour ce comptage")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print()
    
    # 3. Vérifier tous les comptages avec n_serie=True
    print("3. Vérifier tous les comptages avec n_serie=True...")
    try:
        countings_with_nserie = Counting.objects.filter(n_serie=True)
        print(f"   📊 Total comptages avec n_serie=True: {countings_with_nserie.count()}")
        
        if countings_with_nserie.exists():
            print("   📋 Liste des comptages avec n_serie=True:")
            for c in countings_with_nserie[:5]:
                print(f"      - ID: {c.id}, Réf: {c.reference}, Mode: {c.count_mode}")
            if countings_with_nserie.count() > 5:
                print(f"      ... et {countings_with_nserie.count() - 5} autres")
                
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Vérification terminée")

if __name__ == "__main__":
    check_counting_nserie_config()
