#!/usr/bin/env python
"""
Debug script pour vérifier les données dans la base de données
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

from apps.inventory.models import Inventory, Warehouse
from apps.inventory.services.job_service import JobService

def debug_database():
    """Debug des données dans la base de données"""
    print("=== Debug base de données ===")

    # Vérifier l'inventaire 52
    try:
        inventory = Inventory.objects.get(id=52)
        print(f"OK: Inventaire 52 trouve: {inventory.reference}")
        print(f"   - Statut: {inventory.status}")
        print(f"   - Date de creation: {inventory.created_at}")
    except Inventory.DoesNotExist:
        print("ERREUR: Inventaire 52 non trouve")
        return

    # Vérifier le warehouse 15
    try:
        warehouse = Warehouse.objects.get(id=15)
        print(f"OK: Warehouse 15 trouve: {warehouse.warehouse_name}")
        print(f"   - Code: {warehouse.reference}")
        print(f"   - Type: {warehouse.warehouse_type}")
        print(f"   - Statut: {warehouse.status}")
    except Warehouse.DoesNotExist:
        print("ERREUR: Warehouse 15 non trouve")
        return

    # Vérifier les jobs en attente
    print("\n=== Vérification des jobs ===")
    job_service = JobService()
    try:
        pending_jobs = job_service.repository.get_pending_jobs_by_inventory_and_warehouse(52, 15)
        print(f"Jobs en attente trouvés: {len(pending_jobs)}")

        for job in pending_jobs:
            print(f"  - Job {job.id}: {job.reference} (statut: {job.status})")

        if not pending_jobs:
            print("INFO: Aucun job en attente - c'est normal si la validation automatique retourne ce message")

        # Tester la méthode de validation directement
        print("\n=== Test de validation directe ===")
        if pending_jobs:
            job_ids = [job.id for job in pending_jobs]
            print(f"Tentative de validation des jobs: {job_ids}")
            result = job_service.validate_jobs(job_ids)
            print(f"Resultat: {result}")
        else:
            print("Pas de jobs a valider")

    except Exception as e:
        print(f"ERREUR: Erreur lors de la verification des jobs: {str(e)}")
        import traceback
        traceback.print_exc()

    # Vérifier les comptages pour cet inventaire
    print("\n=== Verification des comptages ===")
    try:
        countings = job_service.repository.get_countings_by_inventory(inventory)
        print(f"Nombre de comptages pour l'inventaire: {len(countings)}")

        for counting in countings:
            print(f"  - Comptage {counting.id}: {counting.reference} (ordre: {counting.order})")

        if len(countings) < 2:
            print("ATTENTION: Moins de 2 comptages - cela peut poser probleme pour la validation")

    except Exception as e:
        print(f"ERREUR: Erreur lors de la verification des comptages: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database()
