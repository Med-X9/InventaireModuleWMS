#!/usr/bin/env python
"""
Script de test pour l'endpoint JobAutoValidateView
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.append(os.path.dirname(__file__))

# Ajouter testserver aux ALLOWED_HOSTS pour les tests
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

django.setup()

from django.test import Client
from apps.users.models import UserApp as User
from apps.inventory.models import Inventory, Warehouse, Job
from rest_framework_simplejwt.tokens import AccessToken

def test_auto_validate_endpoint():
    """Test de l'endpoint de validation automatique des jobs"""

    # Créer un client de test
    client = Client()

    # Créer un utilisateur de test s'il n'existe pas
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )

    # Créer un token JWT pour l'utilisateur
    token = AccessToken.for_user(user)
    auth_header = f'Bearer {token}'

    # Tester avec des IDs qui n'existent probablement pas pour voir le message d'erreur
    inventory_id = 999
    warehouse_id = 999

    url = f'/web/api/inventory/{inventory_id}/warehouse/{warehouse_id}/jobs/validate-all/'

    print(f"Test de l'URL: {url}")
    print("Envoi d'une requête POST...")

    response = client.post(url, HTTP_HOST='localhost', HTTP_AUTHORIZATION=auth_header)

    print(f"Status code: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
    try:
        print(f"Response JSON: {response.json()}")
    except ValueError:
        print(f"Response content: {response.content.decode('utf-8')}")

    return response

if __name__ == '__main__':
    try:
        response = test_auto_validate_endpoint()
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
