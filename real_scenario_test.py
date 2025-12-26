#!/usr/bin/env python
"""
Test du scénario réel : inventory existant + warehouse existant
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
from apps.inventory.models import Inventory, Warehouse
from rest_framework_simplejwt.tokens import AccessToken

def test_real_scenario():
    """Test avec des vrais IDs d'inventory et warehouse"""

    # Vérifier ce qui existe en base
    print("=== VÉRIFICATION DES DONNÉES EN BASE ===")

    try:
        # Chercher un inventory qui existe
        inventories = Inventory.objects.all()[:3]
        print(f"Inventories trouvés: {[(inv.id, inv.reference) for inv in inventories]}")

        # Chercher des warehouses qui existent
        warehouses = Warehouse.objects.all()[:3]
        print(f"Warehouses trouvés: {[(wh.id, wh.name) for wh in warehouses]}")

        if not inventories:
            print("❌ Aucun inventory trouvé en base")
            return

        if not warehouses:
            print("❌ Aucun warehouse trouvé en base")
            return

        # Utiliser les vrais IDs
        inventory_id = inventories[0].id
        warehouse_id = warehouses[0].id

        print(f"\n=== TEST AVEC IDS RÉELS ===")
        print(f"Inventory ID: {inventory_id} ({inventories[0].reference})")
        print(f"Warehouse ID: {warehouse_id} ({warehouses[0].name})")

    except Exception as e:
        print(f"Erreur d'accès à la base: {e}")
        # Utiliser des IDs par défaut si la base n'est pas accessible
        inventory_id = 52
        warehouse_id = 15
        print(f"Utilisation d'IDs par défaut: {inventory_id}/{warehouse_id}")

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

    print(f"\nURL: {url}")

    try:
        response = requests.post(url, headers=headers, timeout=10)

        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")

        try:
            data = response.json()
            print(f"\nResponse JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            message = data.get('message', '')
            errors = data.get('errors', [])

            print("\n=== ANALYSE ===")
            if "Une erreur inattendue s'est produite lors de la validation automatique" in message:
                print("❌ MESSAGE GÉNÉRIQUE - Problème non résolu")
                return False
            elif "non trouvé" in message:
                print("✅ Message spécifique (ressource non trouvée)")
                return True
            elif "jobs validés" in message:
                print("✅ SUCCÈS - Jobs validés")
                return True
            elif "Aucun job" in message:
                print("ℹ️  INFO - Aucun job à valider")
                return True
            else:
                print(f"⚠️  Message différent: {message}")
                return False

        except json.JSONDecodeError as e:
            print(f"Erreur parsing JSON: {e}")
            print(f"Response text: {response.text[:500]}...")
            return False

    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return False

if __name__ == '__main__':
    success = test_real_scenario()
    print(f"\n=== RÉSULTAT: {'SUCCÈS' if success else 'ÉCHEC'} ===")

    if not success:
        print("\nINSTRUCTIONS DE DÉBOGAGE:")
        print("1. Vérifiez les logs Django pour l'erreur exacte")
        print("2. Assurez-vous que le serveur est redémarré")
        print("3. Vérifiez qu'il n'y a pas de cache")
