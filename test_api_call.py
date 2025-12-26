#!/usr/bin/env python
"""
Test de l'appel API pour simuler l'erreur
"""
import os
import sys
import django
from django.test import Client
from django.urls import reverse

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

def test_api_call():
    """Test de l'appel API"""
    print("Test de l'appel API pour auto-validate...")

    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import AccessToken
    User = get_user_model()

    # Créer un utilisateur de test si nécessaire
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', password='testpass')

    # Créer un token JWT
    access_token = AccessToken.for_user(user)

    client = Client()

    # URL de l'endpoint
    url = reverse('jobs-validate-all', kwargs={'inventory_id': 52, 'warehouse_id': 15})
    print(f"URL: {url}")

    try:
        # Faire l'appel POST avec le token JWT
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
        response = client.post(url, content_type='application/json', **headers)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.content.decode()}")

        if response.status_code == 200:
            print("SUCCES: L'appel API a fonctionne")
        else:
            print("ERREUR: Probleme avec l'appel API")

    except Exception as e:
        print(f"ERREUR lors de l'appel: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_call()
