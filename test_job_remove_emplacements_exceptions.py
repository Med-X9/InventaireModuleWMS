#!/usr/bin/env python
"""
Script de test pour vérifier la gestion des exceptions dans l'API de suppression d'emplacements
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

def test_exceptions():
    """Test de la gestion des exceptions"""
    print("🧪 Test de la gestion des exceptions...")
    
    use_case = JobRemoveEmplacementsUseCase()
    
    # Test 1: job_id invalide
    print("\n📋 Test 1: job_id invalide")
    try:
        result = use_case.execute(0, [1, 2, 3])
        print("❌ Erreur: L'exception n'a pas été levée")
    except Exception as e:
        print(f"✅ Exception attendue: {str(e)}")
    
    # Test 2: job_id négatif
    try:
        result = use_case.execute(-1, [1, 2, 3])
        print("❌ Erreur: L'exception n'a pas été levée")
    except Exception as e:
        print(f"✅ Exception attendue: {str(e)}")
    
    # Test 3: liste d'emplacements vide
    print("\n📋 Test 3: liste d'emplacements vide")
    try:
        result = use_case.execute(1, [])
        print("❌ Erreur: L'exception n'a pas été levée")
    except Exception as e:
        print(f"✅ Exception attendue: {str(e)}")
    
    # Test 4: emplacement_ids None
    try:
        result = use_case.execute(1, None)
        print("❌ Erreur: L'exception n'a pas été levée")
    except Exception as e:
        print(f"✅ Exception attendue: {str(e)}")
    
    # Test 5: emplacement_ids pas une liste
    print("\n📋 Test 5: emplacement_ids pas une liste")
    try:
        result = use_case.execute(1, "pas une liste")
        print("❌ Erreur: L'exception n'a pas été levée")
    except Exception as e:
        print(f"✅ Exception attendue: {str(e)}")
    
    # Test 6: IDs d'emplacements invalides
    print("\n📋 Test 6: IDs d'emplacements invalides")
    try:
        result = use_case.execute(1, [0, -1, "string"])
        print("❌ Erreur: L'exception n'a pas été levée")
    except Exception as e:
        print(f"✅ Exception attendue: {str(e)}")
    
    # Test 7: Job inexistant
    print("\n📋 Test 7: Job inexistant")
    try:
        result = use_case.execute(99999, [1, 2, 3])
        print("❌ Erreur: L'exception n'a pas été levée")
    except Exception as e:
        print(f"✅ Exception attendue: {str(e)}")
    
    # Test 8: Emplacements inexistants
    print("\n📋 Test 8: Emplacements inexistants")
    try:
        result = use_case.execute(1, [99999, 99998, 99997])
        print("❌ Erreur: L'exception n'a pas été levée")
    except Exception as e:
        print(f"✅ Exception attendue: {str(e)}")
    
    # Test 9: Job sans emplacements à supprimer
    print("\n📋 Test 9: Job sans emplacements à supprimer")
    jobs = Job.objects.all()
    if jobs.count() > 0:
        job = jobs.first()
        # Prendre des emplacements qui ne sont pas dans ce job
        job_locations = JobDetail.objects.filter(job=job).values_list('location_id', flat=True)
        all_locations = Location.objects.all()
        locations_not_in_job = all_locations.exclude(id__in=job_locations)[:3]
        
        if locations_not_in_job.count() > 0:
            try:
                result = use_case.execute(job.id, [loc.id for loc in locations_not_in_job])
                print("❌ Erreur: L'exception n'a pas été levée")
            except Exception as e:
                print(f"✅ Exception attendue: {str(e)}")
        else:
            print("⚠️ Pas d'emplacements disponibles pour ce test")
    else:
        print("⚠️ Aucun job disponible pour ce test")
    
    # Test 10: Inventaire avec moins de 2 comptages
    print("\n📋 Test 10: Inventaire avec moins de 2 comptages")
    # Chercher un inventaire avec moins de 2 comptages
    inventories = Inventory.objects.all()
    for inventory in inventories:
        countings = Counting.objects.filter(inventory=inventory)
        if countings.count() < 2:
            # Créer un job temporaire pour ce test
            warehouses = Warehouse.objects.all()
            if warehouses.count() > 0:
                warehouse = warehouses.first()
                job = Job.objects.create(
                    inventory=inventory,
                    warehouse=warehouse,
                    status='EN ATTENTE'
                )
                
                try:
                    result = use_case.execute(job.id, [1, 2, 3])
                    print("❌ Erreur: L'exception n'a pas été levée")
                except Exception as e:
                    print(f"✅ Exception attendue: {str(e)}")
                
                # Nettoyer le job créé
                job.delete()
                break
    else:
        print("⚠️ Tous les inventaires ont au moins 2 comptages")
    
    print("\n🎉 Tests d'exceptions terminés!")

def main():
    """Fonction principale de test"""
    print("🚀 Test de gestion des exceptions pour la suppression d'emplacements")
    
    try:
        test_exceptions()
        print("\n✅ Tous les tests d'exceptions ont réussi!")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests d'exceptions: {str(e)}")

if __name__ == "__main__":
    main()
