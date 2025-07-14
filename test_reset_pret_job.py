#!/usr/bin/env python
"""
Script de test pour vérifier la réinitialisation d'un job PRET
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment
from apps.inventory.usecases.job_reset_assignments import JobResetAssignmentsUseCase
from django.utils import timezone

def test_reset_pret_job():
    """Test la réinitialisation d'un job PRET"""
    
    print("=== TEST RESET JOB PRET ===\n")
    
    # 1. Vérifier les jobs existants et leurs statuts
    jobs = Job.objects.all()
    print(f"1. Jobs existants ({jobs.count()}):")
    for job in jobs:
        print(f"   - {job.reference}: {job.status}")
        if job.pret_date:
            print(f"     Date prêt: {job.pret_date}")
        if job.en_attente_date:
            print(f"     Date en attente: {job.en_attente_date}")
    
    # 2. Trouver un job PRET ou en créer un pour le test
    pret_job = Job.objects.filter(status='PRET').first()
    
    if not pret_job:
        print("\n2. Aucun job PRET trouvé, création d'un job de test...")
        
        # Créer un job de test avec statut PRET
        from apps.masterdata.models import Warehouse, Account
        from apps.inventory.models import Inventory
        
        # Créer les données nécessaires
        account = Account.objects.first()
        if not account:
            account = Account.objects.create(name='Test Account', code='TEST')
        
        warehouse = Warehouse.objects.first()
        if not warehouse:
            warehouse = Warehouse.objects.create(name='Test Warehouse', code='TEST', account=account)
        
        inventory = Inventory.objects.first()
        if not inventory:
            inventory = Inventory.objects.create(label='Test Inventory', date=timezone.now(), status='EN PREPARATION')
        
        # Créer un job PRET
        pret_job = Job.objects.create(
            status='PRET',
            warehouse=warehouse,
            inventory=inventory,
            pret_date=timezone.now()
        )
        print(f"   Job PRET créé: {pret_job.reference}")
    
    print(f"\n3. Job PRET à tester: {pret_job.reference}")
    print(f"   - Statut actuel: {pret_job.status}")
    print(f"   - Date prêt: {pret_job.pret_date}")
    print(f"   - Date en attente: {pret_job.en_attente_date}")
    
    # 4. Tester le use case
    print(f"\n4. Test du use case de reset...")
    
    use_case = JobResetAssignmentsUseCase()
    
    try:
        result = use_case.execute([pret_job.id])
        print(f"   ✅ Succès: {result['message']}")
        
        # 5. Vérifier les changements
        print(f"\n5. Vérification des changements:")
        
        # Recharger le job
        pret_job.refresh_from_db()
        print(f"   - Nouveau statut: {pret_job.status}")
        print(f"   - Date prêt après reset: {pret_job.pret_date}")
        print(f"   - Date en attente après reset: {pret_job.en_attente_date}")
        
        # Vérifier que les assignments ont été reset
        assignments = Assigment.objects.filter(job=pret_job)
        print(f"   - Assignments après reset ({assignments.count()}):")
        for ass in assignments:
            print(f"     * {ass.reference}: statut {ass.status}")
            print(f"       - Date prêt: {ass.pret_date}")
            print(f"       - Date affecté: {ass.affecte_date}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 6. Test avec un job AFFECTE aussi
    affecte_job = Job.objects.filter(status='AFFECTE').first()
    if affecte_job:
        print(f"\n6. Test avec un job AFFECTE: {affecte_job.reference}")
        print(f"   - Statut actuel: {affecte_job.status}")
        print(f"   - Date affecté: {affecte_job.affecte_date}")
        
        try:
            result = use_case.execute([affecte_job.id])
            print(f"   ✅ Succès: {result['message']}")
            
            # Vérifier les changements
            affecte_job.refresh_from_db()
            print(f"   - Nouveau statut: {affecte_job.status}")
            print(f"   - Date affecté après reset: {affecte_job.affecte_date}")
            print(f"   - Date en attente après reset: {affecte_job.en_attente_date}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    test_reset_pret_job() 