#!/usr/bin/env python
"""
Script de test complet pour la suppression d'emplacements avec comptages multiples
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
from apps.inventory.usecases.job_remove_emplacements import JobRemoveEmplacementsUseCase

def test_complete_workflow():
    """Test complet : ajout puis suppression d'emplacements"""
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
    
    # Étape 1: Ajouter des emplacements
    print("\n🧪 Étape 1: Ajout d'emplacements...")
    
    add_use_case = JobAddEmplacementsUseCase()
    emplacement_ids = [loc.id for loc in available_locations]
    
    try:
        add_result = add_use_case.execute(job.id, emplacement_ids)
        
        print(f"✅ Emplacements ajoutés avec succès:")
        print(f"   - Emplacements ajoutés: {add_result['emplacements_added']}")
        print(f"   - Mode 1er comptage: {add_result['counting1_mode']}")
        print(f"   - Mode 2ème comptage: {add_result['counting2_mode']}")
        print(f"   - Assignments total: {add_result['assignments_count']}")
        
        # Vérifier les JobDetails après ajout
        job_details_after_add = JobDetail.objects.filter(job=job)
        print(f"   - JobDetails après ajout: {job_details_after_add.count()}")
        
        # Étape 2: Supprimer les mêmes emplacements
        print("\n🧪 Étape 2: Suppression d'emplacements...")
        
        remove_use_case = JobRemoveEmplacementsUseCase()
        
        remove_result = remove_use_case.execute(job.id, emplacement_ids)
        
        print(f"✅ Emplacements supprimés avec succès:")
        print(f"   - Emplacements supprimés: {remove_result['emplacements_deleted']}")
        print(f"   - Mode 1er comptage: {remove_result['counting1_mode']}")
        print(f"   - Mode 2ème comptage: {remove_result['counting2_mode']}")
        print(f"   - Assignments restants: {remove_result['assignments_count']}")
        
        # Vérifier les JobDetails après suppression
        job_details_after_remove = JobDetail.objects.filter(job=job)
        print(f"   - JobDetails après suppression: {job_details_after_remove.count()}")
        
        # Vérifier les Assignments après suppression
        assignments_after_remove = Assigment.objects.filter(job=job)
        print(f"   - Assignments après suppression: {assignments_after_remove.count()}")
        
        # Vérifier la cohérence
        job_details_added = add_result['emplacements_added']
        job_details_deleted = remove_result['emplacements_deleted']
        
        print(f"\n📊 Résumé:")
        print(f"   - JobDetails ajoutés: {job_details_added}")
        print(f"   - JobDetails supprimés: {job_details_deleted}")
        print(f"   - Différence: {job_details_added - job_details_deleted}")
        
        if job_details_added == job_details_deleted:
            print("✅ Cohérence vérifiée: tous les emplacements ajoutés ont été supprimés")
        else:
            print("⚠️ Incohérence détectée dans le nombre d'emplacements")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test complet de workflow ajout/suppression d'emplacements")
    
    try:
        success = test_complete_workflow()
        
        if success:
            print("\n🎉 Test complet réussi!")
        else:
            print("\n⚠️ Test complet échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")

if __name__ == "__main__":
    main()
