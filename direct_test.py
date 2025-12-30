#!/usr/bin/env python
"""
Test direct de l'endpoint avec requests
"""
import requests
import json
import sys
import os
import django

# Configuration Django pour créer un token
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.append(os.path.dirname(__file__))
django.setup()

from apps.users.models import UserApp as User
from rest_framework_simplejwt.tokens import AccessToken

def test_direct_api_call():
    """Test direct avec requests"""

    # Créer un token
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', email='test@example.com')

    token = AccessToken.for_user(user)

    # Headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # URL de test
    base_url = 'http://127.0.0.1:8000'
    endpoint = '/web/api/inventory/99999/warehouse/99999/jobs/validate-all/'

    print(f"=== Test direct de l'endpoint ===")
    print(f"URL: {base_url}{endpoint}")
    print(f"Token: {str(token)[:20]}...")

    try:
        response = requests.post(f"{base_url}{endpoint}", headers=headers, timeout=10)

        print(f"Status code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        try:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            # Vérifier le message
            message = response_data.get('message', '')
            if "Une erreur inattendue s'est produite lors de la validation automatique" in message:
                print("❌ ÉCHEC: Message générique trouvé")
                return False
            elif "non trouvé" in message or "non trouv" in message:
                print("✅ SUCCÈS: Message spécifique trouvé")
                return True
            else:
                print(f"⚠️  Message différent: {message}")
                return False

        except json.JSONDecodeError:
            print(f"Response text: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ ERREUR: Impossible de se connecter au serveur")
        print("   Assurez-vous que le serveur Django est démarré: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

if __name__ == '__main__':
    success = test_direct_api_call()
    print(f"\n=== RÉSULTAT: {'SUCCÈS' if success else 'ÉCHEC'} ===")
    sys.exit(0 if success else 1)

