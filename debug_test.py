#!/usr/bin/env python
"""
Test de débogage avec logs en temps réel
"""
import requests
import json
import sys
import os
import django
import logging
import time

# Configuration Django pour créer un token et logger
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.append(os.path.dirname(__file__))

# Configuration du logging pour voir les messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

django.setup()

from apps.users.models import UserApp as User
from rest_framework_simplejwt.tokens import AccessToken

def test_with_detailed_logging():
    """Test avec logging détaillé"""

    # Créer un token
    try:
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        token = AccessToken.for_user(user)
        print(f"Token créé pour user: {user.username}")
    except Exception as e:
        print(f"Erreur création token: {e}")
        return False

    # Headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # URL de test
    base_url = 'http://127.0.0.1:8000'
    endpoint = '/web/api/inventory/99999/warehouse/99999/jobs/validate-all/'

    print(f"\n=== Test de débogage ===")
    print(f"URL: {base_url}{endpoint}")
    print(f"Token: {str(token)[:20]}...")

    # Logger les détails de la requête
    logger = logging.getLogger('test_debug')
    logger.info("Début du test de validation automatique")
    logger.info(f"Endpoint: {endpoint}")
    logger.info(f"User: {user.username} (ID: {user.id})")

    try:
        print("Envoi de la requête...")
        start_time = time.time()

        response = requests.post(f"{base_url}{endpoint}", headers=headers, timeout=10)

        end_time = time.time()
        duration = end_time - start_time

        print(f"Requête terminée en {duration:.2f}s")
        print(f"Status code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")

        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response time: {duration:.2f}s")

        # Afficher la réponse
        try:
            response_data = response.json()
            print(f"\nResponse JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))

            # Analyse du message
            message = response_data.get('message', '')
            errors = response_data.get('errors', [])

            logger.info(f"Response message: {message}")
            logger.info(f"Response errors: {errors}")

            if "Une erreur inattendue s'est produite lors de la validation automatique" in message:
                print("\n❌ PROBLÈME: Message générique trouvé - mes modifications ne sont pas appliquées!")
                logger.error("Message générique détecté - vérification nécessaire")
                return False
            elif "non trouvé" in message or "non trouv" in message:
                print("\n✅ SUCCÈS: Message spécifique trouvé - modifications actives!")
                logger.info("Message spécifique détecté - modifications fonctionnelles")
                return True
            else:
                print(f"\n⚠️  Message différent: {message}")
                logger.warning(f"Message inattendu: {message}")
                return False

        except json.JSONDecodeError as e:
            print(f"Erreur parsing JSON: {e}")
            print(f"Response text: {response.text[:500]}...")
            logger.error(f"JSON decode error: {e}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erreur de connexion: {e}")
        print("Le serveur Django n'est peut-être pas démarré")
        logger.error(f"Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = test_with_detailed_logging()
    print(f"\n=== RÉSULTAT FINAL: {'SUCCÈS' if success else 'ÉCHEC'} ===")
    sys.exit(0 if success else 1)
