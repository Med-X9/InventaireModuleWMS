#!/usr/bin/env python
"""
Test de la gestion des erreurs dans JobAutoValidateView
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

from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

def get_auth_headers():
    """Obtenir les headers d'authentification"""
    User = get_user_model()
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', password='testpass')

    access_token = AccessToken.for_user(user)
    return {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

def test_error_cases():
    """Test de différents cas d'erreur"""
    client = Client()
    headers = get_auth_headers()

    print("=== Test de gestion des erreurs ===")

    # Test 1: ID d'inventaire négatif (passe la regex mais échoue dans la validation)
    print("\n1. Test ID d'inventaire négatif...")
    url = "/web/api/inventory/0/warehouse/15/jobs/validate-all/"
    response = client.post(url, **headers)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response (text): {response.content.decode()}")

    # Test 2: ID de warehouse négatif
    print("\n2. Test ID de warehouse négatif...")
    url = "/web/api/inventory/52/warehouse/0/jobs/validate-all/"
    response = client.post(url, **headers)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response (text): {response.content.decode()}")

    # Test 3: Inventaire qui n'existe pas
    print("\n3. Test inventaire inexistant...")
    url = "/web/api/inventory/99999/warehouse/15/jobs/validate-all/"
    response = client.post(url, **headers)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response (text): {response.content.decode()}")

    # Test 4: Cas normal (devrait fonctionner)
    print("\n4. Test cas normal...")
    url = "/web/api/inventory/52/warehouse/15/jobs/validate-all/"
    response = client.post(url, **headers)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response (text): {response.content.decode()}")

    # Test 5: Sans authentification
    print("\n5. Test sans authentification...")
    client_no_auth = Client()
    url = "/web/api/inventory/52/warehouse/15/jobs/validate-all/"
    response = client_no_auth.post(url)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response (text): {response.content.decode()}")

if __name__ == "__main__":
    test_error_cases()
    print("\n=== Tests terminés ===")