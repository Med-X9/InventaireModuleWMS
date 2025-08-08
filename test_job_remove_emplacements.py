#!/usr/bin/env python
"""
Script de test pour la nouvelle logique de suppression d'emplacements avec comptages multiples
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Inventory, Counting, Job, JobDetail, Assigment
from apps.masterdata.models import Warehouse, Location
from apps.inventory.usecases.job_remove_emplacements import JobRemoveEmplacementsUseCase

def test_with_existing_data():
    """Test avec des données existantes"""
    print("🔍 Recherche de données existantes...")
    
    # Vérifier s'il y a des jobs
    jobs = Job.objects.all()
    print(f"   - Jobs trouvés: {jobs.count()}")
    
    if jobs.count() == 0:
        print("❌ Aucun job trouvé. Créez d'abord un job.")
        return False
    
    # Prendre le premier job
    job = jobs.first()
    print(f"   - Utilisation du job: {job.reference}")
    
    # Vérifier les comptages de l'inventaire
    countings = Counting.objects.filter(inventory=job.inventory).order_by('order')
    print(f"   - Comptages trouvés: {countings.count()}")
    
    if countings.count() < 2:
        print("❌ L'inventaire doit avoir au moins 2 comptages.")
        return False
    
    # Vérifier s'il y a des emplacements dans le job
    job_details = JobDetail.objects.filter(job=job)
    print(f"   - JobDetails trouvés: {job_details.count()}")
    
    if job_details.count() == 0:
        print("❌ Aucun emplacement dans ce job. Ajoutez d'abord des emplacements.")
        return False
    
    # Prendre les 3 premiers emplacements du job
    job_locations = job_details.values_list('location_id', flat=True).distinct()[:3]
    locations_to_remove = Location.objects.filter(id__in=job_locations)
    
    if locations_to_remove.count() == 0:
        print("❌ Aucun emplacement disponible pour la suppression.")
        return False
    
    print(f"   - Utilisation de {locations_to_remove.count()} emplacements à supprimer")
    
    # Sauvegarder l'état initial pour comparaison
    initial_job_details_count = job_details.count()
    initial_assignments_count = Assigment.objects.filter(job=job).count()
    
    # Test de suppression d'emplacements
    print("\n🧪 Test de suppression d'emplacements...")
    
    use_case = JobRemoveEmplacementsUseCase()
    emplacement_ids = [loc.id for loc in locations_to_remove]
    
    try:
        result = use_case.execute(job.id, emplacement_ids)
        
        print(f"✅ Emplacements supprimés avec succès:")
        print(f"   - Job ID: {result['job_id']}")
        print(f"   - Job Reference: {result['job_reference']}")
        print(f"   - Emplacements supprimés: {result['emplacements_deleted']}")
        print(f"   - Mode 1er comptage: {result['counting1_mode']}")
        print(f"   - Mode 2ème comptage: {result['counting2_mode']}")
        print(f"   - Assignments restants: {result['assignments_count']}")
        
        # Vérifier les JobDetails restants
        remaining_job_details = JobDetail.objects.filter(job=job)
        print(f"   - JobDetails restants: {remaining_job_details.count()}")
        
        # Vérifier les Assignments restants
        remaining_assignments = Assigment.objects.filter(job=job)
        print(f"   - Assignments restants: {remaining_assignments.count()}")
        
        # Vérifier les changements
        job_details_deleted = initial_job_details_count - remaining_job_details.count()
        assignments_deleted = initial_assignments_count - remaining_assignments.count()
        
        print(f"   - JobDetails supprimés: {job_details_deleted}")
        print(f"   - Assignments supprimés: {assignments_deleted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de suppression d'emplacements avec données existantes")
    
    try:
        success = test_with_existing_data()
        
        if success:
            print("\n🎉 Test réussi!")
        else:
            print("\n⚠️ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")

if __name__ == "__main__":
    main()
