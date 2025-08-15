#!/usr/bin/env python3
"""
Test direct de l'API sans authentification
"""

import requests
import json

def test_api_direct():
    """Test direct de l'API"""
    
    print("🧪 Test direct de l'API CountingDetail")
    print("=" * 50)
    
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
    
    print("📤 Envoi des données:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(
            'http://localhost:8000/mobile/api/counting-detail/',
            json=data
        )
        
        print(f"\n📥 Réponse reçue:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 400:
            try:
                response_data = response.json()
                error_msg = response_data.get('error', '')
                error_type = response_data.get('error_type', '')
                
                print(f"\n📋 Analyse de l'erreur:")
                print(f"   Type: {error_type}")
                print(f"   Message: {error_msg}")
                
                if "null n'est pas accepté" in error_msg:
                    print("✅ SUCCÈS: Validation null fonctionne - le produit nécessite un n_lot valide")
                elif "déjà utilisé" in error_msg:
                    print("✅ SUCCÈS: Validation numéro de série dupliqué fonctionne")
                else:
                    print("❌ Type d'erreur inattendu")
                    
            except:
                print("❌ Impossible de parser la réponse JSON")
                
        elif response.status_code == 201:
            print("✅ SUCCÈS: Création réussie (produit n'a pas n_lot=True)")
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

if __name__ == "__main__":
    test_api_direct()
