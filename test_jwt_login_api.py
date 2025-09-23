#!/usr/bin/env python
"""
Script de test pour la nouvelle API JWT de login.
"""

import os
import sys
import django
import requests
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def test_jwt_login_api():
    """
    Test de la nouvelle API JWT de login.
    """
    
    print("🧪 Test de la nouvelle API JWT de login")
    print("=" * 50)
    
    # URL de l'API
    base_url = "http://localhost:8000"
    api_url = f"{base_url}/api/mobile/auth/jwt-login/"
    
    print(f"URL de l'API: {api_url}")
    print()
    
    # Données de test
    test_data = {
        "username": "admin",  # Remplacez par un utilisateur valide de votre base
        "password": "admin"   # Remplacez par le mot de passe correct
    }
    
    print(f"Données de test: {test_data}")
    print()
    
    try:
        # Test de l'API
        print("🔍 Test de l'API JWT de login...")
        
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("✅ Succès ! Réponse reçue:")
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # Vérification du format de réponse
            print("\n🔍 Vérification du format de réponse...")
            
            required_fields = ['success', 'access', 'refresh', 'user']
            user_fields = ['user_id', 'nom', 'prenom']
            
            # Vérifier les champs principaux
            for field in required_fields:
                if field in response_data:
                    print(f"✅ Champ '{field}' présent")
                else:
                    print(f"❌ Champ '{field}' manquant")
            
            # Vérifier les champs utilisateur
            if 'user' in response_data:
                for field in user_fields:
                    if field in response_data['user']:
                        print(f"✅ Champ utilisateur '{field}' présent")
                    else:
                        print(f"❌ Champ utilisateur '{field}' manquant")
            
            # Vérifier le type des tokens
            if isinstance(response_data.get('access'), str) and len(response_data['access']) > 0:
                print("✅ Token d'accès valide")
            else:
                print("❌ Token d'accès invalide")
                
            if isinstance(response_data.get('refresh'), str) and len(response_data['refresh']) > 0:
                print("✅ Token de rafraîchissement valide")
            else:
                print("❌ Token de rafraîchissement invalide")
                
        else:
            print("❌ Erreur ! Réponse reçue:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"Texte de réponse: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion. Assurez-vous que le serveur Django est démarré.")
        print("   Commande: python manage.py runserver")
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()

def test_jwt_login_api_with_invalid_credentials():
    """
    Test de l'API avec des identifiants invalides.
    """
    
    print("\n" + "=" * 50)
    print("🧪 Test de l'API JWT avec des identifiants invalides")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    api_url = f"{base_url}/api/mobile/auth/jwt-login/"
    
    # Données invalides
    invalid_data = {
        "username": "utilisateur_inexistant",
        "password": "mot_de_passe_incorrect"
    }
    
    print(f"Données invalides: {invalid_data}")
    print()
    
    try:
        response = requests.post(
            api_url,
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Comportement correct - Erreur 400 pour identifiants invalides")
            try:
                error_data = response.json()
                print("Réponse d'erreur:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"Texte de réponse: {response.text}")
        else:
            print(f"❌ Comportement inattendu - Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de l'API JWT de login...")
    print()
    
    # Test principal
    test_jwt_login_api()
    
    # Test avec identifiants invalides
    test_jwt_login_api_with_invalid_credentials()
    
    print("\n🏁 Tests terminés.")
    print("\n💡 Pour tester manuellement:")
    print("   curl -X POST http://localhost:8000/api/mobile/auth/jwt-login/ \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"username\": \"admin\", \"password\": \"admin\"}'")
