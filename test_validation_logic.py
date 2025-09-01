#!/usr/bin/env python3
"""
Test unitaire de la logique de validation des propriétés du produit
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.usecases.counting_detail_creation import CountingDetailCreationUseCase
from apps.masterdata.models import Product

def test_validation_logic():
    """Test de la logique de validation directement"""
    
    print("🧪 Test de la logique de validation des propriétés du produit")
    print("=" * 70)
    
    # Créer une instance du use case
    use_case = CountingDetailCreationUseCase()
    
    # Test 1: Produit avec n_lot=True mais n_lot=null
    print("\n1. Test produit avec n_lot=True mais n_lot=null...")
    
    data_nlot_null = {
        "counting_id": 1,
        "location_id": 3942,
        "quantity_inventoried": 10,
        "assignment_id": 33,
        "product_id": 13118,        # Ce produit a n_lot=True
        "dlc": "2024-12-31",
        "n_lot": None,              # null (ERREUR ATTENDUE)
        "numeros_serie": [
            {"n_serie": "NS001-2024"}
        ]
    }
    
    try:
        # Simuler la validation
        errors = []
        use_case._validate_data(data_nlot_null)
        print("❌ Validation n'a pas levé d'erreur (problème)")
    except Exception as e:
        error_msg = str(e)
        print(f"✅ Erreur levée: {error_msg}")
        
        if "null n'est pas accepté" in error_msg:
            print("✅ Message d'erreur correct pour n_lot=null")
        else:
            print("❌ Message d'erreur incorrect")
    
    # Test 2: Produit avec n_lot=True et n_lot=""
    print("\n2. Test produit avec n_lot=True mais n_lot=''...")
    
    data_nlot_empty = {
        "counting_id": 1,
        "location_id": 3942,
        "quantity_inventoried": 10,
        "assignment_id": 33,
        "product_id": 13118,        # Ce produit a n_lot=True
        "dlc": "2024-12-31",
        "n_lot": "",                # Chaîne vide (ERREUR ATTENDUE)
        "numeros_serie": [
            {"n_serie": "NS001-2024"}
        ]
    }
    
    try:
        # Simuler la validation
        errors = []
        use_case._validate_data(data_nlot_empty)
        print("❌ Validation n'a pas levé d'erreur (problème)")
    except Exception as e:
        error_msg = str(e)
        print(f"✅ Erreur levée: {error_msg}")
        
        if "null n'est pas accepté" in error_msg:
            print("✅ Message d'erreur correct pour n_lot=''")
        else:
            print("❌ Message d'erreur incorrect")
    
    # Test 3: Produit avec n_lot=True et n_lot valide
    print("\n3. Test produit avec n_lot=True et n_lot valide...")
    
    data_nlot_valid = {
        "counting_id": 1,
        "location_id": 3942,
        "quantity_inventoried": 10,
        "assignment_id": 33,
        "product_id": 13118,        # Ce produit a n_lot=True
        "dlc": "2024-12-31",
        "n_lot": "LOT123",         # n_lot valide
        "numeros_serie": [
            {"n_serie": "NS001-2024"}
        ]
    }
    
    try:
        # Simuler la validation
        errors = []
        use_case._validate_data(data_nlot_valid)
        print("✅ Validation réussie avec n_lot valide")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erreur inattendue: {error_msg}")
    
    print("\n" + "=" * 70)
    print("🏁 Tests de logique terminés")

if __name__ == "__main__":
    test_validation_logic()
