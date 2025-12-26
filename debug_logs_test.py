#!/usr/bin/env python
"""
Test avec logs forcés pour voir l'erreur exacte
"""
import os
import sys
import django
import logging

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.append(os.path.dirname(__file__))

# Ajouter testserver aux ALLOWED_HOSTS
from django.conf import settings
if '127.0.0.1' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('127.0.0.1')

django.setup()

from apps.inventory.services.job_service import JobService

def test_service_directly():
    """Test direct du service pour voir l'erreur exacte"""

    # Configuration du logging pour voir les erreurs
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('debug.log')
        ]
    )

    logger = logging.getLogger(__name__)

    print("=== TEST DIRECT DU SERVICE ===")
    print("Test de auto_validate_jobs(52, 15)")

    try:
        service = JobService()
        result = service.auto_validate_jobs(52, 15)

        print("SUCCES - Pas d'erreur")
        print(f"Resultat: {result}")

    except Exception as e:
        print(f"ERREUR CAPTUREE: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

        # Logger l'erreur
        logger.error(f"Erreur dans test direct: {e}", exc_info=True)

if __name__ == '__main__':
    test_service_directly()
