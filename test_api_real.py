#!/usr/bin/env python
"""
Test réel de l'API pour reproduire l'erreur
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
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

def test_real_api():
    """Test de l'API réelle"""
    print("=== Test API réel ===")

    # Créer un utilisateur de test
    User = get_user_model()
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', password='testpass')

    # Créer un token JWT
    access_token = AccessToken.for_user(user)

    # URL de l'API
    url = 'http://127.0.0.1:8000/web/api/inventory/52/warehouse/15/jobs/validate-all/'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    print(f"URL: {url}")
    print(f"Token: {str(access_token)[:20]}...")

    try:
        response = requests.post(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("SUCCES: L'API fonctionne")
        else:
            print("ERREUR: Probleme avec l'API")

    except requests.exceptions.RequestException as e:
        print(f"ERREUR REQUETE: {str(e)}")

if __name__ == "__main__":
    test_real_api()
