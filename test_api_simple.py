#!/usr/bin/env python3
"""
Test simple de l'API Assignment sans body
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/mobile/api"
AUTH_BASE = f"{BASE_URL}/api/auth"

def test_assignment_api():
    """Test de l'API des assignments"""
    
    print("🧪 Test de l'API Assignment (statut automatique ENTAME)")
    print("=" * 50)
    
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
    
    # 2. Test de l'API assignment (sans body)
    print("\n2. Test de l'API assignment (statut automatique ENTAME)...")
    
    user_id = 1
    assignment_id = 1
    
    try:
        # Pas de body, juste les headers avec le token
        response = requests.post(
            f"{API_BASE}/user/{user_id}/assignment/{assignment_id}/status/",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API fonctionne ! Statut mis à jour vers ENTAME")
        else:
            print("❌ Erreur de l'API")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Tests terminés")

if __name__ == "__main__":
    test_assignment_api()
