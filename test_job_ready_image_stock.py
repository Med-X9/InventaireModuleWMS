#!/usr/bin/env python
"""
Script de test pour vérifier la nouvelle logique de job ready avec image de stock
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting, Inventory
from apps.inventory.usecases.job_ready import JobReadyUseCase
from apps.masterdata.models import Warehouse, Account
from apps.users.models import UserApp
from django.utils import timezone

def test_job_ready_with_image_stock():
    """Test la nouvelle logique avec image de stock"""
    
    print("=== TEST JOB READY AVEC IMAGE DE STOCK ===")
    
    # 1. Créer les données de test
    print("\n1. Création des données de test...")
    
    # Créer un compte et un warehouse
    account = Account.objects.create(
        name='Test Account',
        code='TEST001'
    )
    
    warehouse = Warehouse.objects.create(
        name='Test Warehouse',
        code='WH001',
        account=account
    )
    
    # Créer un inventaire
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
    
    # Créer un job avec statut AFFECTE
    job = Job.objects.create(
        status='AFFECTE',
        warehouse=warehouse,
        inventory=inventory
    )
    
    print(f"   - Job créé: {job.reference} (statut: {job.status})")
    
    # Créer une session mobile
    session = UserApp.objects.create(
        username='test_session',
        type='Mobile'
    )
    
    print(f"   - Session créée: {session.username}")
    
    # 2. Test 1: Configuration valide - 2ème comptage affecté
    print("\n2. Test 1: Configuration valide (2ème comptage affecté)...")
    
    # Créer une affectation pour le 2ème comptage seulement
    assignment2 = Assigment.objects.create(
        job=job,
        counting=counting2,
        session=session,
        status='AFFECTE',
        affecte_date=timezone.now()
    )
    
    print(f"   - Affectation créée: {assignment2.reference} pour le comptage 2")
    
    # Tester le use case
    use_case = JobReadyUseCase()
    
    try:
        result = use_case.execute([job.id])
        print(f"   ✅ SUCCÈS: {result['message']}")
        print(f"   - Jobs mis en PRET: {result['ready_jobs_count']}")
        print(f"   - Assignments mis en PRET: {len(result['updated_assignments'])}")
        
        # Vérifier les changements
        job.refresh_from_db()
        assignment2.refresh_from_db()
        
        print(f"   - Nouveau statut du job: {job.status}")
        print(f"   - Nouveau statut de l'assignment: {assignment2.status}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # 3. Test 2: Configuration invalide - 2ème comptage aussi image de stock
    print("\n3. Test 2: Configuration invalide (2ème comptage image de stock)...")
    
    # Créer un nouveau job pour ce test
    job2 = Job.objects.create(
        status='AFFECTE',
        warehouse=warehouse,
        inventory=inventory
    )
    
    # Créer un 2ème comptage image de stock
    counting2_invalid = Counting.objects.create(
        order=2,
        count_mode='image de stock',
        inventory=inventory
    )
    
    # Créer une affectation pour le 2ème comptage image de stock
    assignment2_invalid = Assigment.objects.create(
        job=job2,
        counting=counting2_invalid,
        session=session,
        status='AFFECTE',
        affecte_date=timezone.now()
    )
    
    print(f"   - Job 2 créé: {job2.reference}")
    print(f"   - Comptage 2 invalide: {counting2_invalid.reference} (image de stock)")
    print(f"   - Affectation créée: {assignment2_invalid.reference}")
    
    try:
        result = use_case.execute([job2.id])
        print(f"   ✅ SUCCÈS INATTENDU: {result['message']}")
    except Exception as e:
        print(f"   ❌ ERREUR ATTENDUE: {e}")
    
    # 4. Test 3: Configuration invalide - aucun comptage affecté
    print("\n4. Test 3: Configuration invalide (aucun comptage affecté)...")
    
    # Créer un nouveau job sans affectation
    job3 = Job.objects.create(
        status='AFFECTE',
        warehouse=warehouse,
        inventory=inventory
    )
    
    print(f"   - Job 3 créé: {job3.reference} (sans affectation)")
    
    try:
        result = use_case.execute([job3.id])
        print(f"   ✅ SUCCÈS INATTENDU: {result['message']}")
    except Exception as e:
        print(f"   ❌ ERREUR ATTENDUE: {e}")
    
    # 5. Test 4: Configuration normale - les deux comptages affectés
    print("\n5. Test 4: Configuration normale (les deux comptages affectés)...")
    
    # Créer un nouvel inventaire avec comptages normaux
    inventory_normal = Inventory.objects.create(
        label='Test Inventory Normal',
        date=timezone.now(),
        status='EN PREPARATION'
    )
    
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
    
    job_normal = Job.objects.create(
        status='AFFECTE',
        warehouse=warehouse,
        inventory=inventory_normal
    )
    
    # Créer les affectations pour les deux comptages
    assignment1_normal = Assigment.objects.create(
        job=job_normal,
        counting=counting1_normal,
        session=session,
        status='AFFECTE',
        affecte_date=timezone.now()
    )
    
    assignment2_normal = Assigment.objects.create(
        job=job_normal,
        counting=counting2_normal,
        session=session,
        status='AFFECTE',
        affecte_date=timezone.now()
    )
    
    print(f"   - Inventaire normal créé: {inventory_normal.reference}")
    print(f"   - Job normal créé: {job_normal.reference}")
    print(f"   - Affectations créées: {assignment1_normal.reference}, {assignment2_normal.reference}")
    
    try:
        result = use_case.execute([job_normal.id])
        print(f"   ✅ SUCCÈS: {result['message']}")
        print(f"   - Jobs mis en PRET: {result['ready_jobs_count']}")
        print(f"   - Assignments mis en PRET: {len(result['updated_assignments'])}")
        
        # Vérifier les changements
        job_normal.refresh_from_db()
        assignment1_normal.refresh_from_db()
        assignment2_normal.refresh_from_db()
        
        print(f"   - Nouveau statut du job: {job_normal.status}")
        print(f"   - Nouveau statut des assignments: {assignment1_normal.status}, {assignment2_normal.status}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    print("\n=== FIN DES TESTS ===")

if __name__ == "__main__":
    test_job_ready_with_image_stock() 