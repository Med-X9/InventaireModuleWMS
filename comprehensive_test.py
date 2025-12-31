#!/usr/bin/env python
"""
Test complet de tous les scénarios d'erreur possibles
"""
import requests
import json
import sys
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.append(os.path.dirname(__file__))

# Ajouter testserver aux ALLOWED_HOSTS
from django.conf import settings
if '127.0.0.1' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('127.0.0.1')

django.setup()

from apps.users.models import UserApp as User
from rest_framework_simplejwt.tokens import AccessToken

def test_scenario(name, inventory_id, warehouse_id, expected_contains=None):
    """Test un scénario spécifique"""
    print(f"\n=== Test: {name} ===")
    print(f"Inventory ID: {inventory_id}, Warehouse ID: {warehouse_id}")

    # Créer un token
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', email='test@example.com')

    token = AccessToken.for_user(user)

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    url = f'http://127.0.0.1:8000/web/api/inventory/{inventory_id}/warehouse/{warehouse_id}/jobs/validate-all/'

    try:
        response = requests.post(url, headers=headers, timeout=10)

        print(f"Status: {response.status_code}")

        try:
            data = response.json()
            message = data.get('message', '')
            print(f"Message: {message}")

            if expected_contains and expected_contains in message:
                print("✅ RÉSULTAT ATTENDU")
                return True
            elif "Une erreur inattendue s'est produite lors de la validation automatique" in message:
                print("❌ MESSAGE GÉNÉRIQUE (PROBLÈME)")
                return False
            else:
                print(f"⚠️  MESSAGE DIFFÉRENT: {message}")
                return False

        except json.JSONDecodeError:
            print(f"Response text: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return False

def main():
    """Test complet"""
    print("TEST COMPREHENSIF DE L'ENDPOINT JobAutoValidateView")
    print("=" * 60)

    scenarios = [
        ("IDs inexistants", 99999, 99999, "non trouvé"),
        ("Inventory inexistant, warehouse existant?", 99999, 1, "non trouvé"),
        ("Inventory existant?, warehouse inexistant", 1, 99999, "non trouvé"),
        ("IDs très grands", 999999, 999999, "non trouvé"),
        ("IDs négatifs", -1, -1, "invalide"),
        ("IDs zéro", 0, 0, "invalide"),
    ]

    results = []

    for name, inv_id, wh_id, expected in scenarios:
        result = test_scenario(name, inv_id, wh_id, expected)
        results.append((name, result))

    print(f"\n{'='*60}")
    print("RÉSUMÉ DES TESTS:")

    all_good = True
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
        if not result:
            all_good = False

    print(f"\nCONCLUSION: {'TOUS LES TESTS RÉUSSIS' if all_good else 'PROBLÈMES DÉTECTÉS'}")

    if not all_good:
        print("\nSi vous voyez des messages génériques, vérifiez:")
        print("1. Serveur Django redémarré")
        print("2. Bonne URL: /web/api/inventory/.../warehouse/.../jobs/validate-all/")
        print("3. Token JWT valide")
        print("4. Pas de cache Postman")

if __name__ == '__main__':
    main()

