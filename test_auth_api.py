#!/usr/bin/env python3
"""
Script de test pour l'API d'authentification mobile
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/mobile/api/auth/login/"

def test_login(username, password):
    """Test de connexion avec les identifiants fournis"""
    print(f"🔐 Test de connexion avec: {username}")
    
    # Données de connexion
    data = {
        "username": username,
        "password": password
    }
    
    try:
        # Requête POST
        response = requests.post(
            LOGIN_URL,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        # Réponse
        try:
            response_data = response.json()
            print(f"📄 Response JSON: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"📄 Response Text: {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur")
        print("💡 Assurez-vous que le serveur Django est démarré: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_with_different_credentials():
    """Test avec différents identifiants"""
    test_cases = [
        ("mobile", "user1234"),
        ("admin", "admin"),
        ("test", "test"),
        ("user", "password"),
    ]
    
    print("🧪 Test de différents identifiants:")
    print("=" * 50)
    
    for username, password in test_cases:
        print(f"\n🔍 Test: {username} / {password}")
        success = test_login(username, password)
        if success:
            print("✅ Connexion réussie!")
            break
        else:
            print("❌ Connexion échouée")
        print("-" * 30)

if __name__ == "__main__":
    print("🚀 Test de l'API d'authentification mobile")
    print("=" * 50)
    
    # Test avec les identifiants fournis
    test_login("mobile", "user1234")
    
    print("\n" + "=" * 50)
    
    # Test avec d'autres identifiants
    test_with_different_credentials()
