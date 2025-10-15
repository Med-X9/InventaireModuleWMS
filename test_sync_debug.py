import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Inventory, Job, Assigment
from apps.users.models import UserApp
from apps.mobile.services.sync_service import SyncService

def debug_sync_data(user_id):
    """Débogue les données de synchronisation"""
    
    print(f"\n{'='*60}")
    print(f"DÉBOGAGE SYNCHRONISATION - USER ID: {user_id}")
    print(f"{'='*60}\n")
    
    # 1. Vérifier l'utilisateur
    try:
        user = UserApp.objects.get(id=user_id)
        print(f"✓ Utilisateur trouvé: {user.nom} {user.prenom}")
        print(f"  - Compte: {user.compte.account_name if user.compte else 'AUCUN'}")
    except UserApp.DoesNotExist:
        print(f"✗ Utilisateur {user_id} non trouvé")
        return
    
    # 2. Vérifier les inventaires
    print(f"\n{'='*60}")
    print("INVENTAIRES")
    print(f"{'='*60}")
    
    inventories_all = Inventory.objects.filter(
        awi_links__account=user.compte
    ).distinct()
    print(f"Total inventaires du compte: {inventories_all.count()}")
    
    inventories_in_realisation = Inventory.objects.filter(
        awi_links__account=user.compte,
        status='EN REALISATION'
    ).distinct()
    print(f"Inventaires 'EN REALISATION': {inventories_in_realisation.count()}")
    
    for inv in inventories_in_realisation:
        print(f"\n  Inventaire ID {inv.id}:")
        print(f"    - Référence: {inv.reference}")
        print(f"    - Statut: {inv.status}")
        print(f"    - Type: {inv.inventory_type}")
        
    # 3. Vérifier les jobs
    print(f"\n{'='*60}")
    print("JOBS")
    print(f"{'='*60}")
    
    all_jobs = Job.objects.all()
    print(f"Total jobs dans la base: {all_jobs.count()}")
    
    for job in all_jobs:
        print(f"\n  Job ID {job.id}:")
        print(f"    - Référence: {job.reference}")
        print(f"    - Statut: {job.status}")
        print(f"    - Inventaire ID: {job.inventory.id if job.inventory else 'AUCUN'}")
        print(f"    - Inventaire Réf: {job.inventory.reference if job.inventory else 'AUCUN'}")
    
    if inventories_in_realisation.exists():
        jobs_for_inventories = Job.objects.filter(inventory__in=inventories_in_realisation)
        print(f"\nJobs liés aux inventaires EN REALISATION: {jobs_for_inventories.count()}")
        
        for job in jobs_for_inventories:
            print(f"\n  Job ID {job.id}:")
            print(f"    - Référence: {job.reference}")
            print(f"    - Statut: {job.status}")
            print(f"    - Inventaire: {job.inventory.reference}")
    
    # 4. Vérifier les assignments
    print(f"\n{'='*60}")
    print("ASSIGNMENTS")
    print(f"{'='*60}")
    
    all_assignments = Assigment.objects.all()
    print(f"Total assignments dans la base: {all_assignments.count()}")
    
    for assignment in all_assignments:
        print(f"\n  Assignment ID {assignment.id}:")
        print(f"    - Référence: {assignment.reference}")
        print(f"    - Statut: {assignment.status}")
        print(f"    - Job ID: {assignment.job.id if assignment.job else 'AUCUN'}")
        print(f"    - Session ID: {assignment.session_id}")
        print(f"    - Counting ID: {assignment.counting.id if assignment.counting else 'AUCUN'}")
    
    if inventories_in_realisation.exists():
        jobs_for_inventories = Job.objects.filter(inventory__in=inventories_in_realisation)
        if jobs_for_inventories.exists():
            assignments_for_jobs = Assigment.objects.filter(job__in=jobs_for_inventories)
            print(f"\nAssignments liés aux jobs: {assignments_for_jobs.count()}")
            
            for assignment in assignments_for_jobs:
                print(f"\n  Assignment ID {assignment.id}:")
                print(f"    - Référence: {assignment.reference}")
                print(f"    - Statut: {assignment.status}")
                print(f"    - Job: {assignment.job.reference}")
    
    # 5. Tester le service de synchronisation
    print(f"\n{'='*60}")
    print("TEST SERVICE SYNCHRONISATION")
    print(f"{'='*60}\n")
    
    try:
        sync_service = SyncService()
        result = sync_service.sync_data(user_id)
        
        print(f"✓ Synchronisation réussie")
        print(f"  - Sync ID: {result['sync_id']}")
        print(f"  - Inventaires: {len(result['data']['inventories'])}")
        print(f"  - Jobs: {len(result['data']['jobs'])}")
        print(f"  - Assignments: {len(result['data']['assignments'])}")
        print(f"  - Countings: {len(result['data']['countings'])}")
        
        if len(result['data']['jobs']) == 0:
            print("\n⚠ ATTENTION: Aucun job retourné!")
            print("Vérifiez que les jobs sont bien liés aux inventaires EN REALISATION")
        
        if len(result['data']['assignments']) == 0:
            print("\n⚠ ATTENTION: Aucun assignment retourné!")
            print("Vérifiez que les assignments sont bien liés aux jobs")
            
    except Exception as e:
        print(f"✗ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        # Par défaut, utiliser user_id = 3 comme dans la réponse JSON
        user_id = 3
    
    debug_sync_data(user_id)

