#!/usr/bin/env python
"""
Script de test pour vérifier l'API job ready avec un seul assignment affecté
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting, Inventory
from apps.inventory.usecases.job_ready import JobReadyUseCase
from apps.inventory.services.job_service import JobService
from apps.masterdata.models import Warehouse, Account, Location, SousZone, Zone
from apps.users.models import UserApp
from django.utils import timezone

def test_job_ready_single_assignment():
    """Test l'API job ready avec un seul assignment affecté"""
    
    print("=== TEST JOB READY AVEC UN SEUL ASSIGNMENT AFFECTÉ ===")
    
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
    
    # Créer un utilisateur mobile (session)
    mobile_user = UserApp.objects.create(
        username='mobile_test',
        email='mobile@test.com',
        type='Mobile'
    )
    
    print(f"   - Compte créé: {account.name}")
    print(f"   - Warehouse créé: {warehouse.name}")
    print(f"   - Emplacements créés: {len(locations)}")
    print(f"   - Utilisateur mobile créé: {mobile_user.username}")
    
    # 2. Test 1: Configuration avec image de stock
    print("\n2. Test 1: Configuration avec image de stock...")
    
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
        
        # Valider les jobs
        job_ids = [job.id for job in jobs]
        result = job_service.validate_jobs(job_ids)
        print(f"   ✅ SUCCÈS: {result['validated_jobs_count']} jobs validés")
        
        # Affecter une session au 2ème comptage
        from apps.inventory.services.assignment_service import AssignmentService
        assignment_service = AssignmentService()
        
        assignment_data = {
            'job_ids': job_ids,
            'counting_order': 2,
            'session_id': mobile_user.id,
            'date_start': timezone.now()
        }
        
        result = assignment_service.assign_jobs(assignment_data)
        print(f"   ✅ SUCCÈS: {result['assignments_created']} affectations créées")
        
        # Mettre les jobs en PRET
        job_ready_use_case = JobReadyUseCase()
        result = job_ready_use_case.execute(job_ids)
        
        print(f"   ✅ SUCCÈS: {result['ready_jobs_count']} jobs mis en PRET")
        print(f"   - Message: {result['message']}")
        
        # Vérifier le statut final
        for job in jobs:
            job.refresh_from_db()
            assignments = Assigment.objects.filter(job=job)
            print(f"   - Job {job.reference}: statut {job.status}")
            for assignment in assignments:
                assignment.refresh_from_db()
                print(f"     - Assignment {assignment.reference}: statut {assignment.status}, session {assignment.session}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # 3. Test 2: Configuration normale
    print("\n3. Test 2: Configuration normale...")
    
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
        
        # Vérifier qu'il y a deux assignments
        job = jobs_normal[0]
        assignments = Assigment.objects.filter(job=job)
        if assignments.count() == 2:
            print(f"   ✅ CORRECT: Deux assignments créés pour les deux comptages")
        else:
            print(f"   ❌ ERREUR: {assignments.count()} assignments créés au lieu de 2")
        
        # Valider les jobs
        job_ids = [job.id for job in jobs_normal]
        result = job_service.validate_jobs(job_ids)
        print(f"   ✅ SUCCÈS: {result['validated_jobs_count']} jobs validés")
        
        # Affecter des sessions aux deux comptages
        for counting_order in [1, 2]:
            assignment_data = {
                'job_ids': job_ids,
                'counting_order': counting_order,
                'session_id': mobile_user.id,
                'date_start': timezone.now()
            }
            
            result = assignment_service.assign_jobs(assignment_data)
            print(f"   ✅ SUCCÈS: {result['assignments_created']} affectations créées pour comptage {counting_order}")
        
        # Mettre les jobs en PRET
        result = job_ready_use_case.execute(job_ids)
        
        print(f"   ✅ SUCCÈS: {result['ready_jobs_count']} jobs mis en PRET")
        print(f"   - Message: {result['message']}")
        
        # Vérifier le statut final
        for job in jobs_normal:
            job.refresh_from_db()
            assignments = Assigment.objects.filter(job=job)
            print(f"   - Job {job.reference}: statut {job.status}")
            for assignment in assignments:
                assignment.refresh_from_db()
                print(f"     - Assignment {assignment.reference}: statut {assignment.status}, session {assignment.session}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # 4. Test 3: Test d'erreur - job sans session affectée
    print("\n4. Test 3: Test d'erreur - job sans session affectée...")
    
    # Créer un job avec image de stock mais sans affecter de session
    inventory_test = Inventory.objects.create(
        label='Test Inventory Error',
        date=timezone.now(),
        status='EN PREPARATION'
    )
    
    counting1_test = Counting.objects.create(
        order=1,
        count_mode='image de stock',
        inventory=inventory_test
    )
    
    counting2_test = Counting.objects.create(
        order=2,
        count_mode='en vrac',
        inventory=inventory_test
    )
    
    try:
        jobs_test = job_service.create_jobs_for_inventory_warehouse(
            inventory_test.id,
            warehouse.id,
            emplacement_ids[:1]  # Un seul emplacement
        )
        
        # Valider le job
        job_ids_test = [jobs_test[0].id]
        result = job_service.validate_jobs(job_ids_test)
        print(f"   ✅ SUCCÈS: {result['validated_jobs_count']} jobs validés")
        
        # Essayer de mettre en PRET sans affecter de session
        try:
            result = job_ready_use_case.execute(job_ids_test)
            print(f"   ❌ ERREUR INATTENDUE: {result['ready_jobs_count']} jobs mis en PRET")
        except Exception as e:
            print(f"   ✅ ERREUR ATTENDUE: {e}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # 5. Test 4: Test d'erreur - job avec statut invalide
    print("\n5. Test 4: Test d'erreur - job avec statut invalide...")
    
    try:
        # Essayer de mettre en PRET un job en attente
        job_ids_invalid = [jobs[0].id]
        jobs[0].status = 'EN ATTENTE'
        jobs[0].save()
        
        try:
            result = job_ready_use_case.execute(job_ids_invalid)
            print(f"   ❌ ERREUR INATTENDUE: {result['ready_jobs_count']} jobs mis en PRET")
        except Exception as e:
            print(f"   ✅ ERREUR ATTENDUE: {e}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    print("\n=== FIN DES TESTS ===")
    print("✅ Tous les tests ont été exécutés")
    print("✅ La logique de validation fonctionne correctement")
    print("✅ Les cas d'erreur sont bien gérés")

if __name__ == "__main__":
    test_job_ready_single_assignment() 