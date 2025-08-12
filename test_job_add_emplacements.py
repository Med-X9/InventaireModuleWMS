#!/usr/bin/env python
"""
Script de test pour la nouvelle logique d'ajout d'emplacements avec comptages multiples
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
from apps.inventory.usecases.job_add_emplacements import JobAddEmplacementsUseCase

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
    
    # Vérifier s'il y a des emplacements disponibles
    locations = Location.objects.all()
    print(f"   - Emplacements trouvés: {locations.count()}")
    
    if locations.count() == 0:
        print("❌ Aucun emplacement trouvé. Créez d'abord des emplacements.")
        return False
    
    # Prendre les 3 premiers emplacements qui ne sont pas déjà dans le job
    job_locations = JobDetail.objects.filter(job=job).values_list('location_id', flat=True)
    available_locations = locations.exclude(id__in=job_locations)[:3]
    
    if available_locations.count() == 0:
        print("❌ Aucun emplacement disponible pour ce job.")
        return False
    
    print(f"   - Utilisation de {available_locations.count()} emplacements disponibles")
    
    # Test d'ajout d'emplacements
    print("\n🧪 Test d'ajout d'emplacements...")
    
    use_case = JobAddEmplacementsUseCase()
    emplacement_ids = [loc.id for loc in available_locations]
    
    try:
        result = use_case.execute(job.id, emplacement_ids)
        
        print(f"✅ Emplacements ajoutés avec succès:")
        print(f"   - Job ID: {result['job_id']}")
        print(f"   - Job Reference: {result['job_reference']}")
        print(f"   - Emplacements ajoutés: {result['emplacements_added']}")
        print(f"   - Mode 1er comptage: {result['counting1_mode']}")
        print(f"   - Mode 2ème comptage: {result['counting2_mode']}")
        print(f"   - Assignments total: {result['assignments_count']}")
        
        # Vérifier les JobDetails
        job_details = JobDetail.objects.filter(job=job)
        print(f"   - JobDetails total: {job_details.count()}")
        
        # Vérifier les Assignments
        assignments = Assigment.objects.filter(job=job)
        print(f"   - Assignments total: {assignments.count()}")
        
        # Nettoyer les JobDetails ajoutés pour ce test
        for location in available_locations:
            JobDetail.objects.filter(job=job, location=location).delete()
        print("   - JobDetails de test supprimés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test d'ajout d'emplacements avec données existantes")
    
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
