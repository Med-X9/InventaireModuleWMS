#!/usr/bin/env python3
"""
Test simple de l'API des assignments et jobs
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/mobile"

def test_assignment_api():
    """Test de l'API des assignments"""
    
    print("🧪 Test de l'API des assignments et jobs")
    print("=" * 50)
    
    # 1. Test de connexion
    print("\n1. Test de connexion...")
    login_data = {
        "username": "mobile_user",  # Remplacer par un utilisateur valide
        "password": "password123"    # Remplacer par le mot de passe valide
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            headers = {'Authorization': f'Bearer {token}'}
            print("✅ Connexion réussie")
        else:
            print(f"❌ Échec de la connexion: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # 2. Test de mise à jour des statuts
    print("\n2. Test de mise à jour des statuts d'un assignment et de son job...")
    user_id = 1      # Remplacer par un ID d'utilisateur valide
    assignment_id = 1  # Remplacer par un ID d'assignment valide
    
    try:
        update_data = {
            "new_status": "ENTAME"
        }
        
        response = requests.post(
            f"{API_BASE}/user/{user_id}/assignment/{assignment_id}/status/",
            json=update_data,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Statuts mis à jour avec succès")
            print(f"   Assignment: {data['data']['assignment']['reference']} -> {data['data']['assignment']['status']}")
            print(f"   Job: {data['data']['job']['reference']} -> {data['data']['job']['status']}")
            print(f"   Message: {data['data']['message']}")
        elif response.status_code == 404:
            print("⚠️ Assignment ou job non trouvé")
        elif response.status_code == 403:
            print("⚠️ Utilisateur non autorisé pour cet assignment")
        elif response.status_code == 400:
            print("⚠️ Transition de statut non autorisée")
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Tests terminés")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de l'API des assignments")
    test_assignment_api()
    print("\n✨ Tests terminés!")
