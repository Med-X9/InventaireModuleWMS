#!/usr/bin/env python3
"""
Vérifier le mode de comptage du counting ID 1
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Counting

def check_counting_mode():
    """Vérifier le mode de comptage du counting ID 1"""
    
    print("🔍 Vérification du mode de comptage du counting ID 1")
    print("=" * 60)
    
    try:
        counting = Counting.objects.get(id=1)
        
        print(f"✅ Counting trouvé: ID {counting.id}")
        print(f"   Mode de comptage: {counting.count_mode}")
        print(f"   N_SERIE activé: {counting.n_serie}")
        print(f"   Autres champs: {[f.name for f in counting._meta.fields if f.name not in ['id', 'count_mode', 'n_serie']]}")
        
        # Vérifier si c'est le bon mode pour déclencher la validation
        if counting.count_mode == "par article":
            print("✅ Mode 'par article' - la validation des propriétés du produit devrait être déclenchée")
        else:
            print(f"❌ Mode '{counting.count_mode}' - la validation des propriétés du produit ne sera PAS déclenchée")
            print("   C'est pourquoi n_lot=null est accepté !")
            
    except Counting.DoesNotExist:
        print("❌ Counting avec l'ID 1 non trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    check_counting_mode()
