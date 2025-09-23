#!/usr/bin/env python3
"""
Déboguer la connexion pour voir la structure de la réponse
"""

import requests
import json

def debug_login():
    """Déboguer la connexion"""
    
    print("🔍 Débogage de la connexion")
    print("=" * 40)
    
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post('http://localhost:8000/api/auth/login/', json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                print(f"\n📋 Réponse JSON:")
                print(json.dumps(response_json, indent=2))
                
                # Vérifier tous les champs possibles
                print(f"\n🔍 Champs disponibles:")
                for key, value in response_json.items():
                    print(f"   {key}: {value} (type: {type(value)})")
                    
            except Exception as e:
                print(f"❌ Erreur parsing JSON: {e}")
        else:
            print(f"❌ Échec de la connexion")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    debug_login()
