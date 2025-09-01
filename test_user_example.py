#!/usr/bin/env python3
"""
Test avec l'exemple exact de l'utilisateur
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/mobile/api"
AUTH_BASE = f"{BASE_URL}/api/auth"  # Correction de l'URL d'auth

def test_user_example():
    """Test avec l'exemple exact de l'utilisateur"""
    
    print("🧪 Test avec l'exemple exact de l'utilisateur")
    print("=" * 60)
    
    # 1. Test de connexion
    print("\n1. Test de connexion...")
    
    login_data = {
        "username": "admin",  # Remplacez par un utilisateur valide
        "password": "admin"   # Remplacez par le mot de passe valide
    }
    
    try:
        response = requests.post(f"{AUTH_BASE}/login/", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            print("✅ Connexion réussie")
        else:
            print(f"❌ Échec de la connexion: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # 2. Test avec l'exemple exact de l'utilisateur
    print("\n2. Test avec l'exemple exact de l'utilisateur...")
    
    user_data = {
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
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=user_data,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            response_data = response.json()
            error_msg = response_data.get('error', '')
            error_type = response_data.get('error_type', '')
            
            print(f"\n📋 Analyse de l'erreur:")
            print(f"   Type: {error_type}")
            print(f"   Message: {error_msg}")
            
            if "null n'est pas accepté" in error_msg:
                print("✅ Validation null fonctionne - le produit nécessite un n_lot valide")
            elif "déjà utilisé" in error_msg:
                print("✅ Validation numéro de série dupliqué fonctionne")
            else:
                print("❌ Type d'erreur inattendu")
                
        elif response.status_code == 201:
            print("✅ Création réussie (produit n'a pas n_lot=True)")
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_user_example()
