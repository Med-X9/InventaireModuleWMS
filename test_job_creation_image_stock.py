#!/usr/bin/env python
"""
Script de test pour vérifier la création de jobs avec image de stock
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting, Inventory
from apps.inventory.services.job_service import JobService
from apps.masterdata.models import Warehouse, Account, Location, SousZone, Zone
from django.utils import timezone

def test_job_creation_with_image_stock():
    """Test la création de jobs avec image de stock"""
    
    print("=== TEST CRÉATION DE JOBS AVEC IMAGE DE STOCK ===")
    
    # 1. Créer les données de test
    print("\n1. Création des données de test...")
    
    # Créer un compte
    account = Account.objects.create(
        name='Test Account',
        code='TEST001'
    )
    
    # Créer un warehouse
    warehouse = Warehouse.objects.create(
        name='Test Warehouse',
        code='WH001',
        account=account
    )
    
    # Créer une zone
    zone = Zone.objects.create(
        name='Test Zone',
        warehouse=warehouse
    )
    
    # Créer une sous-zone
    sous_zone = SousZone.objects.create(
        name='Test Sous Zone',
        zone=zone
    )
    
    # Créer des emplacements
    locations = []
    for i in range(3):
        location = Location.objects.create(
            location_reference=f'LOC{i+1:03d}',
            sous_zone=sous_zone
        )
        locations.append(location)
    
    print(f"   - Compte créé: {account.name}")
    print(f"   - Warehouse créé: {warehouse.name}")
    print(f"   - Zone créée: {zone.name}")
    print(f"   - Sous-zone créée: {sous_zone.name}")
    print(f"   - Emplacements créés: {len(locations)}")
    
    # 2. Test 1: Création avec image de stock
    print("\n2. Test 1: Création avec image de stock...")
    
    # Créer un inventaire avec image de stock
    inventory_image_stock = Inventory.objects.create(
        label='Test Inventory Image Stock',
        date=timezone.now(),
        status='EN PREPARATION'
    )
    
    # Créer les comptages : 1er = image de stock, 2ème = en vrac
    counting1 = Counting.objects.create(
        order=1,
        count_mode='image de stock',
        inventory=inventory_image_stock
    )
    
    counting2 = Counting.objects.create(
        order=2,
        count_mode='en vrac',
        inventory=inventory_image_stock
    )
    
    print(f"   - Inventaire créé: {inventory_image_stock.reference}")
    print(f"   - Comptage 1: {counting1.reference} (image de stock)")
    print(f"   - Comptage 2: {counting2.reference} (en vrac)")
    
    # Créer les jobs
    emplacement_ids = [loc.id for loc in locations]
    job_service = JobService()
    
    try:
        jobs = job_service.create_jobs_for_inventory_warehouse(
            inventory_image_stock.id,
            warehouse.id,
            emplacement_ids
        )
        
        print(f"   ✅ SUCCÈS: {len(jobs)} jobs créés")
        
        # Vérifier les jobs créés
        for job in jobs:
            print(f"   - Job créé: {job.reference} (statut: {job.status})")
            
            # Vérifier les assignments
            assignments = Assigment.objects.filter(job=job)
            print(f"     Assignments créés: {assignments.count()}")
            
            for assignment in assignments:
                print(f"       - Assignment {assignment.reference}: comptage {assignment.counting.reference} (ordre {assignment.counting.order})")
                print(f"         Statut: {assignment.status}")
                print(f"         Session: {assignment.session}")
        
        # Vérifier qu'il n'y a qu'un seul assignment (pour le 2ème comptage)
        job = jobs[0]
        assignments = Assigment.objects.filter(job=job)
        if assignments.count() == 1:
            assignment = assignments.first()
            if assignment.counting.order == 2:
                print(f"   ✅ CORRECT: Un seul assignment créé pour le 2ème comptage")
            else:
                print(f"   ❌ ERREUR: Assignment créé pour le mauvais comptage (ordre {assignment.counting.order})")
        else:
            print(f"   ❌ ERREUR: {assignments.count()} assignments créés au lieu d'1")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # 3. Test 2: Création avec configuration normale
    print("\n3. Test 2: Création avec configuration normale...")
    
    # Créer un inventaire normal
    inventory_normal = Inventory.objects.create(
        label='Test Inventory Normal',
        date=timezone.now(),
        status='EN PREPARATION'
    )
    
    # Créer les comptages : 1er = en vrac, 2ème = par article
    counting1_normal = Counting.objects.create(
        order=1,
        count_mode='en vrac',
        inventory=inventory_normal
    )
    
    counting2_normal = Counting.objects.create(
        order=2,
        count_mode='par article',
        inventory=inventory_normal
    )
    
    print(f"   - Inventaire créé: {inventory_normal.reference}")
    print(f"   - Comptage 1: {counting1_normal.reference} (en vrac)")
    print(f"   - Comptage 2: {counting2_normal.reference} (par article)")
    
    try:
        jobs_normal = job_service.create_jobs_for_inventory_warehouse(
            inventory_normal.id,
            warehouse.id,
            emplacement_ids
        )
        
        print(f"   ✅ SUCCÈS: {len(jobs_normal)} jobs créés")
        
        # Vérifier les jobs créés
        for job in jobs_normal:
            print(f"   - Job créé: {job.reference} (statut: {job.status})")
            
            # Vérifier les assignments
            assignments = Assigment.objects.filter(job=job)
            print(f"     Assignments créés: {assignments.count()}")
            
            for assignment in assignments:
                print(f"       - Assignment {assignment.reference}: comptage {assignment.counting.reference} (ordre {assignment.counting.order})")
                print(f"         Statut: {assignment.status}")
                print(f"         Session: {assignment.session}")
        
        # Vérifier qu'il y a deux assignments (pour les deux comptages)
        job = jobs_normal[0]
        assignments = Assigment.objects.filter(job=job)
        if assignments.count() == 2:
            print(f"   ✅ CORRECT: Deux assignments créés pour les deux comptages")
        else:
            print(f"   ❌ ERREUR: {assignments.count()} assignments créés au lieu de 2")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # 4. Test 3: Vérification des JobDetails
    print("\n4. Test 3: Vérification des JobDetails...")
    
    # Vérifier les JobDetails du premier job
    job = jobs[0]
    job_details = job.jobdetail_set.all()
    print(f"   - JobDetails créés pour {job.reference}: {job_details.count()}")
    
    for job_detail in job_details:
        print(f"     - JobDetail {job_detail.reference}: emplacement {job_detail.location.location_reference}")
        print(f"       Statut: {job_detail.status}")
    
    # 5. Test 4: Test d'erreur avec emplacement inexistant
    print("\n5. Test 4: Test d'erreur avec emplacement inexistant...")
    
    try:
        jobs_error = job_service.create_jobs_for_inventory_warehouse(
            inventory_image_stock.id,
            warehouse.id,
            [99999]  # Emplacement inexistant
        )
        print(f"   ❌ ERREUR INATTENDUE: {len(jobs_error)} jobs créés")
    except Exception as e:
        print(f"   ✅ ERREUR ATTENDUE: {e}")
    
    # 6. Test 5: Test d'erreur avec emplacement d'un autre warehouse
    print("\n6. Test 5: Test d'erreur avec emplacement d'un autre warehouse...")
    
    # Créer un autre warehouse et un emplacement
    warehouse2 = Warehouse.objects.create(
        name='Test Warehouse 2',
        code='WH002',
        account=account
    )
    
    zone2 = Zone.objects.create(
        name='Test Zone 2',
        warehouse=warehouse2
    )
    
    sous_zone2 = SousZone.objects.create(
        name='Test Sous Zone 2',
        zone=zone2
    )
    
    location_other_warehouse = Location.objects.create(
        location_reference='LOC999',
        sous_zone=sous_zone2
    )
    
    try:
        jobs_error = job_service.create_jobs_for_inventory_warehouse(
            inventory_image_stock.id,
            warehouse.id,
            [location_other_warehouse.id]
        )
        print(f"   ❌ ERREUR INATTENDUE: {len(jobs_error)} jobs créés")
    except Exception as e:
        print(f"   ✅ ERREUR ATTENDUE: {e}")
    
    print("\n=== FIN DES TESTS ===")

if __name__ == "__main__":
    test_job_creation_with_image_stock() 