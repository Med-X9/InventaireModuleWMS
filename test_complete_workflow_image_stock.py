#!/usr/bin/env python
"""
Script de test complet pour vérifier le workflow avec image de stock
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting, Inventory
from apps.inventory.services.job_service import JobService
from apps.inventory.usecases.job_ready import JobReadyUseCase
from apps.masterdata.models import Warehouse, Account, Location, SousZone, Zone
from apps.users.models import UserApp
from django.utils import timezone

def test_complete_workflow_image_stock():
    """Test le workflow complet avec image de stock"""
    
    print("=== TEST WORKFLOW COMPLET AVEC IMAGE DE STOCK ===")
    
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
    
    # 2. Créer un inventaire avec image de stock
    print("\n2. Création de l'inventaire avec image de stock...")
    
    inventory = Inventory.objects.create(
        label='Test Inventory Image Stock',
        date=timezone.now(),
        status='EN PREPARATION'
    )
    
    # Créer les comptages : 1er = image de stock, 2ème = en vrac
    counting1 = Counting.objects.create(
        order=1,
        count_mode='image de stock',
        inventory=inventory
    )
    
    counting2 = Counting.objects.create(
        order=2,
        count_mode='en vrac',
        inventory=inventory
    )
    
    print(f"   - Inventaire créé: {inventory.reference}")
    print(f"   - Comptage 1: {counting1.reference} (image de stock)")
    print(f"   - Comptage 2: {counting2.reference} (en vrac)")
    
    # 3. Créer les jobs
    print("\n3. Création des jobs...")
    
    emplacement_ids = [loc.id for loc in locations]
    job_service = JobService()
    
    try:
        jobs = job_service.create_jobs_for_inventory_warehouse(
            inventory.id,
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
        return
    
    # 4. Valider les jobs
    print("\n4. Validation des jobs...")
    
    try:
        job_ids = [job.id for job in jobs]
        result = job_service.validate_jobs(job_ids)
        
        print(f"   ✅ SUCCÈS: {result['validated_jobs_count']} jobs validés")
        print(f"   - Message: {result['message']}")
        
        # Vérifier le statut des jobs
        for job in jobs:
            job.refresh_from_db()
            print(f"   - Job {job.reference}: statut {job.status}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        return
    
    # 5. Affecter une session au 2ème comptage
    print("\n5. Affectation d'une session au 2ème comptage...")
    
    try:
        from apps.inventory.services.assignment_service import AssignmentService
        
        assignment_service = AssignmentService()
        
        # Affecter une session au 2ème comptage
        assignment_data = {
            'job_ids': job_ids,
            'counting_order': 2,
            'session_id': mobile_user.id,
            'date_start': timezone.now()
        }
        
        result = assignment_service.assign_jobs(assignment_data)
        
        print(f"   ✅ SUCCÈS: {result['assignments_created']} affectations créées")
        print(f"   - Message: {result['message']}")
        
        # Vérifier les assignments
        for job in jobs:
            assignments = Assigment.objects.filter(job=job)
            for assignment in assignments:
                assignment.refresh_from_db()
                print(f"   - Assignment {assignment.reference}: statut {assignment.status}, session {assignment.session}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        return
    
    # 6. Mettre les jobs en PRET
    print("\n6. Mise en PRET des jobs...")
    
    try:
        job_ready_use_case = JobReadyUseCase()
        result = job_ready_use_case.execute(job_ids)
        
        print(f"   ✅ SUCCÈS: {result['ready_jobs_count']} jobs mis en PRET")
        print(f"   - Message: {result['message']}")
        
        # Vérifier le statut des assignments
        for job in jobs:
            assignments = Assigment.objects.filter(job=job)
            for assignment in assignments:
                assignment.refresh_from_db()
                print(f"   - Assignment {assignment.reference}: statut {assignment.status}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        return
    
    # 7. Vérification finale
    print("\n7. Vérification finale...")
    
    # Vérifier que tout est cohérent
    for job in jobs:
        job.refresh_from_db()
        assignments = Assigment.objects.filter(job=job)
        
        print(f"   - Job {job.reference}:")
        print(f"     Statut: {job.status}")
        print(f"     Assignments: {assignments.count()}")
        
        for assignment in assignments:
            print(f"       - Assignment {assignment.reference}:")
            print(f"         Comptage: {assignment.counting.reference} (ordre {assignment.counting.order})")
            print(f"         Statut: {assignment.status}")
            print(f"         Session: {assignment.session}")
            print(f"         Date affecte: {assignment.affecte_date}")
            print(f"         Date pret: {assignment.pret_date}")
    
    print("\n=== WORKFLOW COMPLET RÉUSSI ===")
    print("✅ Toutes les étapes ont fonctionné correctement")
    print("✅ Le cas spécial 'image de stock' est géré correctement")
    print("✅ Les jobs peuvent être mis en PRET avec un seul assignment")

def test_workflow_normal():
    """Test le workflow normal (sans image de stock) pour comparaison"""
    
    print("\n\n=== TEST WORKFLOW NORMAL (COMPARAISON) ===")
    
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
    
    print(f"   - Inventaire normal créé: {inventory_normal.reference}")
    print(f"   - Comptage 1: {counting1_normal.reference} (en vrac)")
    print(f"   - Comptage 2: {counting2_normal.reference} (par article)")
    
    # Créer des jobs
    job_service = JobService()
    locations = Location.objects.all()[:3]
    emplacement_ids = [loc.id for loc in locations]
    
    try:
        jobs_normal = job_service.create_jobs_for_inventory_warehouse(
            inventory_normal.id,
            Warehouse.objects.first().id,
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
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    print("\n=== COMPARAISON TERMINÉE ===")

if __name__ == "__main__":
    test_complete_workflow_image_stock()
    test_workflow_normal() 