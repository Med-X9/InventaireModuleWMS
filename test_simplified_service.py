#!/usr/bin/env python3
"""
Test du service simplifié utilisant le CountingDetailCreationUseCase.
"""

import os
import sys
import django
import json
import requests

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.mobile.services.counting_detail_service import CountingDetailService

def test_service():
    """Test du service simplifié."""
    
    print("🧪 TEST DU SERVICE SIMPLIFIÉ")
    print("=" * 50)
    
    # Créer le service
    service = CountingDetailService()
    
    # Données de test (un seul enregistrement valide)
    test_data = {
        "counting_id": 17,
        "location_id": 3930,
        "quantity_inventoried": 10,
        "assignment_id": 55,
        "product_id": 13118,
        "dlc": "2024-12-31",
        "n_lot": "LOT123",
        "numeros_serie": [
            {"n_serie": "1234trew"}
        ]
    }
    
    print(f"📝 Test avec les données: {json.dumps(test_data, indent=2)}")
    
    try:
        # Test de création individuelle
        print(f"\n✅ Test de création individuelle...")
        result = service.create_counting_detail(test_data)
        print(f"✅ Résultat: {json.dumps(result, indent=2, default=str)}")
        
        # Test de validation en lot
        print(f"\n✅ Test de validation en lot...")
        validation_result = service.validate_counting_details_batch([test_data])
        print(f"✅ Résultat validation: {json.dumps(validation_result, indent=2, default=str)}")
        
        print(f"\n🎉 Service simplifié fonctionne correctement !")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service()

