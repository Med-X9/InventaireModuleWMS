#!/usr/bin/env python
"""
Debug étape par étape pour identifier l'erreur exacte
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

from apps.inventory.services.job_service import JobService
from apps.inventory.repositories.job_repository import JobRepository

def debug_step_by_step():
    """Debug étape par étape"""
    print("=== Debug étape par étape ===")

    inventory_id = 52
    warehouse_id = 15

    try:
        print("Étape 1: Création du service")
        job_service = JobService()
        print("OK: Service cree")

        print("Etape 2: Verification inventaire")
        inventory = job_service.repository.get_inventory_by_id(inventory_id)
        if not inventory:
            print("ERREUR: Inventaire non trouve")
            return
        print(f"OK: Inventaire trouve: {inventory.reference}")

        print("Etape 3: Verification warehouse")
        warehouse = job_service.repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            print("ERREUR: Warehouse non trouve")
            return
        print(f"OK: Warehouse trouve: {warehouse.warehouse_name}")

        print("Etape 4: Recuperation jobs en attente")
        pending_jobs = job_service.repository.get_pending_jobs_by_inventory_and_warehouse(inventory_id, warehouse_id)
        print(f"OK: Jobs en attente: {len(pending_jobs)}")

        if not pending_jobs:
            print("INFO: Pas de jobs a valider - devrait retourner succes")
            result = {
                'success': True,
                'validated_jobs_count': 0,
                'validated_jobs': [],
                'message': 'Aucun job en attente a valider'
            }
            print(f"Resultat attendu: {result}")
            return

        print("Etape 5: Validation des jobs")
        job_ids = [job.id for job in pending_jobs]
        print(f"Job IDs a valider: {job_ids}")

        result = job_service.validate_jobs(job_ids)
        print(f"OK: Validation reussie: {result}")

    except Exception as e:
        print(f"ERREUR a l'etape actuelle: {str(e)}")
        print(f"Type d'erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_step_by_step()
