#!/usr/bin/env python3
"""
Trouver un counting en mode "par article"
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Counting

def find_par_article_counting():
    """Trouver un counting en mode 'par article'"""
    
    print("🔍 Recherche d'un counting en mode 'par article'")
    print("=" * 60)
    
    try:
        # Chercher tous les countings
        countings = Counting.objects.all()
        
        print(f"📊 Total de countings trouvés: {countings.count()}")
        
        # Lister tous les modes
        modes = {}
        for counting in countings:
            mode = counting.count_mode
            if mode not in modes:
                modes[mode] = []
            modes[mode].append(counting.id)
        
        print(f"\n📋 Modes de comptage disponibles:")
        for mode, ids in modes.items():
            print(f"   - {mode}: {len(ids)} counting(s) - IDs: {ids[:5]}{'...' if len(ids) > 5 else ''}")
        
        # Chercher un counting en mode "par article"
        par_article_countings = Counting.objects.filter(count_mode="par article")
        
        if par_article_countings.exists():
            counting = par_article_countings.first()
            print(f"\n✅ Counting en mode 'par article' trouvé:")
            print(f"   ID: {counting.id}")
            print(f"   Mode: {counting.count_mode}")
            print(f"   N_SERIE: {counting.n_serie}")
            print(f"\n🎯 Utilisez counting_id={counting.id} pour tester la validation des propriétés du produit")
        else:
            print(f"\n❌ Aucun counting en mode 'par article' trouvé")
            print("   Créez-en un ou utilisez un autre mode")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    find_par_article_counting()
