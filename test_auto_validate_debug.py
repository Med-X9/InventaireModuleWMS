#!/usr/bin/env python
"""
Script de debug pour l'erreur de validation automatique des jobs
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.append(os.path.dirname(__file__))

# Ajouter testserver aux ALLOWED_HOSTS
from django.conf import settings
if '127.0.0.1' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('127.0.0.1')

django.setup()

from apps.inventory.services.job_service import JobService
from apps.inventory.repositories.job_repository import JobRepository
from apps.inventory.exceptions.job_exceptions import JobCreationError

def test_auto_validate():
    """Test de la méthode auto_validate_jobs"""
    print("=== Test de la méthode auto_validate_jobs ===")

    # Paramètres de test basés sur l'URL de l'utilisateur
    inventory_id = 52
    warehouse_id = 15

    try:
        # Test du service directement
        job_service = JobService()
        print(f"Test avec inventory_id={inventory_id}, warehouse_id={warehouse_id}")

        # Vérifier que l'inventaire existe
        inventory = job_service.repository.get_inventory_by_id(inventory_id)
        if not inventory:
            print(f"ERREUR: Inventaire {inventory_id} non trouve")
            return
        print(f"OK: Inventaire trouve: {inventory.reference}")

        # Vérifier que le warehouse existe
        warehouse = job_service.repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            print(f"ERREUR: Warehouse {warehouse_id} non trouve")
            return
        print(f"OK: Warehouse trouve: {warehouse.warehouse_name}")

        # Récupérer les jobs en attente
        pending_jobs = job_service.repository.get_pending_jobs_by_inventory_and_warehouse(inventory_id, warehouse_id)
        print(f"INFO: Jobs en attente trouves: {len(pending_jobs)}")
        for job in pending_jobs:
            print(f"  - Job {job.id}: {job.reference} (statut: {job.status})")

        if not pending_jobs:
            print("INFO: Aucun job en attente a valider")
            return

        # Tester la validation
        print("\nINFO: Test de validation des jobs...")
        result = job_service.validate_jobs([job.id for job in pending_jobs])

        print("SUCCES: Validation reussie:")
        print(f"  - Jobs valides: {result['validated_jobs_count']}")
        print(f"  - Message: {result['message']}")

    except JobCreationError as e:
        print(f"ERREUR METIER: {str(e)}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"ERREUR INATTENDUE: {str(e)}")
        print(f"Type d'erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()

def test_repository_methods():
    """Test des méthodes du repository"""
    print("\n=== Test des méthodes du repository ===")

    repository = JobRepository()
    inventory_id = 52
    warehouse_id = 15

    try:
        # Test de récupération des jobs
        jobs = repository.get_pending_jobs_by_inventory_and_warehouse(inventory_id, warehouse_id)
        print(f"Jobs récupérés: {len(jobs)}")

        for job in jobs:
            print(f"  - Job {job.id}: {job.reference}")
            # Vérifier les relations
            print(f"    - Inventory: {job.inventory.reference if job.inventory else 'None'}")
            print(f"    - Warehouse: {job.warehouse.warehouse_name if job.warehouse else 'None'}")

    except Exception as e:
        print(f"ERREUR REPOSITORY: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Démarrage du debug de l'auto-validation des jobs...")
    test_repository_methods()
    test_auto_validate()
    print("Debug terminé.")
