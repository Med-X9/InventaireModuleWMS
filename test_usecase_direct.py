#!/usr/bin/env python3
"""
Test direct du use case sans passer par l'API
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.usecases.counting_detail_creation import CountingDetailCreationUseCase

def test_usecase_direct():
    """Test direct du use case"""
    
    print("🧪 Test direct du use case CountingDetailCreationUseCase")
    print("=" * 60)
    
    # Créer une instance du use case
    use_case = CountingDetailCreationUseCase()
    
    # Votre exemple exact
    data = {
        "counting_id": 1,                    # Obligatoire
        "location_id": 3942,                 # Obligatoire
        "quantity_inventoried": 10,          # Obligatoire
        "assignment_id": 33,                 # OBLIGATOIRE (nouveau)
        "product_id": 13118,                 # Optionnel (selon le mode)
        "dlc": "2024-12-31",                # Optionnel
        "n_lot": None,                       # Optionnel (MAIS ERREUR si product.n_lot=True)
        "numeros_serie": [                   # Optionnel
            {"n_serie": "NS001-2024"}
        ]
    }
    
    print("📤 Test avec les données:")
    print(f"   counting_id: {data['counting_id']}")
    print(f"   location_id: {data['location_id']}")
    print(f"   quantity_inventoried: {data['quantity_inventoried']}")
    print(f"   assignment_id: {data['assignment_id']}")
    print(f"   product_id: {data['product_id']}")
    print(f"   dlc: {data['dlc']}")
    print(f"   n_lot: {data['n_lot']} (type: {type(data['n_lot'])})")
    print(f"   numeros_serie: {data['numeros_serie']}")
    
    print("\n🔍 Test de validation des données...")
    
    try:
        # Test de validation des données
        use_case._validate_data(data)
        print("❌ PROBLÈME: La validation n'a pas levé d'erreur pour n_lot=null")
        
    except Exception as e:
        error_msg = str(e)
        print(f"✅ SUCCÈS: Erreur levée lors de la validation")
        print(f"   Message: {error_msg}")
        
        if "null n'est pas accepté" in error_msg:
            print("✅ SUCCÈS: Validation null fonctionne correctement")
        else:
            print("❌ Message d'erreur incorrect")
    
    print("\n🔍 Test de validation des propriétés du produit...")
    
    try:
        # Test de validation des propriétés du produit
        errors = []
        use_case._validate_product_properties(data, errors)
        
        if errors:
            print("✅ SUCCÈS: Erreurs de validation détectées:")
            for error in errors:
                print(f"   - {error}")
                
            # Vérifier le message spécifique
            if any("null n'est pas accepté" in error for error in errors):
                print("✅ SUCCÈS: Message 'null n'est pas accepté' trouvé")
            else:
                print("❌ Message 'null n'est pas accepté' manquant")
        else:
            print("❌ PROBLÈME: Aucune erreur de validation détectée")
            
    except Exception as e:
        print(f"❌ Erreur lors de la validation des propriétés: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_usecase_direct()
