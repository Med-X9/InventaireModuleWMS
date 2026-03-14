#!/usr/bin/env python
"""
Test rapide pour vérifier les modifications d'erreur
"""
import os
import sys
import django
import requests

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.append(os.path.dirname(__file__))

# Ajouter testserver aux ALLOWED_HOSTS
from django.conf import settings
if '127.0.0.1' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('127.0.0.1')

django.setup()

from django.test import Client
from apps.users.models import UserApp as User
from rest_framework_simplejwt.tokens import AccessToken

def test_endpoint():
    """Test rapide de l'endpoint avec les modifications"""

    client = Client()

    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )

    # Créer un token JWT
    token = AccessToken.for_user(user)
    auth_header = f'Bearer {token}'

    # URL qui déclenche une erreur (IDs inexistants)
    url = '/web/api/inventory/99999/warehouse/99999/jobs/validate-all/'

    print("=== Test de l'endpoint JobAutoValidateView ===")
    response = client.post(url, HTTP_HOST='127.0.0.1', HTTP_AUTHORIZATION=auth_header)

    print(f"Status code: {response.status_code}")
    response_data = response.json()
    print(f"Response: {response_data}")

    message = response_data.get('message', '')
    errors = response_data.get('errors', [])

    # Vérifier que ce n'est pas le message générique
    if "Une erreur inattendue s'est produite lors de la validation automatique" in message:
        print("❌ ÉCHEC: Message générique toujours présent")
        return False
    elif "Inventaire avec l'ID 99999 non trouvé" in message:
        print("✅ SUCCÈS: Message d'erreur spécifique trouvé")
        return True
    else:
        print(f"⚠️  INATTENDU: Message différent: {message}")
        return False

if __name__ == '__main__':
    try:
        success = test_endpoint()
        print(f"\n=== RÉSULTAT: {'SUCCÈS' if success else 'ÉCHEC'} ===")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



