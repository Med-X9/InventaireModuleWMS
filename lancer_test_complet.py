#!/usr/bin/env python
"""
Script de lancement simple pour le test complet de 1000 lignes
"""

import subprocess
import sys
import os

def main():
    print("🚀 LANCEMENT DU TEST COMPLET 1000 LIGNES")
    print("=" * 60)
    print()
    print("Ce test va:")
    print("✅ Créer toutes les données nécessaires automatiquement")
    print("✅ Tester 5 cas différents avec 1000+ CountingDetail")
    print("✅ Mesurer les performances de chaque cas")
    print("✅ Générer un rapport détaillé")
    print()
    print("Cas de test inclus:")
    print("  1. Mode 'en vrac' sans produit (200 lignes)")
    print("  2. Mode 'par article' avec produit (300 lignes)")
    print("  3. Mode 'image de stock' avec numéros de série (250 lignes)")
    print("  4. Cas complets avec toutes propriétés (200 lignes)")
    print("  5. Variations aléatoires (50 lignes)")
    print("  TOTAL: 1000 lignes")
    print()
    
    confirm = input("Voulez-vous lancer le test complet ? (O/n): ").lower().strip()
    if confirm in ['n', 'non', 'no']:
        print("Test annulé.")
        return
    
    print("\n🔄 Lancement du test...")
    print("=" * 40)
    
    try:
        # Exécuter le test
        result = subprocess.run([
            sys.executable, 
            'test_1000_lignes_complet.py'
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Test terminé avec succès!")
        else:
            print(f"\n❌ Test terminé avec des erreurs (code: {result.returncode})")
            
    except Exception as e:
        print(f"\n❌ Erreur lors du lancement: {e}")
        print("\n💡 Essayez de lancer directement:")
        print("python test_1000_lignes_complet.py")

if __name__ == "__main__":
    main()
