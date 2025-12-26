#!/usr/bin/env python
"""
Test de la logique "tous ou rien" pour la validation automatique des jobs
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

def test_all_or_nothing_logic():
    """Test de la logique tous ou rien"""
    print("=== Test logique 'tous ou rien' ===")

    # Utiliser les IDs de l'exemple de l'utilisateur
    inventory_id = 52  # À adapter selon les vrais IDs
    warehouse_id = 15  # À adapter selon les vrais IDs

    try:
        service = JobService()
        repository = JobRepository()

        print(f"Test avec inventory_id: {inventory_id}, warehouse_id: {warehouse_id}")

        # Récupérer tous les jobs
        all_jobs = repository.get_jobs_by_inventory_and_warehouse(inventory_id, warehouse_id)
        print(f"Total des jobs trouvés: {len(all_jobs)}")

        # Afficher le statut de chaque job
        pending_jobs = []
        non_pending_jobs = []

        for job in all_jobs:
            print(f"  - Job {job.id} ({job.reference}): statut = '{job.status}'")
            if job.status == 'EN ATTENTE':
                pending_jobs.append(job)
            else:
                non_pending_jobs.append(job)

        print(f"\nRésumé:")
        print(f"  - Jobs en attente: {len(pending_jobs)}")
        print(f"  - Jobs avec autre statut: {len(non_pending_jobs)}")

        if non_pending_jobs:
            print("\nERREUR: Logique 'tous ou rien' - VALIDATION IMPOSSIBLE")
            print("   Raison: Certains jobs ne sont pas en statut 'EN ATTENTE'")
            for job in non_pending_jobs:
                print(f"   - {job.reference}: {job.status}")

            # Tester la méthode (devrait lever une erreur)
            try:
                result = service.auto_validate_jobs(inventory_id, warehouse_id)
                print("ATTENTION: La méthode n'a pas leve d'erreur comme attendu!")
                print(f"Resultat: {result}")
            except Exception as e:
                print(f"OK: Erreur attendue: {str(e)}")

        else:
            print("\nOK: Logique 'tous ou rien' - VALIDATION POSSIBLE")
            print("   Tous les jobs sont en statut 'EN ATTENTE'")

            # Tester la méthode (devrait réussir)
            try:
                result = service.auto_validate_jobs(inventory_id, warehouse_id)
                print(f"OK: Validation reussie: {result}")
            except Exception as e:
                print(f"ERREUR: Erreur inattendue: {str(e)}")

    except Exception as e:
        print(f"Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_or_nothing_logic()
