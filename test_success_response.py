#!/usr/bin/env python
"""
Test de la fonction success_response
"""
import os
import sys
import django

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

from apps.inventory.utils.response_utils import success_response

def test_success_response():
    """Test de la fonction success_response"""
    print("=== Test success_response ===")

    try:
        # Test avec les mêmes données que celles retournées par le service
        result = {
            'success': True,
            'validated_jobs_count': 0,
            'validated_jobs': [],
            'message': 'Aucun job en attente à valider'
        }

        print(f"Test 1: Appel success_response avec result: {result}")
        response = success_response(
            data=result,
            message=result['message']
        )
        print(f"OK: success_response retourne: {response}")
        print(f"Status: {response.status_code}")
        print(f"Data: {response.data}")

    except Exception as e:
        print(f"ERREUR dans success_response: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_success_response()
